"""Read-only, owner-authorized PayPal cash-in report; aggregates only.

Only OAuth authentication POST and Transaction Search GET are permitted.
No raw records, identifiers, credentials, tokens, or provider error bodies persist.
The output file is replaced atomically only after complete retrieval/validation.
"""
from __future__ import annotations
import argparse
import base64
from collections import Counter, defaultdict
import datetime as dt
from decimal import Decimal, InvalidOperation
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

PRIVATE_NOTE = Path('/Users/quentinflores/Downloads/Xcerebro:Jarvis/Just Jarvis/ Xcerebro/05 Operations/Credentials - Private.md')
API = 'https://api-m.paypal.com'
ZONE = ZoneInfo('America/Chicago')
UTC = dt.timezone.utc
DOCS = [
    'https://developer.paypal.com/api/transaction-search/v1/search-get',
    'https://developer.paypal.com/api/transaction-search/v1/definitions/transaction_detail_list/',
    'https://developer.paypal.com/reports/reference/t-codes/',
]
KINDS = ('income', 'financing', 'deduction', 'repayment', 'excluded', 'review')

class SafeFailure(Exception):
    def __init__(self, kind, status=None):
        self.kind, self.status = kind, status
        super().__init__(kind)

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None

OPENER = urllib.request.build_opener(NoRedirect)

def request(path, token=None, credentials=None, params=None):
    if path not in ('/v1/oauth2/token', '/v1/reporting/transactions'):
        raise SafeFailure('endpoint_not_allowlisted')
    headers = {'Accept': 'application/json', 'User-Agent': 'QuentinPrivateCashIn/2.0'}
    data, method = None, 'GET'
    if path == '/v1/oauth2/token':
        if credentials is None:
            raise SafeFailure('missing_oauth_credentials')
        headers['Authorization'] = 'Basic ' + base64.b64encode((':'.join(credentials)).encode()).decode()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        data, method = b'grant_type=client_credentials', 'POST'
    else:
        if not token:
            raise SafeFailure('missing_access_token')
        headers['Authorization'] = 'Bearer ' + token
    url = API + path + ('?' + urllib.parse.urlencode(params) if params else '')
    try:
        with OPENER.open(urllib.request.Request(url, data=data, headers=headers, method=method), timeout=40) as response:
            obj = json.load(response)
            if not isinstance(obj, dict):
                raise SafeFailure('invalid_response_shape')
            return obj
    except urllib.error.HTTPError as exc:
        status = exc.code
        exc.close()
        raise SafeFailure('http_error', status) from None
    except SafeFailure:
        raise
    except Exception:
        raise SafeFailure('network_or_response_error') from None

def credentials():
    content = PRIVATE_NOTE.read_text()
    values = []
    for name in ('PAYPAL_CLIENT_ID', 'PAYPAL_CLIENT_SECRET'):
        match = re.search(re.escape('`' + name + '`') + r'\s+```text\n([^\n]+)\n```', content)
        if not match:
            raise SafeFailure('credential_format_not_found')
        values.append(match.group(1).strip())
    del content
    return tuple(values)

def parse_date(value):
    try:
        result = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
        if result.tzinfo is None or result.utcoffset() is None:
            raise ValueError
        return result.astimezone(UTC)
    except Exception:
        raise SafeFailure('invalid_timezone_aware_datetime') from None

def iso(value):
    return value.astimezone(UTC).isoformat().replace('+00:00', 'Z')

def cents(value):
    try:
        number = Decimal(str(value)) * 100
        if not number.is_finite() or number != number.to_integral_value():
            raise ValueError
        return int(number)
    except (ValueError, InvalidOperation):
        raise SafeFailure('non_cent_currency_amount_requires_review') from None

def classification(code, status, amount):
    # Unknown/new statuses never silently become money received. R is preserved.
    if status != 'S':
        return 'review', 'provider_status_' + status
    if code.startswith('T00'):
        return ('income', 'successful_incoming_payment') if amount > 0 else ('excluded', 'outgoing_or_zero_payment')
    if code in {'T2004', 'T9701'}:
        return ('financing', 'financing_received') if amount > 0 else ('repayment', 'financing_repaid') if amount < 0 else ('review', 'zero_financing_event')
    if code == 'T9702' or code.startswith(('T16', 'T18')):
        return ('repayment', 'credit_repayment') if amount < 0 else ('review', 'credit_funding_or_reversal_requires_review')
    if code in {'T1107', 'T1120', 'T1106', 'T1114', 'T1115', 'T1118', 'T1201', 'T1202', 'T1205', 'T1207', 'T1208'}:
        return 'deduction', 'refund_dispute_or_reversal'
    if code.startswith('T01') or code in {'T1108', 'T1109'}:
        return 'deduction', 'separate_fee_or_fee_reversal'
    if code in {'T1105', 'T1110', 'T1111'} or code.startswith(('T13', 'T15', 'T21', 'T98')):
        return 'excluded', 'hold_reserve_authorization_or_display'
    if code.startswith('T02'):
        return 'excluded', 'internal_currency_conversion'
    if code.startswith(('T03', 'T04', 'T06', 'T07', 'T17', 'T20')) or code in {'T1101', 'T1104', 'T1112'}:
        return 'excluded', 'funding_transfer_or_withdrawal'
    if code.startswith('T05') or code in {'T1000', 'T1102', 'T1119'}:
        return 'excluded', 'purchase_or_purchase_reversal'
    if code == 'T2301':
        return 'excluded', 'tax_withholding'
    return 'review', 'unmapped_event_code'

def windows(start, end):
    cursor = start.astimezone(ZONE)
    while cursor < end:
        month_end = cursor.replace(year=cursor.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0) if cursor.month == 12 else cursor.replace(month=cursor.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        stop = min(month_end, end)
        if stop.astimezone(UTC) - cursor.astimezone(UTC) > dt.timedelta(days=31):
            stop = (cursor.astimezone(UTC) + dt.timedelta(days=31)).astimezone(ZONE)
        yield cursor, stop
        cursor = stop

def atomic_save(target, obj):
    target = Path(target)
    # Do not resolve target symlinks; os.replace replaces the directory entry.
    if not target.parent.is_dir():
        raise SafeFailure('output_parent_not_found')
    fd, temporary = tempfile.mkstemp(prefix='.' + target.name + '.', suffix='.tmp', dir=target.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, 'w') as stream:
            json.dump(obj, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

def collect(year, cutoff):
    now = dt.datetime.now(UTC)
    start = dt.datetime(year, 1, 1, tzinfo=ZONE).astimezone(UTC)
    year_end = dt.datetime(year + 1, 1, 1, tzinfo=ZONE).astimezone(UTC)
    end = min(cutoff, year_end).replace(microsecond=0)
    if not start < end or cutoff > now + dt.timedelta(seconds=5):
        raise SafeFailure('invalid_or_future_reporting_period')
    state = {
        'schema_version': 2, 'source': 'paypal', 'currency_basis': 'two_decimal_integer_cents_no_fx_conversion',
        'entity': 'Just Jarvis LLC', 'observed_account_name': 'VS STAFFING LLC',
        'entity_note': 'Owner confirmed PayPal payout recipient as Just Jarvis LLC; earlier observed provider account label was VS STAFFING LLC.',
        'retrieved_at_utc': iso(now), 'year': year, 'timezone': str(ZONE),
        'period_start': iso(start), 'period_end_exclusive': iso(end), 'requested_cutoff_utc': iso(cutoff),
        'retrieval_complete': False, 'data_coverage_complete': False,
        'query_windows': [], 'documents': DOCS,
    }
    auth = request('/v1/oauth2/token', credentials=credentials())
    token = auth.get('access_token')
    if not isinstance(token, str) or not token:
        raise SafeFailure('access_token_missing')
    state['reporting_scope_present'] = 'https://uri.paypal.com/services/reporting/search/read' in auth.get('scope', '').split()
    del auth
    seen, all_rows = {}, []
    timestamps = []
    duplicate_count = returned_count = outside_count = 0
    for left, right in windows(start, end):
        query = {'start_date': iso(left), 'end_date': iso(right), 'pages_read': 0, 'returned_records': 0, 'expected_records': None, 'complete': False}
        state['query_windows'].append(query)
        expected_pages, expected_count = None, None
        for page in range(1, 1001):
            response = request('/v1/reporting/transactions', token=token, params={'start_date': iso(left), 'end_date': iso(right), 'fields': 'transaction_info', 'balance_affecting_records_only': 'Y', 'page_size': 500, 'page': page})
            total_pages, total_items = int(response['total_pages']), int(response['total_items'])
            if total_pages < 0 or total_items < 0 or total_pages > 1000:
                raise SafeFailure('invalid_pagination_metadata')
            if expected_pages is None:
                expected_pages, expected_count = total_pages, total_items
                query['expected_records'] = total_items
            if (total_pages, total_items) != (expected_pages, expected_count):
                raise SafeFailure('pagination_changed_during_retrieval')
            if int(response.get('page', page)) != page:
                raise SafeFailure('unexpected_page_number')
            refreshed = response.get('last_refreshed_datetime')
            if refreshed:
                timestamps.append(parse_date(refreshed))
            rows = response.get('transaction_details', [])
            if not isinstance(rows, list):
                raise SafeFailure('invalid_transaction_list')
            query['pages_read'] += 1
            query['returned_records'] += len(rows)
            returned_count += len(rows)
            for row in rows:
                info = row['transaction_info']
                initiated = parse_date(info['transaction_initiation_date'])
                if not start <= initiated < end:
                    outside_count += 1
                    continue
                code, status = info['transaction_event_code'], info['transaction_status']
                if not isinstance(code, str) or not re.fullmatch(r'T\d{4}', code) or not isinstance(status, str) or not re.fullmatch(r'[A-Z]', status):
                    raise SafeFailure('invalid_event_or_status_shape')
                amount_obj = info['transaction_amount']
                currency = amount_obj['currency_code']
                if not isinstance(currency, str) or not re.fullmatch(r'[A-Z]{3}', currency):
                    raise SafeFailure('invalid_currency_shape')
                amount = cents(amount_obj['value'])
                fee_obj = info.get('fee_amount')
                if fee_obj and fee_obj['currency_code'] != currency:
                    raise SafeFailure('mixed_fee_currency_requires_review')
                signed_fee = cents(fee_obj['value']) if fee_obj else 0
                identity = (info['transaction_id'], code, iso(initiated), currency)
                content = (amount, signed_fee, status, info.get('transaction_updated_date'))
                if identity in seen:
                    if seen[identity] != content:
                        raise SafeFailure('same_event_changed_during_retrieval')
                    duplicate_count += 1
                    continue
                seen[identity] = content
                kind, reason = classification(code, status, amount)
                # Identifiers and linkage references only exist in these in-memory rows.
                all_rows.append({'id': info['transaction_id'], 'reference': info.get('paypal_reference_id'), 'reference_type': info.get('paypal_reference_id_type'), 'date': initiated.astimezone(ZONE).date().isoformat(), 'currency': currency, 'kind': kind, 'code': code, 'status': status, 'amount_minor': amount, 'fee_minor': -signed_fee, 'net_minor': amount + signed_fee, 'reason': reason, 'fee_present': fee_obj is not None})
            if page >= max(total_pages, 1):
                if query['returned_records'] != expected_count:
                    raise SafeFailure('pagination_record_count_mismatch')
                query['complete'] = True
                break
            if not rows:
                raise SafeFailure('empty_nonterminal_page')
        if not query['complete']:
            raise SafeFailure('pagination_safety_limit_reached')
        print(json.dumps({'month': left.astimezone(ZONE).strftime('%Y-%m'), 'pages': query['pages_read'], 'records': query['returned_records'], 'complete': True}), flush=True)
    del token
    buckets = {}
    originals = defaultdict(list)
    for row in all_rows:
        if row['kind'] == 'income':
            originals[row['id']].append(row)
        key = tuple(row[k] for k in ('date', 'currency', 'kind', 'code', 'status'))
        bucket = buckets.setdefault(key, {**dict(zip(('date', 'currency', 'kind', 'code', 'status'), key)), 'amount_minor': 0, 'fee_minor': 0, 'net_minor': 0, 'count': 0, 'fee_present_count': 0, 'reason': row['reason']})
        for field in ('amount_minor', 'fee_minor', 'net_minor'):
            bucket[field] += row[field]
        bucket['count'] += 1
        bucket['fee_present_count'] += int(row['fee_present'])
    linkage = []
    for row in all_rows:
        if row['code'] in {'T1201', 'T0114', 'T0106'} and row['status'] == 'S':
            matches = originals.get(row['reference'], []) if row['reference_type'] == 'TXN' else []
            linkage.append({'date': row['date'], 'currency': row['currency'], 'code': row['code'], 'amount_minor': row['amount_minor'], 'fee_minor': row['fee_minor'], 'matched_income_record_count': len(matches), 'matching_basis': 'exact_reference_id_to_original_id_in_memory' if matches else 'no_direct_income_link_in_current_period', 'original_income_amount_minor': sum(x['amount_minor'] for x in matches) if matches else None})
    daily = sorted(buckets.values(), key=lambda b: (b['date'], b['currency'], b['kind'], b['code'], b['status']))
    totals = {}
    for row in daily:
        currency_totals = totals.setdefault(row['currency'], {kind: {'amount_minor': 0, 'fee_minor': 0, 'net_minor': 0, 'count': 0} for kind in KINDS})
        for field in ('amount_minor', 'fee_minor', 'net_minor', 'count'):
            currency_totals[row['kind']][field] += row[field]
    for currency_totals in totals.values():
        currency_totals['cash_in_minor'] = currency_totals['income']['amount_minor'] + currency_totals['financing']['amount_minor']
        currency_totals['net_cash_activity_minor'] = sum(currency_totals[k]['net_minor'] for k in ('income', 'financing', 'deduction', 'repayment'))
    if sum(row['count'] for row in daily) != len(seen):
        raise SafeFailure('aggregate_record_count_mismatch')
    if any(row['amount_minor'] - row['fee_minor'] != row['net_minor'] for row in daily):
        raise SafeFailure('aggregate_arithmetic_mismatch')
    if any(sum(row[k] for row in daily) != sum(row[k] for row in all_rows) for k in ('amount_minor', 'fee_minor', 'net_minor')):
        raise SafeFailure('aggregate_ledger_mismatch')
    state.update({
        'retrieval_complete': True,
        'data_coverage_complete': len(timestamps) == sum(q['pages_read'] for q in state['query_windows']) and min(timestamps) >= end if timestamps else False,
        'provider_last_refreshed_min_utc': iso(min(timestamps)) if timestamps else None,
        'provider_last_refreshed_max_utc': iso(max(timestamps)) if timestamps else None,
        'transactions_count': len(seen), 'returned_record_count': returned_count,
        'boundary_duplicates_removed': duplicate_count, 'outside_period_records_excluded': outside_count,
        'daily': daily, 'totals_by_currency': totals,
        'status_counts': dict(sorted(Counter(r['status'] for r in all_rows).items())),
        'review_code_status_counts': dict(sorted(Counter(r['code'] + '|' + r['status'] for r in all_rows if r['kind'] == 'review').items())),
        'dispute_linkage_aggregates': linkage,
        'classification_note': 'All positive successful T00 payment credits count as income without business-category filtering. Successful financing receipts, related repayments, refunds/disputes and separately charged fees retain distinct accounting kinds. Funding, internal transfers, withdrawals, holds/reserves, conversion and purchases are excluded. Unsupported events/statuses, including R, remain visible as review and do not enter totals.',
        'fee_note': 'Embedded PayPal fee_amount is negated: a charged fee is positive, a refunded fee negative. Missing fee_amount contributes zero reported fee; fee_present_count preserves presence. Standalone fee events retain signed source transaction amount, avoiding double subtraction. net_minor = amount_minor - fee_minor.',
        'window_note': 'America/Chicago calendar dates with a whole-second exclusive cutoff; monthly queries overlap boundary instants and exact repeated events are deduplicated in memory. Provider indexing can trail execution by up to three hours; retrieval completeness and index coverage are separate.',
        'privacy': 'Aggregates only; no transaction/customer identifiers, free text, credentials, access tokens, or raw responses are persisted.',
    })
    state['status'] = 'complete' if state['data_coverage_complete'] else 'complete_with_provider_index_lag'
    return state

def self_test():
    assert cents('0.29') == 29 and cents('-1.05') == -105
    for bad in ('0.001', 'NaN', 'Infinity', 'not-money'):
        try:
            cents(bad)
        except SafeFailure:
            pass
        else:
            raise AssertionError('invalid amount accepted')
    assert classification('T0000', 'S', 23500)[0] == 'income'
    assert classification('T0001', 'S', 7099)[0] == 'income'
    assert classification('T0006', 'S', -100)[0] == 'excluded'
    assert classification('T0300', 'S', 100)[0] == 'excluded'
    assert classification('T0403', 'R', -100)[0] == 'review'
    assert classification('T1201', 'S', -70000)[0] == 'deduction'
    assert classification('T0114', 'S', -1500)[0] == 'deduction'
    assert classification('T9701', 'S', 100)[0] == 'financing'
    assert classification('T9702', 'S', -100)[0] == 'repayment'
    assert classification('T9999', 'S', 100)[0] == 'review'
    start, end = dt.datetime(2026, 1, 1, tzinfo=ZONE), dt.datetime(2027, 1, 1, tzinfo=ZONE)
    parts = list(windows(start, end))
    assert parts[0][0] == start and parts[-1][1] == end
    assert all(a[1] == b[0] for a, b in zip(parts, parts[1:]))
    assert all(b.astimezone(UTC) - a.astimezone(UTC) <= dt.timedelta(days=31) for a, b in parts)
    print(json.dumps({'status': 'self_test_passed', 'credentials_read': False}))

def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--year', type=int, default=dt.datetime.now(ZONE).year)
    parser.add_argument('--cutoff', help='Timezone-aware ISO instant; defaults to current UTC time.')
    parser.add_argument('--output', help='Aggregate JSON file, atomically replaced on successful complete retrieval only.')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.output:
        parser.error('--output is required')
    try:
        cutoff = parse_date(args.cutoff) if args.cutoff else dt.datetime.now(UTC)
        result = collect(args.year, cutoff)
        atomic_save(args.output, result)
        print(json.dumps({'status': result['status'], 'records': result['transactions_count'], 'data_coverage_complete': result['data_coverage_complete'], 'provider_cutoff': result['provider_last_refreshed_min_utc'], 'totals_by_currency': result['totals_by_currency']}), flush=True)
        return 0
    except Exception as exc:
        failure = {'status': 'failed', 'error_type': exc.kind if isinstance(exc, SafeFailure) else 'local_validation_or_io_failure', 'output_replaced': False}
        if isinstance(exc, SafeFailure) and exc.status is not None:
            failure['http_status'] = exc.status
        print(json.dumps(failure), file=sys.stderr, flush=True)
        return 2

if __name__ == '__main__':
    sys.exit(main())
