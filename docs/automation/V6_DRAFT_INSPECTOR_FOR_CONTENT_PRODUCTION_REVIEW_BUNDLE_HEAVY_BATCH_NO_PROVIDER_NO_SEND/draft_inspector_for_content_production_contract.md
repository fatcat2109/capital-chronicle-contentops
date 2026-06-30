# V6 Draft Inspector for Content Production Contract

## Input Requirements

Input must be a V6 content production review bundle with all six packet sections present, future draft inspection eligibility true, hard false flags false, human review required true, and blockers empty.

## Report Status Rules

- Inspector mode is `deterministic_local_review_only`.
- Empty citations keep `citation_status` at `source_review_required`.
- Missing evidence remains `review_required`.
- Source freshness remains `source_review_required` unless later sourced research exists.
- Advice, alert-service, market prediction, model authority, and trade execution statuses must pass.
- Discord safety requires discussion question and disclosure with no publication or dispatch.
- SEO safety requires limitations and caveats preserved.
- Variant execution passes only when platform readiness and dispatch-ready values are false.

## Allowed Future Targets

- `payload_hash_preview_only`
- `approval_ledger_preparation_only`

## Blocked Targets

- live_send
- dispatch
- publication
- public_url_creation
- metrics_creation
- provider_call
- browser_session
- env_read
- credential_value_read

## Hard False State

`eligible_for_live_send_now`, provider_call_made, env_read, credential_value_read, network_call_made, browser_session_used, public_url_created, metrics_created, publication_ready, dispatch_allowed, and runtime_truth are always false.
