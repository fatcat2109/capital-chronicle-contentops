# ContentOps V5 Manual Distribution Evidence Registry Browser QA

## Canonical target

- Canonical UI target: `ui/contentops_v5/`
- Local QA URL: `http://127.0.0.1:5173/`
- No V4 or standalone dashboard was targeted.

## Registry platforms visible

- Substack
- LinkedIn
- X

## Safety invariants confirmed

- `api_used=false` for every registry platform.
- `url_network_verified=false` for every registry platform.
- `metrics_network_verified=false` for every registry platform.
- `controls_enabled=false` for every registry platform.
- Controls remain blocked, including approve, send, publish, dispatch, and schedule.
- No platform API was used.
- No network/public URL verification, fetch, or scrape was performed.
- No env values or credentials were read.
- No browser-session, cookie, localStorage, or sessionStorage data was inspected.
- No live post, reply, DM, like, repost, quote-post, schedule, approve, send, publish, or dispatch occurred.

## Screenshots

- `manual_export_registry_summary.png` - Manual Export registry summary.
- `approval_queue_registry_summary.png` - Approval Queue registry summary.
- `evidence_vault_registry_summary.png` - Evidence Vault registry summary.
