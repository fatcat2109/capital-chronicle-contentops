# ContentOps V5 Manual Distribution Registry Operator Audit View Refinement QA

## Canonical target

- Canonical UI target: `ui/contentops_v5/`
- Local QA URL: `http://127.0.0.1:5173/`
- No V4 or standalone dashboard was targeted.

## Reusable panel visibility

The reusable `ManualDistributionRegistryPanel` is visible in:

- Manual Export / Pilot Verification
- Approval Queue
- Evidence Vault

## Registry evidence visible

- Platforms visible: Substack, LinkedIn, X
- Registry hash visible
- Metrics and URL hash summaries visible
- `api_used=false`
- `url_network_verified=false`
- `metrics_network_verified=false`
- `controls_enabled=false`
- Controls remain blocked/enabled=false

## Safety invariants

No platform API, network/public URL verification, env read, credential read,
browser-session read, cookie/localStorage/sessionStorage inspection, or live action occurred.
No post, reply, DM, like, repost, quote-post, schedule, approve, send, publish, or dispatch occurred.

## Screenshots

- `manual_export_registry_refined_view.png`
- `approval_queue_registry_refined_view.png`
- `evidence_vault_registry_refined_view.png`
