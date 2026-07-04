# Institutional Content Calendar + Workflow Board Screen (After 0165)

Task label: TASK_CONTENTOPS_0165_INSTITUTIONAL_CONTENT_CALENDAR_AND_WORKFLOW_BOARD_SCREEN_V0
Repo: A:\Capital Chronicle\tools\cc-live-contentops
Branch: master
Baseline HEAD before this task: e483bc8 — "feat: build institutional evidence vault audit timeline"

This task builds the Content Calendar + Workflow Board screen inside the static
institutional shell prototype (`ui/institutional_shell/`) into an institutional
operations board. It remains static, local-only, fixture-driven, manual-workflow-only,
with no backend, no dependency, no network, no env reads, no platform/provider API,
no scheduler, no auto-publish, no live controls, and no evidence-mutation controls.

## 1. Owner Decision

The Content Calendar + Workflow Board is an institutional operations board, not a
social media scheduler. An operator should immediately see which ideas exist, which
items need sources, which drafts are review-only, which are blocked and why, which
are operator-approved for manual posting only, which were manually posted out-of-band,
which have manually entered metrics, what evidence/limitations support each item, why
no scheduled/live/auto-publish state exists, and what the next allowed task is.

## 2. What Changed (within ui/institutional_shell only)

- `fixture_data.js`: added `content_calendar_workflow_detail` with hero band, 12
  safety banners, 7 allowed workflow states, 8 forbidden states, 8 content items
  across allowed states, 3-lane model, evidence/source panel, approval/manual-publish
  panel, freshness/limitations panel, 10 blocked reasons, static calendar planning
  grid, workflow board columns, manual metrics placeholder, decision ledger handoff,
  evidence vault handoff, visual export handoff, 11 disabled controls, evidence
  summary, next allowed action.
- `app.js`: added `renderContentCalendar` bound to the `content_calendar` screen with
  a read-only workflow board, planning grid, and policy panels (no active controls).
- `styles.css`: added `.wf-board` workflow board styles.
- `README.md`: documented the Content Calendar + Workflow Board.

## 3. Allowed Workflow States (manual-only)

idea, source_needed, draft_review, blocked, operator_approved_for_manual,
manually_posted, metrics_entered.

## 4. Forbidden States (never active lifecycle states)

scheduled, auto_publish_ready, live_published_by_system, public_ready,
publish_queued, platform_dispatched, api_posted, bot_posted. These appear only in a
forbidden-state registry, never as active item states or workflow columns.

## 5. Screen Zones

1. Hero status band: title, workflow mode, public state, live/scheduler/automation
   state (all disabled), current gate, next allowed action.
2. Safety ribbon: LOCAL_ONLY, REVIEW_ONLY, MANUAL_REVIEW_REQUIRED,
   NOT_PUBLIC_POSTABLE, LIVE_DISABLED, SCHEDULER_DISABLED, KILL_SWITCH_ACTIVE,
   SECRET_REDACTED, NO_FINANCIAL_ADVICE, NO_SIGNAL_LANGUAGE, MISSING_DATA_VISIBLE,
   MANUAL_PUBLISH_TRACKING_ONLY.
3. Workflow board: 7 allowed-state columns with item cards (id, title, type, lane,
   claim risk, blocked reasons, next operator action).
4. Lane model: pre_alpha_process (review-only), grounded_news_context (source/citation
   required), future_artifact_backed (blocked).
5. Content items: 8 items covering data_sufficiency, forecast_readiness,
   failure_forensics, build_in_public, macro_education, product_update, market_note.
   Two market_note items carry educational/general-only, freshness label, limitations,
   no-signal and no-buy/sell/hold constraints.
6. Evidence & source panel: source/evidence required, artifact IDs required for future
   artifact-backed content, no invented artifact IDs, missing source blocks readiness,
   proxy/degraded visible.
7. Approval & manual publish panel: operator approval required, not automatic, approval
   does not imply platform posting, manual publish out-of-band, manual post URL recorded
   later (not fetched), metrics entered later manually, no API sync.
8. Freshness & limitations panel: stale items require review, freshness label required
   for current claims, missing/degraded/proxy labels visible, forecast-not-ready is a
   valid state.
9. Blocked reasons (10): missing_source, missing_artifact_id, future_artifact_not_available,
   claim_risk_too_high, market_note_missing_freshness, limitation_not_visible,
   manual_review_missing, public_ready_disabled, scheduler_disabled, live_posting_disabled.
10. Calendar planning grid: static week slots labeled planned review slot / manual
    publish window candidate / source refresh checkpoint / metrics entry reminder. No
    scheduled-post/auto-publish/dispatch/queue semantics.
11. Metrics placeholder: manual entry only; no scraping, no platform API metrics, no
    automatic sync.
12. Decision ledger handoff: evidence-backed, read-only history, no auto-approval.
13. Evidence Vault handoff: every item needs evidence refs; no evidence mutation from
    this screen.
14. Visual Export handoff: next screen is 0166; screenshots must be redacted; no
    export-to-platform.
15. Disabled controls (11): schedule, auto_publish, publish_now, queue, platform_sync,
    scrape_metrics, fetch_post_url, generate_final_copy, approve_all, upload_evidence,
    refresh_project_sources — all read-only, none active.
16. Evidence summary + next allowed action panel.

## 6. Safety Posture (Enforced)

- Static/local-only, fixture/mock-data-only, manual-workflow-only.
- No backend, no dependency, no `fetch`/XHR/WebSocket/EventSource, no remote URL.
- No platform/provider API, no env/credential read, no scheduler, no auto-publish, no
  live posting, no scraping, no evidence mutation.
- No secrets, env paths, request URLs, raw platform responses, raw vendor data.
- No financial advice, no signal/trading language, no red/green market-direction semantics.

## 7. Validation Surface

- Schema: `schemas/institutional_content_calendar_workflow_board_screen_packet.schema.json`.
- Validator + summary: `live_contentops/institutional_content_calendar_workflow_board_screen.py`.
- CLI summary: `python -m live_contentops.cli pre-alpha-institutional-content-calendar-workflow-board-screen-summary`.
- Tests: `tests/test_institutional_content_calendar_workflow_board_screen.py` (static
  asset inspection, no browser).

## 8. Relationship To Telegram Live-Gate Sequencing

This screen does NOT supersede Telegram live-gate sequencing. No scheduling or live
posting is enabled. The Telegram live step still requires a separate explicit
operator/ChatGPT GO.

