# CC Artifact Packet Operator Decision V1

Current policy task: `TASK_CONTENTOPS_PUBLIC_PERMISSIVE_SUPERVISED_MODE_V0`

The default operator-decision path remains block-first: without explicit
`--operator-public-override`, the current packet stays blocked for public
candidacy because it is `dqr_status=BLOCKED`, `candidate_only=true`, and
`publish_eligibility=internal_draft_only`.

With `--operator-public-override --public-mode candidate_commentary`, ContentOps
may prepare a local public candidate-commentary preview from the same packet.
The old DQR/candidate/internal-only/source-quality blockers become visible
warnings only when these safeguards pass:

- mandatory public disclaimer is present
- candidate/proxy and non-authoritative labels remain visible
- DQR/source caveats remain visible
- approval hash continuity passes
- deterministic local duplicate guard passes
- no exact-authority promotion is made
- no financial advice or trading signal is present

Current override result: `PUBLIC_CANDIDATE_ALLOWED_WITH_CAVEATS`.

Dispatch status remains locked for this task:

- `dispatch_allowed_now=false`
- `public_dispatch_performed=false`
- `platform_api_call_performed=false`
- `browser_cdp_performed=false`
- `network_or_source_fetch_performed=false`
- `env_credential_session_read_performed=false`
- `main_repo_write_performed=false`
- `scheduler_retry_outbox_execution_performed=false`

Generated preview evidence:

- `docs/automation/PUBLIC_PERMISSIVE_SUPERVISED_MODE_V0/public_override_decision_v0.json`
- `docs/automation/PUBLIC_PERMISSIVE_SUPERVISED_MODE_V0/candidate_public_preview_v0.md`
- `docs/automation/PUBLIC_PERMISSIVE_SUPERVISED_MODE_V0/candidate_platform_payloads_v0.json`
- `docs/automation/PUBLIC_PERMISSIVE_SUPERVISED_MODE_V0/caveat_disclaimer_block_v0.md`
- `docs/automation/PUBLIC_PERMISSIVE_SUPERVISED_MODE_V0/public_permissive_evidence_v0.json`

Next task: controlled live dispatch under operator public override.
