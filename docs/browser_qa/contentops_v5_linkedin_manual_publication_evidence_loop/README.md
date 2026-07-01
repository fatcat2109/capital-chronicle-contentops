# ContentOps V5 LinkedIn Manual Publication Evidence Loop Browser QA

Target: canonical V5 dashboard at `http://127.0.0.1:5173/`.

## Scope

Checked only repo-local V5 dashboard surfaces:

- Manual Export & Pilot Verification
- Approval & Dispatch
- Evidence Vault

## Safety boundary

- No LinkedIn URL was opened.
- No LinkedIn API was called.
- No browser storage/session/cookie/localStorage/sessionStorage inspection was performed.
- No credentials or env values were read.
- No publish, dispatch, schedule, send, approve, DM, comment, like, or reaction action was performed.

## Result

PASS. LinkedIn fixture/manual-only evidence is visible in canonical V5.

## Evidence

- `manual_export_qa.png`
- `approval_queue_qa.png`
- `evidence_vault_qa_full.png`
- `linkedin_v5_qa.webp`

## Observed labels

- `LinkedIn manual post draft`
- `LinkedIn manual publication evidence pending review`
- `LinkedIn manual publication evidence vault`

## Observed safety states

- `linkedin_api_used=false`
- `url_network_verified=false`
- `metrics_network_verified=false`
- `enabled_publish_send_dispatch_approve_controls=false`
- blocked controls include approve, send, publish, dispatch, schedule
