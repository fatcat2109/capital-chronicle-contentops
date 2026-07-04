# Institutional Publish Readiness Tower Screen (After 0163)

Task label: TASK_CONTENTOPS_0163_INSTITUTIONAL_PUBLISH_READINESS_TOWER_SCREEN_V0
Repo: A:\Capital Chronicle\tools\cc-live-contentops
Branch: master
Baseline HEAD before this task: 85f7627 — "feat: rebuild institutional content studio screen"

This task rebuilds the Publish Readiness Tower screen inside the static
institutional shell prototype (`ui/institutional_shell/`) into an
institutional-grade readiness/gating surface. It remains static, local-only,
fixture-driven, with no backend, no dependency, no network, no env reads, no
platform/provider API, and no live controls. It makes future supervised
publishing readiness inspectable WITHOUT enabling publishing.

## 1. Owner Decision

The Publish Readiness Tower is a control tower for future supervised publishing,
not a social scheduler. An operator should immediately see which platforms are
modeled, that all are dry-run only, why live posting / platform APIs / scheduler
are disabled, why manual approval and the kill switch still block publishing, and
why credentials remain redacted/local-only.

## 2. What Changed (within ui/institutional_shell only)

- `fixture_data.js`: added `publish_readiness_tower_detail` with hero band, 12
  safety banners, 8-platform capability registry (all dry-run/live-disabled/
  scheduling-disabled/not-public-postable), dry-run batch manifest, manual
  approval gate, kill switch gate, credential/secret state, redacted audit gate,
  official docs gate, Telegram pilot tower (11 read-only sub-gates), 11-row
  publish-disabled control surface, idempotency/partial-failure panel, future
  live handoff panel, evidence summary, next allowed action.
- `app.js`: added a dedicated `renderPublishReadinessTower` path bound to the
  `publish_readiness_tower` screen, rendering all zones with disabled, read-only
  control chips.
- `styles.css`: reuses existing institutional card/chip/hero styling.
- `README.md`: documented the Publish Readiness Tower.


## 3. Tower Zones

1. Hero status band: title, publish mode, public state, live state, platform API
   state, scheduler state, current gate, next allowed action.
2. Safety ribbon: LOCAL_ONLY, DRY_RUN_ONLY, REVIEW_ONLY, MANUAL_REVIEW_REQUIRED,
   NOT_PUBLIC_POSTABLE, LIVE_DISABLED, API_VALIDATED_NO_POST,
   CHANNEL_PERMISSION_UNVALIDATED, KILL_SWITCH_ACTIVE, SECRET_REDACTED,
   NO_FINANCIAL_ADVICE, NO_SIGNAL_LANGUAGE.
3. Platform capability registry (8): Telegram, X, LinkedIn, Threads, Substack,
   Facebook Page, Instagram, TikTok. Each: intended use, dry-run render,
   credential state, docs verification, manual review required, not
   public-postable, live API disabled, scheduling disabled, next blocker.
4. Dry-run batch manifest: dry-run only, fixture/mock payload only, no real
   dispatch, source lineage required, limitation visibility required, idempotency
   modeled, partial failure modeled, redacted audit required, manual approval
   gate required.
5. Manual approval gate: approval required before any live publish, review-only/
   dry-run now, public-ready approval disabled, operator decision required,
   revocation supported, no auto-approval.
6. Kill switch gate: active, blocks publishing, no publish while active, must be
   audited in future live tasks.
7. Credential & secret state: local-only/out-of-band, values never displayed,
   token/chat ID redacted, env path not shown, secret redaction required, no
   credential read in this task, validation does not imply posting permission.
8. Redacted audit gate: audit events modeled; no unredacted secrets, raw request
   URLs, raw platform responses, or raw env paths; future responses must be
   redacted; evidence packet must be secret-safe.
9. Official docs gate: per-platform docs verification required, Telegram docs gate
   implemented, other platforms require future verification, docs verification is
   not runtime authority and does not enable live posting.
10. Telegram pilot tower (11 read-only sub-gates): credential presence redacted,
    official docs implemented, getMe token validation gate (live run separate/
    later), channel write permission unvalidated, dry-run payload preview modeled,
    manual approval required, kill switch active, sendMessage disabled, live
    adapter disabled, posting disabled, scheduler disabled. Next live step
    requires a separate explicit operator/ChatGPT GO.
11. Publish-disabled control surface (11, all disabled/read-only): publish,
    schedule, connect API, OAuth, sendMessage, getMe live call, upload media,
    publish all, auto-post, scrape metrics, reply/DM.
12. Idempotency / partial failure: idempotency required before live, duplicate
    prevention required, partial failure policy required, rollback/manual fallback
    required, no current live retry loop.
13. Future live handoff: live adapter absent/disabled, one-platform live requires
    explicit GO, no autonomous posting, no autonomous replies/DMs, platform-by-
    platform rollout only.
14. Evidence summary: linked publish automation readiness, platform capability
    registry, dry-run manifest, credential policy, redacted audit log, Telegram
    gate; validation/test/scan evidence required.
15. Next allowed action: AWAIT OPERATOR/CHATGPT AUDIT_OF_0163_EVIDENCE_BEFORE
    ANY_NEXT_TASK; future task 0164 Evidence Vault only after audit.

## 4. Safety Posture (Enforced)

- Static/local-only, fixture/mock-data-only.
- No backend, no dependency, no `fetch`/XHR/WebSocket/EventSource, no remote URL.
- No platform/provider API, no live posting/scheduling/scraping, no live adapter.
- All publish/connect/API/schedule/OAuth/send controls render disabled, read-only.
- No one-button publish-all; no real publish controls.
- No secrets, env paths, request URLs, raw platform responses, raw vendor data.
- No financial advice, no signal/trading language, no buy/sell/long/short as
  enabled content, no bullish/bearish (red/green = market-direction) semantics.

## 5. Validation Surface

- Schema: `schemas/institutional_publish_readiness_tower_screen_packet.schema.json`.
- Validator + summary: `live_contentops/institutional_publish_readiness_tower_screen.py`.
- CLI summary: `python -m live_contentops.cli pre-alpha-institutional-publish-readiness-tower-screen-summary`.
- Tests: `tests/test_institutional_publish_readiness_tower_screen.py` (static-asset
  inspection, no browser).

## 6. Relationship To Telegram Live-Gate Sequencing

This screen does NOT supersede Telegram live-gate sequencing. The Telegram pilot
tower is a read-only, redacted display of sub-gates; nothing calls getMe or
sendMessage, no credentials are shown, and the next Telegram live step still
requires a separate explicit operator/ChatGPT GO.
