# Business Brain dashboard handoff

Saved September 15, 2026, at Quentin’s request.

## Owner decision and next step

Quentin stopped the proposed GitHub Actions migration. He wants an AI agent to handle the income dashboard after Business Brain is connected to that agent. Save this context and move to a new chat for the next Business Brain project. Do not resume the GitHub migration or choose the next project without his direction.

The existing `daily-income-dashboard` Codex schedule remains ACTIVE at 08:00 America/Chicago; it was not changed by this handoff. It still uses Codex usage. The September 15 wakeup was redirected into migration research and then stopped; no new collection or publication completed today. Agent integration has not been implemented.

## Existing deliverables

- Private dashboard: https://quentin-revenue.realquentinflores.chatgpt.site/
- Private source and aggregate recovery repository: https://github.com/xcerebroai/business-revenue-dashboard
- Workspace: `/Users/quentinflores/Documents/Codex/2026-09-14/business-revenue-dashboard`
- Canonical Business Brain vault: `/Users/quentinflores/Downloads/Xcerebro:Jarvis/Just Jarvis/ Xcerebro`
- Read the vault’s `AGENTS.md` and `START HERE - Project Memory.md` first. The five-link Business Brain Home stays unchanged.
- Dashboard runbook: `outputs/Daily income refresh - runbook.md`; definitions and coverage: `outputs/Revenue dashboard - operating note.md`.

GitHub source was last verified pushed at `0b3f7149c20af4537cda9968ed6b38d8077f929b`. The existing Site project is `appgprj_6aa864f591748191ac5f8604c71901f2`; preserve its ID, URL and owner-only access. Its live version 2 was built from `c67b7d07e253c83256402201849981507af5818a`. Later recovery documentation was GitHub-only.

## Verified financial state

The September 14 snapshot has $335,653.01 incoming and $295,751.30 after known deductions and repayments. Incoming totals: Stripe $167,168.84, PayPal $52,099.00, Skool $101,678.26, BILL $9,525.00, Gusto $5,181.91. Stripe includes $34,800 financing; $25,903.11 repayments reduce the after-deductions amount. These are incoming cash activity, not profit or a bank balance.

Quentin wants all incoming money combined, without business/sales classification. Just Jarvis LLC receives Stripe, PayPal and the two paid Skool communities’ payouts. PayPal displays VS STAFFING LLC; Gusto’s recipient profile is Honestly Nevermind LLC. Preserve observed labels without inferring legal changes. Skool’s separate merchant/Express payout flow is not included in the owner’s Standard Stripe charges.

Stripe and PayPal API collection succeeded through September 14, 22:26:59 UTC, with complete pagination. Skool’s three communities, BILL Payments In and both Gusto contractor payer profiles were collected through browser reports. Preserve source-specific dates, provider indexing, financing, refunds and exclusions. Never replace an unavailable source with zero or treat bank transfers as new income.

## Deferred work, not implemented

No GitHub Actions workflow, cloud reporting secrets, new ingestion endpoint or hosting changes were created. Two tentative environment-variable adapter changes were saved locally in `work/deferred-github-actions.patch`; the working collectors were restored to their committed versions. The patch is only a draft and is excluded from Git.

Research found an API path for BILL, but the supplied key alone is insufficient: production organization/login or sync-token access must be verified. Gusto contractor login does not grant a general personal API; partner/admin authorization or a separately validated email/export source would be needed. No documented complete Skool payout API was found. Saved browser reports remain the current method. Recheck provider documentation when integration resumes.

The future agent should first read this handoff and the runbook, connect only the authorized reporting access, test one complete collection/validation/private-publication cycle, then deliberately transfer scheduling ownership to avoid duplicate runs. Keep secrets in protected storage, never in ordinary notes, Git, logs or published JSON. This handoff authorizes no money movement, external sends, billing/settings changes or broader sharing.
