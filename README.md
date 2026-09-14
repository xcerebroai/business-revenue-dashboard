# Private revenue dashboard

Owner-only Sites dashboard for Quentin Flores. Static UI with reviewed aggregate evidence; no provider credentials, customer records or provider calls in the frontend.

See `outputs/Revenue dashboard - operating note.md` for metric definitions, source cutoffs, exclusions, manual refresh, reconciliation limits and recovery.

Validated source: `dist/`. Local finance collection and build scripts: `work/finance/` (ignored; preserved in the local recovery artifact). Build the snapshot with `python3 work/finance/build_snapshot.py`; verify with `node work/finance/verify.mjs` and `node --check dist/app.js`. New currencies and new Stripe categories require review before publication. Only privately publish through the configured Sites project; never change its audience as part of a refresh.
