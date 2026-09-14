# Daily income dashboard refresh

Private dashboard: https://quentin-revenue.realquentinflores.chatgpt.site

Run daily at **8:00 AM America/Chicago** in the existing task on this Mac. This is a local Codex refresh and private publication, not a continuously connected bank feed. The Mac must be available and Chrome reporting sessions signed in. Refresh failures keep the last successful source amounts and display a stale warning. The open dashboard checks for a newly published snapshot every five minutes and when the tab becomes visible.

Workspace: `/Users/quentinflores/Documents/Codex/2026-09-14/business-revenue-dashboard`.

## Authorized work and data boundary

Quentin requested daily collection of all incoming money from Stripe, PayPal, Skool, BILL and Gusto, including Stripe financing. Read reports, use existing saved reporting credentials, validate aggregate data, and publish privately to the same owner-only Site. Do not move money, create invoices, modify billing/payout accounts, change permissions, generate credentials, send messages, or change sharing. The user-supplied BILL developer key is not enough to authenticate its API and is not stored in this project; use the signed-in report. Gusto uses the contractor browser reports.

Provider credentials must stay in Keychain or the existing private credential note. Never put secret values, raw customer records, provider IDs, bank identifiers, or free-text transaction notes into this project, logs, prompts, Git, archives or Site data. API collectors keep raw records and duplicate keys in memory and save aggregates only. The private Sites source credential is short lived and must remain in memory and per-command authentication only.

## Refresh procedure

1. Read the current browser and Sites skills from the installed catalog. Preserve the dashboard’s design and existing audience. Work in this checkout only. Snapshot `dist/data.json` into an ignored `work/` prior-run file for the change comparison.
2. Run `python3 scripts/refresh_api.py`. It refreshes both Stripe and PayPal with a common current UTC cutoff and complete YTD pagination. Saved Stripe access uses the Keychain adapter at `/Users/quentinflores/Code/xcerebro-site-revamp/.local/brain-finance/secure_stripe_report.py`; PayPal access uses the authorized private note. If sandbox access blocks authorized reporting, request the runtime escalation, never print secrets. Each source independently replaces its local evidence only after full validation. Inspect the sanitized success/failure result and provider indexing timestamps. Partial API failures do not prevent other sources from updating.
3. Read current-year browser reports from the existing Chrome session with the approved browser tool. Discover a relevant connector first unless browser use is explicitly in force. If no reporting connector is available, use browser UI; never fetch undocumented internal APIs, cookies, storage or app state. Reuse the persistent browser binding when present. Dates and tables must be grounded in fresh visible page/DOM evidence.
4. **BILL:** Open the signed-in `app01.us.bill.com` account and select **Payments In**, never Payments Out. Clear the default “Last 30 days, next 30 days” filter. In the current UI, all 81 historical records load at once and the footer says “All records loaded”; future runs must recheck pagination/record counts. Read actual table cells for delivery date, payment type, status, currency and amount. Include Paid ePayments and genuine recorded cash receipts. Exclude Void/canceled/failed/unpaid amounts. Scheduled/pending amounts are not received. Offline payment types such as PayPal or card may duplicate another provider; inspect them before adding. The existing $2,000 Cash receipt is recorded as delivered July 27, 2026; its detail explicitly says Cash, and no matching $2,000 Stripe/PayPal receipt appeared July 20–August 3. It is included as a BILL-recorded cash receipt, not independent bank verification. Do not silently change its recorded date to the invoice’s older due date.
5. **Gusto:** In the account menu, **Switch company** lists two contractor profiles for Honestly Nevermind LLC: DealMachine Operations, Inc. and DealMachine Holdings LLC. Select each profile’s Sign in, then **Pay**. Read **Contractor payments** sorted by payday descending. Include Complete Direct deposit totals only. Use header names because Operations shows Wage and Total while Holdings may show only Total. Do not add both wage and total. Read all current-year rows, following pagination until older-year rows or disabled Next. On the initial run, Operations had seven March–September payments and Holdings two January–February payments; these counts will change. Inspect the company list for new payer profiles each run. Use observed links, not invented profile IDs. Do not click Make primary, add company or change account settings.
6. **Skool:** Read all three communities: `https://www.skool.com/aicheatcodes`, `https://www.skool.com/aw-academy-2604`, and `https://www.skool.com/wholesaling-houses-101-3860`. In each community’s owner Settings, open Payouts and the payout history. Read every current-year payout page until the next page reaches the prior year or Next is disabled. The original counts were 23, 36 and 1, respectively. Observe fresh DOM/AX controls before clicking. USD was confirmed in an actual payout invoice for each community; new currencies require review. Include net payout amounts once. Never estimate from members, price, account balance or pending payout amounts. Skool’s official FAQ states member processing occurs on Skool’s merchant and payouts use a separate Stripe Express account; the collected owner Stripe account is Standard. This supports treating these payouts as separate from the owner Stripe charges. Recheck if the account/processing arrangement changes.
7. For each browser source, write a complete sanitized JSON report under `work/finance/` with the schema below, then run `python3 scripts/import_browser.py PATH`. Replace that source’s entire current-year snapshot instead of appending. Deduplicate repeated page reads using actual row/invoice links in memory, but do not collapse legitimate distinct payments just because amounts/dates match. Do not store those links or IDs in delivered data. Keep each community/payer name only as a group label. If any required page/profile is unavailable, do not import partial data: run `python3 scripts/record_failure.py SOURCE` and keep its last-good report. Never mark an old source refreshed without reading it.
8. Run `python3 scripts/build_dashboard.py`, then `node scripts/verify.mjs`, `node --check dist/app.js`, and Python syntax validation. Verify source totals, included financing, exclusions, current month, date filters, and the stale flags. The aggregate headline deliberately combines gross Stripe/PayPal payments with net Skool payouts and reported BILL/Gusto receipts; fee deductions apply only where reported. Do not label it profit, accounting revenue or bank balance. Do not impose sales/brand/entity classification gates. New currencies or unknown provider events require inspection; never guess values.
9. Publish through the current Sites hosting skill. Read `.openai/hosting.json` and reuse its exact project ID. Preserve owner-only access. Commit validated source, obtain a short-lived source write credential, push using `scripts/push_private.py` with the credential through hidden stdin, and keep tokens out of files/arguments/logs. After a successful push, read the full current HEAD SHA. Package only the static output using the installed Sites helper. On macOS, strip AppleDouble `._*` entries from the archive if present. Save/deploy the exact pushed source to the private Site and wait for terminal success. Do not change access, create another Site, or publish customer/credential files. Update the existing Site view; no extra browser QA unless requested. Failed publishing must be reported as a failure; do not claim the live dashboard updated.
10. Compare successful source cash-in totals and recent dates against the prior snapshot. Stay quiet for an unchanged, healthy report. Notify Quentin of meaningful new incoming money, a source correction, a refresh/publish failure, or required sign-in. Include current source coverage, not misleading zeros. Do not repeatedly notify about an unchanged known issue. Refresh the local recovery ZIP after meaningful source/implementation changes, excluding secrets and raw records. Keep the compact business memory and canonical operating note aligned when behavior changes.

## Browser import schema

```json
{
  "source": "gusto",
  "checked_at": "CURRENT_TIME_WITH_TIMEZONE",
  "period_start": "CURRENT_YEAR-01-01T00:00:00-06:00",
  "period_end_exclusive": "CURRENT_TIME_WITH_TIMEZONE",
  "retrieval_complete": true,
  "coverage_note": "Which profiles/pages and terminal pagination were checked",
  "groups": ["Observed payer or community name"],
  "rows": [{
    "date": "YYYY-MM-DD",
    "currency": "USD",
    "kind": "income",
    "category": "completed_direct_deposit",
    "group": "Observed payer or community name",
    "count": 1,
    "amount_minor": 12345,
    "fee_minor": 0,
    "net_minor": 12345
  }]
}
```

`amount_minor - fee_minor = net_minor`; use integer cents. Browser report zero fee fields mean no additional reported fee to deduct, not proof that the provider charged no fee. Allowed kinds: income, financing, deduction, repayment, excluded, review. Category examples: net_payout, paid_epayment, recorded_cash, void_epayment, completed_direct_deposit. A failed source must retain its original successful `checked_at`. The builder uses only allowlisted aggregate fields for the frontend.

## Recovery and references

`work/finance/sources/` holds last-good aggregate evidence. `work/finance/refresh-status.json` holds last attempts; `work/finance/schedule.json` holds the active schedule metadata. `dist/data.json` and `outputs/revenue-snapshot.json` are the published/portable aggregate view. Repeated imports replace a complete source and cannot grow totals by appending duplicates. The dashboard itself does not contain API secrets or directly contact financial providers.

[Skool’s merchant and separate Express payouts](https://help.skool.com/article/86-subscriptions-faq) · [Stripe reporting categories](https://docs.stripe.com/reports/reporting-categories) · [PayPal reporting](https://developer.paypal.com/api/transaction-search/v1/search-get) · [BILL receivable payments](https://developer.bill.com/reference/listreceivablepayments) · [Gusto contractor payments](https://support.gusto.com/article/110191889100000/getting-paid-through-gusto-and-viewing-payments-for-us-contractors)
