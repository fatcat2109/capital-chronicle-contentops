# Capital Chronicle ContentOps — Project Source Export (After 0153)

## Authority Hierarchy
1. This export and the AFTER_0153 bundle docs are the consolidated authority for future
   ChatGPT sessions.
2. Repo evidence (committed code, schemas, fixtures, tests) is the ground truth.
3. Operator/ChatGPT task prompts define scope per task.
4. Do not rely on prior IDE/chat history. Repo evidence is authority.

## Repo Path and Accepted Baseline
- Repo path: A:\Capital Chronicle\tools\cc-live-contentops
- Branch: master
- Accepted HEAD: a644f82 — "feat: add telegram credential setup guide"
- Accepted through: 0153.

## Hard Boundaries
No financial advice; no buy/sell/hold; no position sizing; no personalized trade
recommendations; no guaranteed prediction; no signal-service framing; no
trading/execution/broker/order-routing framing; no social auto-posting; no autonomous
replies/DMs; no scraping; no platform credentials in repo; no secrets
printed/logged/committed; no raw vendor data redistribution; no unverified numeric
market claims; no hiding missing/degraded/proxy data; no live posting/scheduling/API
calls. No backend/server. No provider/LLM API calls from repo.

## Accepted Task Summaries 0138–0153
- 0138 Social Platform Foundation / Control Plane — platform-fit matrix + safety states.
- 0139 LLM-Assisted Content Writer Workbench — template-only prompt packs, no repo LLM calls.
- 0140 Grounded News Angle Workbench — operator-supplied source metadata; news is a hook, not a signal.
- 0141 Daily Content Studio Run Packet — composes 0138/0139/0140 into a daily run surface.
- 0142 Daily Content Studio Markdown Review Export — human-readable review packet renderer.
- 0143 Operator Decision Ledger — records manual review decisions; not a publish approval system.
- 0144 External Draft Review Packet — review of externally pasted drafts; repo does not generate.
- 0145 UI Data Contract — view-model contract; not a frontend implementation.
- 0146 Static Daily Content Studio UI — fixture-only static frontend; no backend.
- 0147 Static UI Review Workflow — local navigation/filter/inspector; no live controls.
- 0148 Publish Automation Readiness + Platform Capability Registry — dry-run only; one-button publish-all disabled.
- 0149 Dry-Run Publish Batch Manifest — kill-switch/redacted-audit/idempotency/partial-failure modeled.
- 0150 Credential and Secret Policy for Publish Adapters — future-only env slots; never commit secrets.
- 0151 Redacted Publish Audit Log + Secret Evidence Guard — no-secret evidence; fail-closed on secret-like values.
- 0152 Telegram One-Platform Live Pilot Readiness Gate — decision ready_to_prepare_future_credential_setup_task.
- 0153 Telegram Credential Setup Operator Guide + Env Slot Stub — placeholder-only; reads no credentials.

## Operational Caveats
- 0152 process caveat: module/test use non-colliding names
  (live_contentops/telegram_one_platform_live_pilot_gate.py,
  tests/test_telegram_one_platform_live_pilot_gate.py) because
  live_contentops/telegram_live_pilot_gate.py and tests/test_telegram_live_pilot_gate.py
  already existed from accepted 0083. The 0152 schema name and CLI command match spec.
- 0153 caveat: an operator local env path was referenced out-of-band
  (OPERATOR_LOCAL_ENV_FILE_PROVIDED_OUT_OF_BAND) but was not read, parsed, printed, or
  committed.
- Fake detector-test token/chat-id values inside negative-test functions and a
  pre-existing 0083/0084 placeholder default chat-id value are not real secrets.

## Current CLI Commands Available
pre-alpha-social-platform-foundation-summary;
pre-alpha-llm-content-writer-workbench-summary;
pre-alpha-grounded-news-angle-workbench-summary;
pre-alpha-daily-content-studio-run-summary;
pre-alpha-daily-content-studio-markdown-export(-summary);
pre-alpha-daily-content-studio-decision-ledger-summary;
pre-alpha-daily-content-studio-external-draft-review-summary;
pre-alpha-daily-content-studio-ui-data-contract-summary;
pre-alpha-daily-content-studio-static-frontend-summary;
pre-alpha-publish-automation-readiness-summary;
pre-alpha-dry-run-publish-batch-manifest-summary;
pre-alpha-publish-adapter-credential-secret-policy-summary;
pre-alpha-redacted-publish-audit-log-summary;
pre-alpha-telegram-live-pilot-gate-summary;
pre-alpha-telegram-credential-setup-guide-summary;
status; operator-command-summary.

## Current Safety Gates
All validators fail closed. Live posting, platform API, provider/LLM API, credential
reads, scheduler, scraping, newsletter/CMS, OAuth, one-button publish-all, and
public-ready final copy are all disabled and validated to be disabled. Kill-switch halt
is active. Manual review and not-public-postable are enforced everywhere.

## Next Task Recommendation
TASK_CONTENTOPS_0155_TELEGRAM_REDACTED_CREDENTIAL_PRESENCE_CHECK_LOCAL_ONLY_V0

## Future Credential Presence-Check Boundary (Exact Wording)
A future credential presence-check may read only an approved local env source and
return boolean/redacted evidence only. It must not print credential values, must not
validate against Telegram, must not call any Telegram API, must not post, and remains
blocked until explicit operator/ChatGPT GO.
