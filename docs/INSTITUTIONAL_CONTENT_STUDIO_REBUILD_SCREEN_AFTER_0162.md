# Institutional Content Studio Rebuild Screen (After 0162)

Task label: TASK_CONTENTOPS_0162_INSTITUTIONAL_CONTENT_STUDIO_REBUILD_SCREEN_V0
Repo: A:\Capital Chronicle\tools\cc-live-contentops
Branch: master
Baseline HEAD before this task: 1b0f34a — "feat: build institutional command center screen"

This task rebuilds the Content Studio (Daily Content Studio) screen inside the
static institutional shell prototype (`ui/institutional_shell/`) into an
institutional-grade editorial control surface. It remains static, local-only,
fixture-driven, with no backend, no dependency, no network, no env reads, no
provider/LLM calls, no news fetch, and no live controls.

## 1. Owner Decision

The Content Studio is an editorial QA cockpit, not a social post generator. The
operator should immediately see allowed/blocked content lanes, why future
artifact-backed content is blocked, why grounded news is a hook not a signal,
source/evidence requirements, claim-risk classification, guardrail results,
limitations/refusal mode, dry-run platform fit, decision-ledger and draft-inspector
handoffs, blocked actions, and the next allowed action.

## 2. What Changed (within ui/institutional_shell only)

- `fixture_data.js`: added `content_studio_detail` with hero band, 10 safety
  banners, 3 content lanes, lane rules, grounded-news rule panel, 8
  source/evidence requirements, draft review-only panel, 6 claim-risk classes,
  12 guardrail categories, limitations/refusal mode, 5-platform dry-run fit
  preview, platform fit constraints, editorial quality state, decision-ledger
  handoff, draft-inspector handoff, 12-row blocked action matrix, evidence
  summary, next allowed action.
- `app.js`: added a dedicated `renderContentStudio` path bound to the
  `daily_content_studio` screen, rendering all zones with disabled, read-only
  guardrail/blocked-action chips.
- `styles.css`: added minimal Content Studio lane card styling.
- `README.md`: documented the Content Studio.


## 3. Content Studio Zones

1. Hero status band: title, content mode, public state, generation state,
   current gate, next allowed action.
2. Safety ribbon: LOCAL_ONLY, REVIEW_ONLY, MANUAL_REVIEW_REQUIRED,
   NOT_PUBLIC_POSTABLE, LIVE_DISABLED, SECRET_REDACTED, NO_FINANCIAL_ADVICE,
   NO_SIGNAL_LANGUAGE, MISSING_DATA_VISIBLE, FORECAST_NOT_READY.
3. Content lane control: pre_alpha_process (allowed review-only),
   grounded_news_context (allowed with constraints), future_artifact_backed
   (blocked). Lane mixing blocked; fake fixture artifacts blocked; invented
   source artifact IDs blocked; CC alpha implied before approval blocked.
4. Grounded news rule: news is hook not signal; source metadata supplied
   externally; repo does not search/fetch news; no market direction / model
   predicts / actionable trade framing.
5. Source/evidence requirements: source URL/date, summary, claim-risk notes,
   freshness label, limitation label, future artifact ID, missing source blocks
   publish-readiness.
6. Draft intake (review-only): external/manual draft only; repo does not call
   provider/LLM APIs; review-only; final public copy generation disabled; manual
   Jim review required.
7. Claim-risk classifier: first-party philosophy, evergreen education, cited
   factual, current factual requiring citation, market-sensitive (blocked or
   transformed to evergreen education), forbidden claim (blocked).
8. Guardrail results (forbidden): buy/sell/hold, long/short, position sizing,
   entries/exits, target prices, guaranteed prediction, signal-service framing,
   execution/broker/order routing, fake alpha, unsupported numeric market claims,
   raw vendor data redistribution, hidden missing/degraded/proxy data.
9. Limitations / refusal mode: missing stays missing, degraded stays degraded,
   proxy-only labeled, forecast readiness can stay blocked, no-forecast is a
   valid output, uncertainty must be visible.
10. Platform fit preview (dry-run, read-only): Substack, LinkedIn, X, Threads,
    Telegram (future pilot only after gates). No export/schedule/publish/live API.
11. Editorial quality state: review/evidence completeness, limitation
    visibility, guardrail cleanliness, manual review pending; never implies
    publish-ready.
12. Decision ledger handoff: operator decision required, no auto-approval,
    revocation supported, evidence refs required, public-ready approval disabled.
13. Draft Inspector handoff: source/lineage and guardrails must remain visible.
14. Blocked action matrix (disabled, read-only): generate final public copy,
    auto-approve, publish, schedule, provider/LLM API, news search/fetch,
    platform API, scrape metrics, artifact-backed without real artifacts, create
    market signal, credential display, one-button publish-all.
15. Evidence summary: linked workbench/grounded-news/external-draft-review/
    decision-ledger/platform-fit; evidence packet required.
16. Next allowed action: AWAIT OPERATOR/CHATGPT AUDIT_OF_0162_EVIDENCE_BEFORE
    ANY_NEXT_TASK; future task 0163 only after audit.

## 4. Safety Posture (Enforced)

- Static/local-only, fixture/mock-data-only.
- No backend, no dependency, no `fetch`/XHR/WebSocket/EventSource, no remote URL.
- No provider/LLM API, no news search/fetch, no live posting/scheduling/scraping.
- All forbidden/blocked actions render only as disabled, read-only text.
- No final public-ready copy generation; no fake artifact-backed alpha content.
- No secrets, env paths, request URLs, raw platform responses, raw vendor data.
- No financial advice, no signal/trading language, no buy/sell/long/short as
  enabled content, no bullish/bearish (red/green = market-direction) semantics.

## 5. Validation Surface

- Schema: `schemas/institutional_content_studio_screen_packet.schema.json`.
- Validator + summary: `live_contentops/institutional_content_studio_screen.py`.
- CLI summary: `python -m live_contentops.cli pre-alpha-institutional-content-studio-screen-summary`.
- Tests: `tests/test_institutional_content_studio_screen.py` (static-asset
  inspection, no browser).

## 6. Relationship To Telegram Live-Gate Sequencing

This screen does NOT supersede Telegram live-gate sequencing. Telegram appears
only as a future dry-run platform-fit entry; nothing calls getMe or sendMessage
and no credentials are shown.
