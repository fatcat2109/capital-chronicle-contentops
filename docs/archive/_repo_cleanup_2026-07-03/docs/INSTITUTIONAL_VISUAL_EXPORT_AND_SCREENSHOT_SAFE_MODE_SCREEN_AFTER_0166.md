# Institutional Visual Export + Screenshot-Safe Mode Screen (After 0166)

Task label: TASK_CONTENTOPS_0166_INSTITUTIONAL_VISUAL_EXPORT_AND_SCREENSHOT_SAFE_MODE_SCREEN_V0
Repo: A:\Capital Chronicle\tools\cc-live-contentops
Branch: master
Baseline HEAD before this task: db13050 — "feat: build institutional content calendar workflow board"

This task builds the Visual Export + Screenshot-Safe Mode screen inside the static
institutional shell prototype (`ui/institutional_shell/`) into a compliance-grade
export-preparation room. It remains static, local-only, fixture-driven, and
export-preparation-only: no backend, no dependency, no network, no env reads, no
platform/provider API, no screenshot capture, no image/PDF/SVG export, no file
download, no upload, no posting, no browser automation, no Antigravity.

## 1. Owner Decision

The Visual Export + Screenshot-Safe Mode screen is an export-preparation surface, not
an export generator. An operator should immediately see which UI surfaces are safe to
screenshot, which fields must be redacted, which labels/watermarks must be visible,
which limitations/freshness/evidence fields must remain visible, why secrets/env
paths/raw responses must never appear, why export-to-platform is disabled, why
screenshot capture has not occurred, why Antigravity is future-only, what manual
operator checks are required, and what next task is allowed after audit.

## 2. What Changed (within ui/institutional_shell only)

- `fixture_data.js`: added `visual_export_detail` with hero band, 14 safety banners,
  screenshot-safe mode panel, 6-card export-safe gallery, 10-field redaction overlay,
  10 watermark/status labels, limitations/freshness visibility, evidence visibility,
  12-item export eligibility checklist, 15-action blocked export matrix, Antigravity
  handoff (future-only), visual quality checklist, 6 screenshot-safe preview states (1
  safe + 5 blocked), manual operator checklist, evidence summary, next allowed action.
- `app.js`: added `renderVisualExport` bound to the `visual_export_studio` screen —
  all read-only panels, no active controls.
- `styles.css`: added `.vx-gallery`, `.vx-card`, `.vx-watermark`, `.vx-label` styles.
- `README.md`: documented the Visual Export + Screenshot-Safe Mode screen.

## 3. Export-Preparation-Only Posture

This screen never captures a screenshot, never creates an image/PDF/SVG file, never
downloads a file, never uploads to a platform, and never posts. The blocked export
action matrix renders capture/export/download/upload/publish/schedule/send/Antigravity/
browser/scrape/refresh/read-env/edit-evidence only as disabled read-only chips. The
active export/capture control count is 0.

## 4. Screen Zones

1. Hero status band: title, export mode, screenshot capture state (not_captured),
   file export/upload/posting/browser-automation states (disabled), Antigravity
   (future_only), current gate, next allowed action.
2. Safety ribbon (14): LOCAL_ONLY, REVIEW_ONLY, MANUAL_REVIEW_REQUIRED,
   NOT_PUBLIC_POSTABLE, LIVE_DISABLED, EXPORT_PREP_ONLY, SCREENSHOT_NOT_CAPTURED,
   SECRET_REDACTED, NO_FINANCIAL_ADVICE, NO_SIGNAL_LANGUAGE, MISSING_DATA_VISIBLE,
   LIMITATIONS_VISIBLE, WATERMARK_REQUIRED, ANTIGRAVITY_FUTURE_ONLY.
3. Screenshot-safe mode panel: visual/prep only; no screenshot taken; no browser
   automation; no Antigravity; no image/video/PDF export; no upload/post; operator
   manual redaction verification required.
4. Export-safe card gallery (6): Command Center, Content Studio, Publish Readiness
   dry-run, Evidence Vault audit, Content Calendar manual workflow, Telegram gate
   redacted. Each card carries watermark, required labels, evidence/limitations
   visibility, redaction-required, and forbidden fields.
5. Redaction overlay (10 fields, never displayed): credentials, token/chat ID,
   env paths, raw request URLs, raw platform responses, raw vendor data, personal
   operator local paths, unapproved source artifact IDs, secret hashes/snippets/
   lengths, platform target identifiers.
6. Watermark/status labels (10): Local fixture UI, Not public-postable, Review-only,
   No financial advice, No signal language, Live/API disabled, Limitations visible,
   Missing/degraded/proxy visible, Screenshot-safe mode, Evidence refs visible.
7. Limitations/freshness visibility: limitations cannot be hidden; freshness visible
   for market/current claims; missing/degraded/proxy visible; DQR/forecast-readiness
   blocks visible; no confident forecast when data sufficiency blocks.
8. Evidence reference visibility: evidence refs visible; task evidence packet IDs
   visible; source artifact IDs only if approved/real; future artifact-backed without
   real IDs blocked; evidence vault handoff read-only; invented artifact IDs not allowed.
9. Export eligibility checklist (12): no secrets, no raw env path, no raw request URL,
   no raw platform response, no raw vendor data, no public-ready false claim, no
   signal/trade advice language, limitations visible, freshness where required,
   evidence refs visible, watermark visible, operator review required.
10. Blocked export/action matrix (15, all disabled): capture_screenshot, export_png,
    export_pdf, export_svg, download_file, upload_to_platform, publish_to_platform,
    schedule_post, send_telegram_message, run_antigravity, browser_capture,
    scrape_metrics, refresh_project_sources, read_env, edit_evidence.
11. Antigravity handoff (future-only): not run yet; future 0167 may define browser QA;
    requires explicit operator/ChatGPT GO; must be narrow and screenshot-safe; no
    live/API/env in browser; no credentials in browser state; no platform posting.
12. Visual quality checklist: high contrast, legibility, dense readable layout, status
    labels visible, blocked states obvious, redaction obvious, no color-only status,
    no green/red market-direction, no P&L/trading look, no social-scheduler glamor.
13. Screenshot-safe preview states (6): export_ready_with_redaction (only safe) plus
    blocked_missing_limitations, blocked_secret_visible, blocked_public_ready_claim,
    blocked_no_evidence_refs, blocked_unredacted_platform_response (all blocked).
14. Manual operator checklist (8) + evidence summary + next allowed action panel.

## 5. Safety Posture (Enforced)

- Static/local-only, fixture/mock-data-only, export-preparation-only.
- No backend, no dependency, no `fetch`/XHR/WebSocket/EventSource, no remote URL.
- No platform/provider API, no env/credential read, no scheduler, no live posting,
  no scraping, no evidence mutation.
- No screenshot capture, no image/PDF/SVG export, no file download, no upload, no post.
- No secrets, env paths, request URLs, raw platform responses, raw vendor data.
- No financial advice, no signal/trading language, no red/green market-direction semantics.

## 6. Validation Surface

- Schema: `schemas/institutional_visual_export_screenshot_safe_mode_screen_packet.schema.json`.
- Validator + summary: `live_contentops/institutional_visual_export_screenshot_safe_mode_screen.py`.
- CLI summary: `python -m live_contentops.cli pre-alpha-institutional-visual-export-screenshot-safe-mode-screen-summary`.
- Tests: `tests/test_institutional_visual_export_screenshot_safe_mode_screen.py` (static
  asset inspection, no browser).

## 7. Relationship To Telegram Live-Gate Sequencing

This screen does NOT supersede Telegram live-gate sequencing. No screenshot, export,
posting, or live action is enabled. Antigravity browser QA remains deferred to 0167 and
requires a separate explicit operator/ChatGPT GO.

