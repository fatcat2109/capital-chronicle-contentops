# ContentOps V5 X Manual Publication Evidence Loop Browser QA

## Canonical target

- Canonical UI target: `ui/contentops_v5/`
- No V4 or standalone dashboard was targeted.
- Local QA URL: `http://127.0.0.1:5173/`

## Screenshot files

- `manual_export_qa.png` - Manual Export shows the X manual publication evidence loop.
- `approval_queue_qa.png` - Approval Queue shows X manual publication evidence pending review.
- `evidence_vault_qa.png` - Evidence Vault shows the actual `X manual publication evidence vault` panel.
- `x_manual_qa_recording.webp` - Local V5 browser QA recording artifact.

## Required visual confirmations

- Manual Export includes `X manual publication evidence loop`.
- Approval Queue includes `X manual publication evidence pending review`.
- Evidence Vault includes `X manual publication evidence vault`.
- Evidence Vault shows at least one X packet ID/hash.
- Evidence Vault safety line shows:
  - `x_api_used=false`
  - `url_network_verified=false`
  - `metrics_network_verified=false`
  - `controls_enabled=false`

## Safety invariants confirmed

- No X URL was opened, fetched, scraped, or network-verified.
- No X API was used.
- No browser session data was read.
- No cookies were inspected.
- No `localStorage` was inspected.
- No `sessionStorage` was inspected.
- No tokens were inspected.
- No env values were read.
- No credentials were read.
- No live post was performed.
- No dispatch was performed.
- No schedule action was performed.
- No send action was performed.
- No approve action was performed.
- No reply was performed.
- No DM was performed.
- No like was performed.
- No repost was performed.
- No quote-post was performed.

## Scope note

This QA evidence is for a local fixture/operator-supplied X manual publication evidence loop only. It does not imply public URL verification, provider readiness, platform authentication, live publishing, or any platform-side action.
