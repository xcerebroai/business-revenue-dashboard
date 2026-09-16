# Quentin Flores — private income dashboard

[Open the private dashboard](https://quentin-revenue.realquentinflores.chatgpt.site)

Updated September 16, 2026. **Daily refresh is active at 8:00 AM Central.** Today's scheduled run refreshed Stripe and PayPal through 13:02:42 UTC. Skool, BILL and Gusto retain their September 14 amounts and original check dates, marked stale. BILL and Gusto require Chrome sign-in. Complete Skool collection is blocked pending explicit authorization for Wholesaling Houses 101; partial results were not imported.

| Source | Money coming in, 2026 YTD | After known deductions and repayments |
| --- | ---: | ---: |
| Stripe, including financing | $168,919.27 | $130,970.37 |
| PayPal, all successful incoming payments | $52,099.00 | $49,729.49 |
| Skool, three communities | $101,678.26 | $101,678.26 |
| BILL, Paid receipts | $9,525.00 | $9,525.00 |
| Gusto, both payer profiles | $5,181.91 | $5,181.91 |
| **Combined** | **$337,403.44** | **$297,085.03** |

All amounts USD. The combined incoming amount includes **$34,800 in Stripe financing advances**. Stripe repayments of **$26,253.18** reduce the after-deductions amount. Financing is incoming cash, not sales revenue; no remaining loan balance is inferred. This is an incoming-activity dashboard, not profit, tax reporting, accounting revenue, or a bank-balance reconciliation.

## What changed

Quentin requested all incoming money without brand or sales classification. The previous PayPal checkout-only gate is removed: successful general-payment credits ($1,875.36) and mass-payment credits ($1,214.96) are included alongside checkout receipts ($49,008.68). Attached fees total $1,654.51; a linked $700 chargeback and $15 fee are deducted once.

Skool’s **60 observed net payouts** are included: AI For Business Mastermind $52,625.74, Real Estate Cheat Codes $48,782.82 and Wholesaling Houses 101 $269.70. Each community’s invoice explicitly states USD. [Skool’s official FAQ](https://help.skool.com/article/86-subscriptions-faq) says member payments process on Skool’s merchant account and its payouts use a separate Stripe Express account; the collected owner Stripe account is Standard. Together with the Skool payout invoices, this supports including Skool payouts separately from owner Stripe charges. Gross Skool member receipts and fees are not estimated or deducted again.

BILL has **nine Paid ePayments totaling $7,525** and **one recorded Cash receipt of $2,000**, for $9,525. All 81 historical rows loaded with date filters cleared; 11 are in 2026, including a $709.25 Void ePayment that is excluded. The cash detail records delivery July 27, 2026 even though its invoice due date is older; the dashboard follows the delivery date. No matching $2,000 Stripe/PayPal receipt appeared July 20–August 3. Inclusion relies on BILL’s recorded cash status; bank receipt and all possible cross-provider relationships are not independently verified. Unpaid invoices and scheduled payments do not count.

Gusto has **nine Complete Direct deposit payments**: seven March–September payments from DealMachine Operations, Inc. and two January–February payments from DealMachine Holdings LLC. Both profiles are under **Honestly Nevermind LLC**. Totals, not wage-plus-total, are counted. History was read through the prior year.

Quentin confirmed **Just Jarvis LLC** receives Stripe, PayPal and the two paid Skool communities’ payouts. PayPal’s observed account label remains **VS STAFFING LLC**. These are source labels, not a verified legal rename or consolidated-entity statement. Wholesaling Houses 101’s legal entity is still unconfirmed. These distinctions do not block the requested incoming-money view.

## Collection, limits and daily behavior

Stripe and PayPal used the common whole-second cutoff **2026-09-16 13:02:42 UTC**. Stripe has 8,579 balance entries over 86 pages. PayPal has 150 balance-affecting records over nine complete query windows; its indexed-through timestamp is preserved on the dashboard and may lag the request. Browser sources show their actual check times. Months use America/Chicago; the current month is partial.

Transfers to a bank, bank funding, holds, reserves and voids do not create additional income. Unknown provider codes/statuses remain outside the total for review. Refunds, disputes, reversals, known fees and financing repayments preserve source signs. Missing fee breakdowns on browser payout reports are not invented. The page checks for newly published data every five minutes and when reopened.

The active Codex heartbeat is `daily-income-dashboard`, attached to this existing task, daily at **08:00 America/Chicago**. It collects read-only data, preserves last-good amounts on failure, marks stale sources, validates, then republishes to the same owner-private Site. A failed source can stay visible while healthy sources update. No credentials are in the dashboard. BILL’s developer key alone is insufficient for API login; browser reporting is used. Gusto uses contractor-browser reporting. Provider sessions may require renewed sign-in. This is scheduled local reporting, not a cloud bank feed.

The exact procedure is in **Daily income refresh - runbook.md** beside this note. `scripts/refresh_api.py`, `scripts/import_browser.py`, `scripts/build_dashboard.py`, and `scripts/verify.mjs` implement collection, safe imports, aggregation and checks. Failed attempts are saved separately from last-good source evidence. New currencies require unit review before inclusion.

## Verification and recovery

Validated all five source totals, all 45 current month-range combinations, financing/repayment arithmetic, no-double-counting of balance transfers, source count preservation, stale-state behavior and syntax. Both API collectors completed a live refresh through the daily orchestrator. Browser history covered all required current-year pages/profiles. The September 16 scheduled collection refreshed both API sources; all three browser sources retained their previous complete reports. Publication must be confirmed separately from collection.

The workspace is `/Users/quentinflores/Documents/Codex/2026-09-14/business-revenue-dashboard`. `outputs/revenue-snapshot.json` contains the portable aggregate view; `outputs/dashboard-recovery.zip` preserves the dashboard, scripts, runbook and last-good aggregate evidence. Recovery excludes provider credentials, raw customer records and transaction IDs. Saved Stripe Keychain access and the private PayPal credential note remain local dependencies; the ZIP does not back up those secrets.

## GitHub storage

The dashboard source, refresh scripts, reports and sanitized recovery snapshots are saved in the private repository [xcerebroai/business-revenue-dashboard](https://github.com/xcerebroai/business-revenue-dashboard). The existing daily automation also exports and pushes validated updates there. The live dashboard remains on its owner-private Sites URL. Credentials and browser sessions stay local; no GitHub Pages or Actions refresh is configured. A fresh clone can restore aggregate evidence with `python3 scripts/recovery.py restore` and verify it with `node scripts/verify.mjs`.

## Owner decision — September 15, 2026

Quentin stopped the proposed GitHub Actions migration and wants an AI agent to handle reporting after Business Brain is connected to it. No Actions workflow, cloud secrets or new dashboard endpoint were deployed. The existing daily Codex schedule is unchanged and still uses Codex usage. Draft adapter edits were saved as an ignored local patch and removed from the working collectors. [[Resume - Income Dashboard Agent Integration]] records the exact state and next actions. The next chat is for the next owner-selected Business Brain project, not automatic continuation of the migration.

## September 16 collection result

Stripe incoming increased $1,750.43; PayPal was unchanged. The combined after-deductions amount increased $1,333.73. AI For Business Mastermind and Real Estate Cheat Codes showed new payouts of $1,756.07 and $1,800.47, respectively; these partial Skool findings are not in the published totals because the required third-community check was blocked by automatic approval review. The requested approval and BILL/Gusto sign-ins remain pending. No account settings, access audience or schedules changed.
