#!/usr/bin/env python3
"""GET-only Stripe cash-in aggregates. No credentials or event IDs are persisted.

The only runtime write is an atomic, mode-0600 successful output at --output.
The saved Keychain adapter is imported without executing its command-line code.
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from zoneinfo import ZoneInfo

sys.dont_write_bytecode = True
ADAPTER = Path('/Users/quentinflores/Code/xcerebro-site-revamp/.local/brain-finance/secure_stripe_report.py')
ZONE = ZoneInfo('America/Chicago')
UTC = dt.timezone.utc
MAX_PAGES = 10000
FIELDS = ('count', 'amount_minor', 'fee_minor', 'net_minor')
EXCLUDED = {
    'payout', 'payout_reversal', 'payout_minimum_balance_hold',
    'payout_minimum_balance_release', 'risk_reserved_funds',
    'reserve_transaction', 'reserved_funds', 'reserve_hold', 'reserve_release',
}
DEDUCTIONS = {'refund', 'refund_failure', 'dispute', 'dispute_reversal', 'fee', 'fee_refund'}


class SafeFailure(Exception):
    def __init__(self, kind, endpoint=None, status=None):
        super().__init__(kind)
        self.kind, self.endpoint, self.status = kind, endpoint, status


def iso(value):
    return value.astimezone(UTC).isoformat().replace('+00:00', 'Z')


def parse_cutoff(value):
    try:
        result = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
        if result.tzinfo is None:
            raise ValueError()
        return result.astimezone(UTC).replace(microsecond=0)
    except (AttributeError, ValueError):
        raise SafeFailure('cutoff_must_be_timezone_aware_iso_datetime') from None


def integer(value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise SafeFailure('amount_or_timestamp_not_integer')
    return value


def token(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-z][a-z0-9_]{0,79}', value):
        raise SafeFailure('unexpected_provider_enum_shape')
    return value


def classify(category, amount):
    if category == 'charge':
        return 'income' if amount >= 0 else 'review'
    if category == 'financing_payout':
        # Negative corrections stay in this bucket; only positive advances
        # contribute to incoming money, while corrections reduce retained funds.
        return 'financing'
    if category == 'financing_paydown':
        # Positive paydown reversals restore earlier withholding, not new money.
        return 'repayment'
    if category in DEDUCTIONS:
        return 'deduction'
    if category in EXCLUDED:
        return 'excluded'
    return 'review'


def bucket_add(target, key, amount, fee, net):
    bucket = target.setdefault(key, dict.fromkeys(FIELDS, 0))
    bucket['count'] += 1
    bucket['amount_minor'] += amount
    bucket['fee_minor'] += fee
    bucket['net_minor'] += net


def safe_get(adapter, key, endpoint, params=None):
    if endpoint not in {'/v1/account', '/v1/balance_transactions'}:
        raise SafeFailure('endpoint_not_allowlisted')
    result = adapter.get(key, endpoint, params)
    if not result.get('ok'):
        status = result.get('status')
        if not isinstance(status, int) or not 100 <= status <= 599:
            status = None
        # Never surface provider message, identifiers, or free-text error fields.
        raise SafeFailure('provider_request_failed', endpoint, status)
    if not isinstance(result.get('data'), dict):
        raise SafeFailure('provider_response_not_object', endpoint)
    return result['data']


def account_metadata(account):
    controller = account.get('controller') or {}
    dashboard = controller.get('stripe_dashboard') or {}
    fees = controller.get('fees') or {}
    losses = controller.get('losses') or {}
    def enum(value, allowed):
        return value if value in allowed else 'unknown' if value is not None else None
    def literal_bool(value):
        return value if isinstance(value, bool) else None
    kind = enum(account.get('type'), {'standard', 'express', 'custom', 'none'})
    dashboard_kind = enum(dashboard.get('type'), {'full', 'express', 'none'})
    currency = account.get('default_currency')
    if not isinstance(currency, str) or not re.fullmatch(r'[a-z]{3}', currency):
        currency = None
    result = {
        'type': kind,
        'default_currency': currency.upper() if currency else None,
        'controller': {
            'type': enum(controller.get('type'), {'account', 'application'}),
            'is_controller': literal_bool(controller.get('is_controller')),
            'stripe_dashboard_type': dashboard_kind,
            'requirement_collection': enum(controller.get('requirement_collection'), {'stripe', 'application'}),
            'fees_payer': enum(fees.get('payer'), {'account', 'application', 'application_custom', 'application_express'}),
            'losses_payments': enum(losses.get('payments'), {'stripe', 'application'}),
        },
        'charges_enabled': literal_bool(account.get('charges_enabled')),
        'payouts_enabled': literal_bool(account.get('payouts_enabled')),
        'standard_account_observed': kind == 'standard',
        'express_account_observed': kind == 'express' or dashboard_kind == 'express',
        'skool_overlap_resolved': False,
        'overlap_note': 'Account type/controller describes this Stripe account only. It does not establish receipt-level non-overlap with Skool payouts.',
    }
    return result


def atomic_save(path, value):
    path = Path(path)
    if not path.parent.is_dir():
        raise SafeFailure('output_parent_directory_missing')
    temporary = None
    try:
        fd, temporary = tempfile.mkstemp(prefix='.' + path.name + '.', suffix='.pending', dir=path.parent)
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass


def collect(output, cutoff, year, match=None):
    now = dt.datetime.now(UTC)
    start = dt.datetime(year, 1, 1, tzinfo=ZONE)
    next_year = dt.datetime(year + 1, 1, 1, tzinfo=ZONE)
    end = min(cutoff, next_year.astimezone(UTC))
    if end <= start or cutoff > now + dt.timedelta(seconds=2):
        raise SafeFailure('invalid_or_future_reporting_period')
    spec = importlib.util.spec_from_file_location('private_stripe_keychain_adapter', ADAPTER)
    if spec is None or spec.loader is None:
        raise SafeFailure('adapter_unavailable')
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    try:
        key = adapter.retrieve(adapter.SERVICE, adapter.ACCOUNT).decode('utf-8')
    except Exception:
        raise SafeFailure('keychain_read_failed') from None
    if not key.startswith(('rk_live_', 'sk_live_')):
        raise SafeFailure('saved_credential_not_live_stripe_key')

    account = account_metadata(safe_get(adapter, key, '/v1/account'))
    seen, monthly, daily, normalized, matches = set(), {}, {}, {}, {}
    cursor, pages = None, 0
    complete = False
    for page in range(1, MAX_PAGES + 1):
        params = {'limit': 100, 'created[gte]': int(start.timestamp()), 'created[lt]': int(end.timestamp())}
        if cursor:
            params['starting_after'] = cursor
        response = safe_get(adapter, key, '/v1/balance_transactions', params)
        if response.get('object') != 'list' or not isinstance(response.get('data'), list) or not isinstance(response.get('has_more'), bool):
            raise SafeFailure('invalid_pagination_response')
        items = response['data']
        pages = page
        for item in items:
            event_id = item.get('id')
            if not isinstance(event_id, str) or not event_id or event_id in seen:
                raise SafeFailure('missing_or_duplicate_transaction_identifier')
            seen.add(event_id)
            created = integer(item['created'])
            if not int(start.timestamp()) <= created < int(end.timestamp()):
                raise SafeFailure('transaction_outside_requested_period')
            amount, fee, net = (integer(item[field]) for field in ('amount', 'fee', 'net'))
            if amount - fee != net:
                raise SafeFailure('transaction_arithmetic_mismatch')
            currency = item.get('currency')
            if not isinstance(currency, str) or not re.fullmatch(r'[a-z]{3}', currency):
                raise SafeFailure('invalid_currency_shape')
            currency = currency.upper()
            category = token(item.get('reporting_category') or 'unknown')
            raw_type = token(item.get('type') or 'unknown')
            local_date = dt.datetime.fromtimestamp(created, ZONE).date().isoformat()
            month = local_date[:7]
            direction = 'credit' if amount > 0 else 'debit' if amount < 0 else 'zero'
            kind = classify(category, amount)
            if match and kind == 'income' and amount == match['amount_minor'] and match['start_date'] <= local_date < match['end_date_exclusive']:
                bucket_add(matches, '|'.join((local_date, currency, category, raw_type)), amount, fee, net)
            bucket_add(monthly, '|'.join((month, currency, category, raw_type, direction)), amount, fee, net)
            bucket_add(daily, '|'.join((local_date, currency, category, raw_type, direction)), amount, fee, net)
            bucket_add(normalized, (local_date, month, currency, kind, category, raw_type, direction), amount, fee, net)
        if not response['has_more']:
            complete = True
            break
        if not items:
            raise SafeFailure('empty_nonterminal_page')
        cursor = items[-1]['id']
    del key
    if not complete:
        raise SafeFailure('pagination_limit_reached')
    rows = [dict(zip(('date', 'month', 'currency', 'kind', 'category', 'type', 'direction'), k), **v) for k, v in sorted(normalized.items())]
    totals = {}
    for row in rows:
        currency = row['currency']
        b = totals.setdefault(currency, {
            'transaction_count': 0, 'ledger_amount_minor': 0, 'ledger_fee_minor': 0, 'ledger_net_minor': 0,
            'income_minor': 0, 'financing_advanced_minor': 0, 'incoming_minor': 0,
            'income_and_financing_net_minor': 0, 'deduction_net_minor': 0, 'repayment_net_minor': 0,
            'after_deductions_minor': 0, 'excluded_net_minor': 0, 'review_net_minor': 0, 'review_count': 0,
        })
        b['transaction_count'] += row['count']
        for f in ('amount', 'fee', 'net'):
            b['ledger_' + f + '_minor'] += row[f + '_minor']
        kind = row['kind']
        if kind in {'income', 'financing'}:
            target = 'income_minor' if kind == 'income' else 'financing_advanced_minor'
            b[target] += max(row['amount_minor'], 0)
            b['incoming_minor'] += max(row['amount_minor'], 0)
            b['income_and_financing_net_minor'] += row['net_minor']
        elif kind in {'deduction', 'repayment', 'excluded', 'review'}:
            b[kind + '_net_minor'] += row['net_minor']
            if kind == 'review':
                b['review_count'] += row['count']
    for b in totals.values():
        b['after_deductions_minor'] = b['income_and_financing_net_minor'] + b['deduction_net_minor'] + b['repayment_net_minor']
        if b['after_deductions_minor'] + b['excluded_net_minor'] + b['review_net_minor'] != b['ledger_net_minor']:
            raise SafeFailure('kind_to_ledger_reconciliation_mismatch')
        if b['ledger_amount_minor'] - b['ledger_fee_minor'] != b['ledger_net_minor']:
            raise SafeFailure('currency_arithmetic_mismatch')
    if sum(r['count'] for r in rows) != len(seen):
        raise SafeFailure('normalized_count_mismatch')
    for field in FIELDS:
        if sum(b[field] for b in daily.values()) != sum(b[field] for b in monthly.values()) or sum(b[field] for b in daily.values()) != sum(r[field] for r in rows):
            raise SafeFailure('daily_monthly_reconciliation_mismatch')
    result = {
        'schema_version': 2, 'source': 'stripe', 'status': 'success',
        'retrieved_at_utc': iso(dt.datetime.now(UTC)), 'started_at_utc': iso(now),
        'timezone': 'America/Chicago', 'year': year,
        'period_start': iso(start), 'period_end_exclusive': iso(end),
        'covered_through_exclusive': iso(end),
        'retrieval_complete': True, 'aggregation_complete': True,
        'transactions_count': len(seen), 'pages_read': pages,
        'classification_complete': not any(b['review_count'] for b in totals.values()),
        'account_metadata': account, 'rows': rows,
        'raw_daily_categories': daily, 'raw_monthly_categories': monthly,
        'currency_totals': totals,
        'definitions': {
            'incoming_minor': 'Positive external charge amounts plus positive financing advances; before provider fees and deductions.',
            'deduction': 'Signed refunds, disputes, their restorations, fees and fee restorations; positive adjustments do not count as new incoming money.',
            'repayment': 'Signed financing withholding and withholding reversals; positive reversals do not count as new incoming money.',
            'after_deductions_minor': 'Signed net income/financing/deduction/repayment activity; excludes transfers, reserves, unknown records. Not profit or bank deposits.',
            'amount_units': 'Integer provider minor units, isolated by currency. USD minor units are cents. No conversion or floating point amounts.',
            'raw_category_key': 'date-or-month|currency|reporting_category|type|amount_direction',
            'coverage': 'GET balance_transactions filtered by created >= local-year start and created < whole-second UTC cutoff. Provider future adjustments remain possible.',
        },
        'privacy': 'Aggregates and allowlisted account metadata only; no credentials, customer fields, account IDs, transaction IDs, source IDs or free text persisted.',
    }
    if match:
        result['requested_overlap_check'] = {
            **match,
            'date_basis': 'Balance transaction created date in America/Chicago.',
            'matching_buckets': matches,
            'matching_count': sum(b['count'] for b in matches.values()),
            'note': 'Matching amount/date is a candidate only and does not establish cross-provider identity.',
        }
    atomic_save(output, result)
    print(json.dumps({'status': 'success', 'transactions_count': len(seen), 'pages_read': pages, 'covered_through_exclusive': iso(end), 'classification_complete': result['classification_complete'], 'account_metadata': account, 'currency_totals': totals, 'requested_overlap_check': result.get('requested_overlap_check')}, sort_keys=True), flush=True)


def self_test():
    assert classify('charge', 100) == 'income'
    assert classify('financing_payout', 100) == 'financing'
    assert classify('financing_paydown', -20) == 'repayment'
    assert classify('financing_paydown', 20) == 'repayment'
    assert classify('dispute_reversal', 20) == 'deduction'
    assert classify('payout_minimum_balance_release', 100) == 'excluded'
    assert classify('transfer', 100) == 'review'
    assert classify('new_provider_category', 100) == 'review'
    for value in (1.0, True, '1'):
        try:
            integer(value)
            raise AssertionError('non-integer accepted')
        except SafeFailure:
            pass
    assert parse_cutoff('2026-09-14T19:31:21.514136Z').microsecond == 0
    example = {'type': 'standard', 'id': 'sensitive', 'controller': {'type': 'account', 'is_controller': False, 'stripe_dashboard': {'type': 'full'}}}
    meta = account_metadata(example)
    assert meta['standard_account_observed'] and 'sensitive' not in json.dumps(meta)
    print('PASS: cash-in classification, reversal handling, integer amounts, timestamp precision, metadata privacy.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output')
    parser.add_argument('--cutoff', help='Timezone-aware ISO cutoff; exclusive, floored to whole seconds.')
    parser.add_argument('--year', type=int, help='Local America/Chicago reporting year; defaults to cutoff year.')
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--match-amount-minor', type=int, help='Optional incoming-amount overlap candidate check; integer minor units.')
    parser.add_argument('--match-start', help='Inclusive local YYYY-MM-DD start for optional candidate check.')
    parser.add_argument('--match-end', help='Exclusive local YYYY-MM-DD end for optional candidate check.')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.output:
        parser.error('--output is required unless --self-test is used')
    try:
        cutoff = parse_cutoff(args.cutoff) if args.cutoff else dt.datetime.now(UTC).replace(microsecond=0)
        year = args.year if args.year is not None else cutoff.astimezone(ZONE).year
        if not 1970 <= year <= 9998:
            raise SafeFailure('invalid_year')
        match = None
        if any(x is not None for x in (args.match_amount_minor, args.match_start, args.match_end)):
            try:
                left = dt.date.fromisoformat(args.match_start)
                right = dt.date.fromisoformat(args.match_end)
                if args.match_amount_minor is None or args.match_amount_minor <= 0 or left >= right:
                    raise ValueError()
            except (ValueError, TypeError):
                raise SafeFailure('invalid_overlap_check_arguments') from None
            match = {'amount_minor': args.match_amount_minor, 'start_date': left.isoformat(), 'end_date_exclusive': right.isoformat()}
        collect(args.output, cutoff, year, match)
        return 0
    except SafeFailure as exc:
        print(json.dumps({'status': 'failed', 'error_type': exc.kind, 'endpoint': exc.endpoint, 'http_status': exc.status, 'output_written': False}), flush=True)
        return 2
    except Exception:
        # No exception strings or traceback: library failures can contain data.
        print(json.dumps({'status': 'failed', 'error_type': 'unexpected_collector_failure', 'output_written': False}), flush=True)
        return 2


if __name__ == '__main__':
    sys.exit(main())
