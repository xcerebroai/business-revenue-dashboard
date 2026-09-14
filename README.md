# Private daily income dashboard

Owner-private Sites dashboard for Quentin Flores, combining Stripe, PayPal, Skool, BILL and Gusto incoming activity with Stripe financing and repayments.

The frontend contains aggregate evidence only. Read `outputs/Daily income refresh - runbook.md` for the active 8 AM Central Codex heartbeat and signed-in browser procedure. Read `outputs/Revenue dashboard - operating note.md` for definitions, current totals, coverage, indexing lag and recovery.

API refresh: `python3 scripts/refresh_api.py`. Browser reports: validated full-source imports with `scripts/import_browser.py`. Build aggregates: `python3 scripts/build_dashboard.py`. Check: `node scripts/verify.mjs` and `node --check dist/app.js`. API secrets stay in existing local credential storage; never add them to source or static assets. Only publish through the existing owner-private Sites project in `.openai/hosting.json`.
