# Private daily income dashboard

Private source repository for Quentin Flores’s income dashboard, combining Stripe, PayPal, Skool, BILL and Gusto with Stripe financing and repayments.

- Live dashboard: [quentin-revenue.realquentinflores.chatgpt.site](https://quentin-revenue.realquentinflores.chatgpt.site)
- GitHub: [xcerebroai/business-revenue-dashboard](https://github.com/xcerebroai/business-revenue-dashboard)
- Daily update: **8 AM Central**, run by the existing Codex automation on the owner’s Mac. Each validated update is pushed here and published privately to the dashboard.

## What is saved

`dist/` contains the working dashboard and latest aggregate data. `scripts/` contains reporting, imports, validation and recovery tools. `recovery/` contains five sanitized last-good source snapshots and refresh metadata. `outputs/` contains the portable report and operating instructions. This repository contains private financial totals and must stay private.

Provider credentials, customer records, transaction IDs, browser sessions, temporary working files and ZIP archives are excluded. The existing browser sessions and local credential storage are still required for collection. GitHub does not run the browser-based daily refresh, and no GitHub Pages site or Actions job is configured.

## Restore a clone

Python 3.9+ and a recent Node.js are required. The static dashboard can be served directly from `dist/`.

```sh
python3 scripts/recovery.py restore
node scripts/verify.mjs
python3 -m http.server 8000 --directory dist
```

Recovery preserves the original reporting dates and refuses to overwrite local working data. It restores aggregates only; it does not create credentials, browser sessions or a new scheduler. Follow [the daily runbook](outputs/Daily%20income%20refresh%20-%20runbook.md) to reconnect reporting on another machine. Stripe’s saved Keychain adapter and the private PayPal note are local dependencies described there.

## Refresh and save

Use `python3 scripts/refresh_api.py` for Stripe/PayPal and `scripts/import_browser.py` for complete browser-source reports. Then build with `python3 scripts/build_dashboard.py` and validate with `node scripts/verify.mjs` and `node --check dist/app.js`. Run `python3 scripts/recovery.py export` before committing to update the reviewed recovery data. Push `main` to the `github` remote and use the existing Sites project for private deployment. Never force-push or change the repository or Site audience as part of a refresh.

See [the operating note](outputs/Revenue%20dashboard%20-%20operating%20note.md) for definitions, source coverage and reconciliation limits.
