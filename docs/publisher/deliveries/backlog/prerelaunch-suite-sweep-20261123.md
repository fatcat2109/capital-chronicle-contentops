# Delivery: backlog/prerelaunch-suite-sweep-20261123 (Builder J, CC-775, 23-24 Nov 2026)

Goal: the whole ContentOps suite runs on the live head with no known failure, so that a new failure
cannot hide among old ones. Nothing was posted, sent or opened; no browser, scheduled task, lane
runner or file under `A:\Capital Chronicle\Runtime` was touched.

## Full suite on the live head

- Head: 2b775517 (live since 23 Nov 20:58 GMT+7), detached copy at `C:\CapitalChronicleScratch\builder-j-livehead`.
- Command: `python -B -m pytest -q -p no:cacheprovider -rfE --basetemp=... --junitxml=... tests` (one process).
- Run: 23 Nov 14:19-16:32Z (2 h 13 min).
- **Totals: 13,464 passed, 67 failed, 1 error, 78 skipped.** That is 68 failing ids in 31 files.
  - 6 belonged to Builder I (CC-774). They pass on this branch after merging its integration 74235574.
  - The other 62 are below. They split into 3 real defects (4 ids), 4 wall-clock or test-hygiene
    defects (11 ids) and 47 stale ids.
- Two more failures were hidden behind the first failure inside `test_security_scans`, and one
  further `test_discord_card_without_bot_token` assertion appeared after its first fix. They are
  covered by the follow-up commit a95935b4.

## Real defects (code fixed, test kept or extended)

1. **An event pack's LinkedIn company copy crashed publication** (`event_pack_v1.validate_intent`, commit 84adc8d7).
   - Since CC-684 (f4367ae1), the coordinator adds a company-page copy of every new LinkedIn intent.
   - Event packs (CC-404) hold no `linkedin_company` payload, so `publish_plan` raised
     `KeyError: 'linkedin_company'` partway through a pack's derivatives.
   - The company copy is now checked against the pack's own LinkedIn copy, which is the same
     reviewed text by design. The "copy changed" check is unchanged.
   - Test: `test_event_pack_cc404::test_coordinator_publishes_once_then_readbacks_and_all_registered_derivatives`
     now expects 10 sends, including `linkedin_company`.
2. **The Daily App showed LinkedIn as the retired official API** (`daily_app_ui_read_model_v1`, commit 53b64cf2).
   - After CC-684, any LinkedIn readiness row, including a verified Neo account, was rewritten as
     AUTH_UNAVAILABLE and not write-eligible, with a HIGH incident asking for the official-member OAuth flow.
   - LinkedIn now follows the Neo rule that every browser destination uses. Old Edge or official-API
     rows count as history only (NEO_ACCOUNT_AND_EXECUTOR_NOT_VERIFIED). The incident now asks to verify
     the Neo session.
   - Tests: the two `test_daily_app_ui_read_model_v1` LinkedIn ids now also check that a Neo READY row is ready.
3. **A refused POST to the loopback control server reset the connection on Windows** (`server.py`, commit 7fc3b432).
   - A refusal (403 or 404) was sent while the request body was still unread. Closing the socket then
     reset the connection, so the caller saw an abort or a timeout instead of 403.
   - The server now reads a bounded declared body (64 KB at most) before refusing. Origin checks are unchanged.
   - Test: `test_operator_control_plane_hourly_audit_v1::test_loopback_shutdown_requires_origin_exact_payload_and_reuses_fallback`.
     The test also stops reading the operator's live headline sidecars (see "Left over").

## Wall-clock, environment and hygiene defects in tests (no code changed)

- `test_x_mention_responder_cc456` (8 ids): NOW was taken once at import, but the coordinator checks a
  draft's age against the real clock (90 minutes). In a full run these tests ran over 80 minutes after
  collection and failed with X_API_MENTION_DRAFT_STALE. NOW is now refreshed for each test. They passed alone.
- `test_audience_feedback_cc402::test_export_writes_installed_desk_contract_with_platform_lines`:
  the export uses the wall clock and keeps the last week, so the fixture (posts of 10 Nov) aged out on
  17 Nov. The test now fixes the script's clock.
- `test_plan_status_touch_cc331::test_frozen_export_dry_run_has_no_store_writes_and_repeat_keeps_exact_bytes`:
  it failed only in the full run. The store uses WAL mode, so a checkpoint, for example when a
  garbage-collected connection closes, rewrites the main file without any new write. The test now
  checkpoints before each hash, so only a committed write can change the bytes.
  **This cause is inferred, not reproduced.**
- `test_contentops_profile_continuity_lock_v1::test_exact_9222_owner_is_reused_without_launch` (the error):
  it patched `Path.exists` globally. The CC-758 isolation teardown (f93d3967, 23 Nov) then read a report
  file that did not exist. It now uses a real tmp folder.

## Stale tests (the code changed on purpose; each changed test cites its commit)

| Test file (ids) | Commit and item that changed the behaviour | Change in the test |
|---|---|---|
| native_headline_filter (1), native_manual_candidate (1), native_editorial_claude_cc300 (3), codex_desktop_newsroom_operator `test_pending_native_call...` (1) | 49dd59f4 (CC-403, decision 60): another model, effort or label is recorded, not refused | Asserts the observation is kept verbatim. The invocation identity, surface and run checks still refuse. |
| native_configured_provenance (1) | 5e66a899 (CC-425, decisions 60 and 86): the current reviewer records its own invocation | Another reviewer invocation is accepted and kept |
| native_desktop_editorial (1), daily_app_ui (2, see defect 2), linkedin_official_member_api (2), repost_after_removal_cc247 linkedin (2) | f4367ae1 (CC-684): LinkedIn member on Neo; the official API path refuses with CC684_LINKEDIN_MEMBER_API_RETIRED | Neo readiness asserted. The official transport is tested directly. LinkedIn reposts use a controlled CC-247 review in place of the native acceptance; the exact-review guard is unchanged. |
| eight_platform_substack_first_pipeline (7), x_no_website_automation (1) | 280439b3 (CC-454, decision 121): YouTube Community and the LinkedIn company page reopened; only Instagram's Neo bar remains | YouTube is required again. Retired-route tests use a controlled YouTube bar. |
| capital_chronicle_latest_report_consumer (1) | d0fa300f (CC-425): recovery reads only rows of public destinations | Asserts internal rows never reach recovery |
| capital_chronicle_report_editorial_workspace (1) | ab47600f (14 Nov): the publisher name no longer counts as a news-peg word | The controlled writer's dek names the EIA storage peg |
| native_newsroom_publication_recovery (2) and the shared `seeded` fixture | 74427ad6 and a117d523 (CC-124): a scheduled run prepares sources itself; 9d398110: an unanswered visual edit is superseded | The fixture follows the scheduled branch; max_frozen uses an answered visual edit |
| codex_desktop_newsroom_operator `test_rollout...` (1) | 41e3d138 and 73053979 (CC-326, decision 90): issued schedule prompts stay frozen | Compares every field except the frozen prompt |
| contentops_v1_lane_20261104 (1) | 41e3d138 (decision 90): public dates carry "(ET)" | Expected title |
| discord_card_without_bot_token (2) | 1cb0a3bb (CC-672) and 8488f070 (CC-338): the day circuit uses two coordinator helpers | The fake coordinator carries the real helpers |
| native_tool_return_lease (1) | 3b80d6fa (CC-338): editorial preparation runs beside another window's publication | begin and resume still wait; standing and advance run |
| no_preview_links_decision83 (4) | 7a12bea0 (CC-459): no fact-card fallback; CC-584 (decision 82): a plan post needs its chart | The fixture post carries CC-459's recorded capture, so the link guard is reached |
| notes_main_account_cc453 (4) | 457ba14c, a68a252c and f1b16fdd (16 Nov): Notes read dialogs outside main, read links in the editor, and wait for an enabled Post | The fake DOM answers those calls |
| substack_native_caption_readback (3) | 154d838c (CC-453): readback checks the identity bound in the request | The fake request carries it |
| ppi_source_projection (3) | 104a2770 (CC-145): `history_documents` reads the producer | The fixture names its producer |
| rolling_x_grounded_article_media_builder (1) | 8de240b1 and d4009b2c (CC-423, CC-451): every derivative closes with both notices | Expected X reply |
| weekly_coordinator_readbacks (1) | 03b8a7c0 (CC-402): audience metrics keep an exactly identified object with failed copy | Engagement counts it; coverage still does not |
| scheduler_v6 (1) | fcd5aeb0 (CC-297): tests read secrets from the process environment only | Controlled Instagram dry-run binding |
| security_scans (1, then 2 hidden) | 19663007 (CC-639), db18c941 (CC-436), cc585388 (CC-681) and five modules of 5-12 Nov (see the test comments) | Each network module added to its allowlist. **Ops Product: please glance at this list.** These are the existing publishing and readback modules, not new network paths. |

No test on the posting path lost a check. Where a test now accepts something it used to refuse, it is
a model, effort or reviewer label that decision 60 says is recorded, not refused. The identity, run,
surface, invocation, link, image and exact-review checks are all still asserted.

## Checks on this branch

- After merging the live head 74235574 (Builder I), the 52 changed or covering test files and Builder I's
  5 files ran: 1,261 passed, 3 failed (the follow-ups above). After commit a95935b4 those 3 files give
  24 passed and 0 failed.
- A full-suite run on the branch head follows (next section).

## Left over (owner)

- Ops Product: the shutdown control (`prepare_safe_shutdown`) builds the whole Daily App snapshot. That
  reads every live headline sidecar, which now takes more than 5 s. The operator console's shutdown can
  therefore be slow. This is not fixed here; the test now uses empty sidecars.
- Ops Product: confirm the security-scan allowlist additions above.
- Builder H's modules were not edited. No real defect needed one.
