# Alpha Wait-State Operator Runbook - After TASK_CONTENTOPS_0073

LOCAL ONLY | ADVISORY ONLY | FIXTURE ONLY | HUMAN REVIEW REQUIRED | NOT PUBLIC POSTABLE
NO PROVIDER CALL | NO SEARCH CALL | NO PLATFORM ACTION

## Current accepted state
- Repo: A:\Capital Chronicle\tools\cc-live-contentops
- Accepted starting HEAD for 0073: c8bd94e (0072 completion)
- Wait-state status: WAITING_FOR_REAL_CAPITAL_CHRONICLE_ALPHA_ARTIFACTS
- approval_granted=false; publish_ready=false; human_review_required=true
- fixture_only=true; requires_real_alpha_artifacts_now=false

## What is built
Local-only, deterministic, fixture-only ContentOps review infrastructure:
- Grounded research / SEO / prompt / citation guardrail.
- Editorial QA / preview / selection.
- Grounded editorial packet export.
- Packet audit / review queue.
- Operator decision capture / review history.
- Packet registry / review ledger.
- Operator dashboard query / handoff.
- Project Sources bundle / export.
- Real-artifact intake contract / readiness gate.
- Artifact-to-packet bridge / synthetic route guard.
- End-to-end fixture-only real-artifact pipeline trace.

## What is not built (intentionally disabled)
Provider/LLM API calls; network/search; platform APIs; credentials/env reads;
scheduling; live posting; autonomous replies/DMs; browser automation/scraping;
public-postable synthetic content; real alpha artifact access; Capital Chronicle
core repo reads/writes.

## Why the wait state is correct
The local review stack is complete and ready to receive future approved
artifacts through local contracts. Real Capital Chronicle internal alpha
artifacts do not exist in this sidecar yet and must not be faked. The correct
posture is a safe wait-state, not more synthetic posting.

## How to use the system while waiting
- Inspect local fixture-only summaries and reports.
- Review the pipeline trace scenario matrix.
- Prepare a real alpha artifact spec offline.
- Curate the Project Sources upload bundle.
- Plan the next local-only maintenance task.

## What not to do
- Do not post fixture/demo/synthetic content publicly.
- Do not enable provider/search/platform calls.
- Do not read credentials or env files.
- Do not treat any fixture as a real approved artifact.
- Do not mutate the Capital Chronicle core repo.
- Do not grant approval/publish/platform authority.

## How to resume when real alpha artifacts exist
Before real alpha intake, all of these must be true:
- Capital Chronicle internal alpha artifact spec exists.
- Approved export location/path provided by operator.
- Source artifact IDs available.
- Lineage / freshness / limitations included.
- DQR / data sufficiency / forecast readiness states explicit.
- Missing / proxy / degraded data explicit.
- Content type mapped.
- No financial advice / execution / signal claims.
- Local-only copy or fixture approved by operator.
- No direct core repo mutation by ContentOps.

Before public content:
- Real approved artifact has passed the intake gate.
- Bridge route is not blocked.
- Packet export / audit / review queue pass.
- Operator decision record exists.
- Public-post status is still manual-only.
- No auto-posting.
- Platform-specific human review.
- Freshness / limitations / source IDs visible.
- No buy/sell/hold / position sizing / guaranteed prediction / execution language.
- Final copy reviewed by Jim.

Before any live integration:
- Separate explicit GO from operator.
- New task label specifically authorizing live/provider/platform scope.
- Credential policy and secret handling tested.
- Dry-run adapter contracts.
- Redacted audit events.
- Rate-limit / error handling.
- Kill switch.
- Rollback / manual fallback.
- No autonomous posting or replies without later explicit approval.

## Evidence checklist for first real artifact intake
- [ ] Operator-approved artifact spec attached.
- [ ] Source artifact IDs present.
- [ ] Lineage refs present.
- [ ] Freshness + limitations present.
- [ ] DQR / data sufficiency / forecast readiness explicit.
- [ ] Missing / proxy / degraded data explicit.
- [ ] No forbidden finance/execution/signal language.
- [ ] Intake gate -> READY_FOR_LOCAL_REVIEW_ONLY (not public-ready).
- [ ] Operator decision recorded.

## Project Sources upload instructions
Upload only the docs listed in UPLOAD_BUNDLE_MANIFEST_AFTER_0073.md. Remove the
stale 0072 and 0069 bundles and older source bundles first. Never upload .env,
credentials, raw logs, provider outputs, platform IDs, __pycache__, or large
fixture dumps. Do not upload the operator-owned .gitignore.

## Known caveats
- .gitignore is modified in the working tree, unstaged, and outside task commit
  scope. Do not edit, stage, clean, revert, normalize, or commit it.
- 0072 evidence prose had inconsistent path wording; committed 0072 docs use the
  underscore convention (AFTER_0072 / TASK_CONTENTOPS_0072). 0073 standardizes on
  the same underscore convention.

## Final next task recommendation
WAIT_FOR_REAL_CAPITAL_CHRONICLE_ALPHA_ARTIFACTS_OR_OPERATOR_SELECTED_LOCAL_MAINTENANCE
