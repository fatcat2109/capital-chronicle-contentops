# Delivery: backlog/prerelaunch-decision-checks-20261123

Pre-relaunch audit of the evening decision checks (CC-690, CC-756, CC-731, CC-432, CC-639), built by a Claude Builder for Ops Product on 23 Nov 2026 (Jim's order of 09:22Z: no posting until the relaunch; audit before going live).

- Branch: `backlog/prerelaunch-decision-checks-20261123`
- Code commit: `1970a90fe2785c6956bfc1e1df35ce995759ce68` (this note is the next commit on the same branch)
- Base: `b4508d05d948035b3d29d2f990353a1889a0d626` (the live head at the start)
- Nothing was posted, sent, tagged or merged; the production store and `Runtime` were only read.

## Files changed

- `live_contentops/public_decision_checks_v1.py` (the checks)
- `live_contentops/day_readback_v1.py` (correction rows as decision source; manual Posted mark time; pause line in the evening file)
- `scripts/run_day_readback.py` (prints the pause state)
- `tests/test_prerelaunch_decision_checks_20261123.py` (new, 26 tests)
- `tests/test_public_decision_checks_cc690.py`, `tests/test_day_readback_cc639.py`: three expectations moved to the new rule (a target is a decision 157 failure only under the policy; their fixtures are dated 17 and 19 Nov, so they now carry `target_policy` or expect `BEFORE_POLICY`)

## How it was checked

- Store copy: `C:\CapitalChronicleScratch\builder-d-audit-data\contentops_daily_app_v1.sqlite3` (sqlite backup API from a `mode=ro` connection).
- Replay: `C:\CapitalChronicleScratch\builder-d-audit-scripts\replay_days.py` runs `build_report` with no HTTP (`fetcher=None`) on six evening windows (18/19 Nov 12:15Z to 23/24 Nov 12:15Z); the SQLite connection is redirected to the copy, runtime files are read read-only. Output: `C:\CapitalChronicleScratch\builder-d-audit-data\replay\baseline\` (live code) and `...\replay\final\` (this branch), each window with `report.json` and `copies.json` (the text each check read).
- One public read: Telegram 229's embed page and photo, fetched once (`...\builder-d-audit-data\public-images\`).

## What the checks got wrong, and the fixes (19-23 Nov windows, baseline to final)

FAIL rows: 708 to 542. Each remaining FAIL was read against its post; they are real (see "Left as is").

| Decision | Platform | Count | Example | Kind | Fix |
|---|---|---|---|---|---|
| 157 target | all 9 plan routes | 116 false failures | t.me/CapitalChronicle/226 (22 Nov 19:27Z): "Target level: 53,000", row queued 19:25Z, before the 22:30Z policy | false | `_target_policy`, `_plan_target`: FAIL only for a row marked `DECISION_40_NO_TARGET` or a copy frozen from 22 Nov 22:30Z; earlier ones are listed `BEFORE_POLICY` (126) |
| 157 target | threads 8, x 2 | 10 missed | Threads USD/JPY 20 Nov 08:17Z: "Target level: 157.95." sat in the thread reply, which the readback never verified | missed | `PublicCopy.bound_reply_texts`: a confirmed dispatch whose readback verified only the root contributes its frozen `reply_texts` |
| CC-729 notices once | threads | 6 missed (no check existed) | Threads root and reply each printed both notices (20 Nov) | missed | new `_notices` / `notice_counts` check, decision id CC-729 |
| CC-768 dated results | telegram, discord | no check existed | correction reply 232 under post 230 | missed | new `_result_frame`: results from 23 Nov 04:00Z print their plan dates and "Correction to the" when corrected; correction replies carry a label and a date; `correction-*` rows read as their source |
| 158 voice | all | 50 false ENTRY_ZONE_MISSING, 111 false INVALIDATION_LEVEL_MISSING flags | "Cancel if spot price trades at or above 3,609 before entry"; "if price breaks through 3,566 (breakout)" | false flags | `_INVALIDATION_LEVEL` reads the cancel line, `_ENTRY_LEVEL` reads "breaks through"; `_POSITION_WORD` skips net long/short, short covering/interest; correction notes get only the position-word rule. Final: 0 and 0 |
| 113 analysis link | telegram, discord | 2 false | Telegram 226: the update 227 replied first, the link reply 228 followed at 19:58Z | false | `_analysis`: a dedicated `plan_analysis_link` reply under the post counts wherever it sits |
| 82 chart | telegram 6, facebook 3, instagram 3, threads 3 | 15 false | Telegram 229: the public 800x450 JPEG is the uploaded 1600x900 gold chart (sha 6abae0f1..., rms 7.8, worst tile 19.9 under the stored pixel rule) | false | `_chart`: on these re-encoding routes a pixel MISMATCH with the right symbol is `UNVERIFIED` (`POSTED_CHART_RECOMPRESSED_UNVERIFIED`) and prepares no correction reply. Only Telegram was confirmed by eye; Facebook, Instagram and Threads are the same re-encoding case, NOT VERIFIED one by one |
| CC-672 coverage | 8 routes | 32 false | setup copies `SUPERSEDED_NOT_POSTED` (PLAN_ALREADY_FILLED / CANCELLED) | false | `_coverage`: `EXPECTED` (`PLAN_COPY_SUPERSEDED_BY_LATER_STATE`) |
| CC-672, CC-684, 98 | x, substack_notes, linkedin_company | 4 + 3 false | copies settled with `JIM_POSTS_BY_HAND_20261123` | false | `EXPECTED` (`..._HANDED_TO_JIM`) from 22 Nov 20:31Z, read from `control/suspended_routes.json` (or the pause's saved copy); the Sunday 22 Nov 18:00Z wrap stays a failure |

Antigravity's first pass (input only): `C:\CapitalChronicleScratch\builder-d-audit-scripts\agy_first_pass.py` sent the 52 distinct plan-copy texts to `call_light(callers=("antigravity",))` in 13 batches; 10 answered (40 texts), 3 timed out at 180 s. Its reading agreed with this branch's code on all 40 texts for target, cases, entry level, invalidation level, repeated notices and position words; with the live code it disagreed on 17 entry and 31 invalidation readings, which matches the false flags fixed above. Evidence: `...\builder-d-audit-data\agy-first-pass\`, `agy-compare.txt`, `agy-compare-livehead.txt`.

## Paused days

- The pause is read from `control/pause-*/manifest.json` (`paused_at_utc`, `cause`) and ends at `restored.json`'s `started_at_utc`; no `restored.json` means still paused.
- A copy, wrap, first post, LinkedIn copy or Discord channel copy that falls due inside the pause gets status `PAUSED` with `pause_cause`. On a day the pause covers completely, older unresolved copies (already reported on their own day) are `PAUSED` with `carried_over: true`.
- `decision_checks.json` gains `pause`: `{"state": "PAUSED" | "PARTLY_PAUSED", "cause", "paused_at_utc", "restored_at_utc", "public_copies_in_window", "held_checks"}`; the evening file opens its Decision checks with "Paused: posting paused since ... (cause) ..."; the command prints `pause`.
- Replay of 23/24 Nov 12:15Z: state PAUSED, cause `JIM_PAUSE_20261123T0450Z_UNTIL_20261125T1600Z`, 0 failures, 19 held (live code on the same window: 22 failures, 10 missing-wrap rows and 12 carried-over copies; `...\replay\baseline-paused\`).
- `PAUSED`, `EXPECTED` and `BEFORE_POLICY` never count as failures or unverified; each check row lists them by status.

## Tests

- `tests/test_public_decision_checks_cc690.py tests/test_day_readback_cc639.py tests/test_public_output_golden_cc691.py tests/test_prerelaunch_decision_checks_20261123.py`: 124 passed on 1970a90f (`C:\CapitalChronicleScratch\builder-d-audit-data\targeted-tests-1970a90f.xml`).
- `tests/test_image_templates_cc465.py tests/test_plan_queue_clock_cc732.py tests/test_plan_state_alerts_cc543.py`: 132 passed, 1 failed: `tests/test_image_templates_cc465.py::test_instagram_publishes_and_reads_back_the_native_chart_and_table` (TypeError, `observe_images` keyword in `_eight_platform_substack_first_pipeline_impl_v1`). The same id fails on the live head b4508d05 (`C:\CapitalChronicleScratch\builder-d-livehead`): not caused by this branch.

## Left as is (real, not check defects)

- 113: plan posts of 19-21 Nov with no layer lines and no confirmed analysis page (the census finding); 23 Nov setups linking "how we measure a trading rule" instead of their own page (pages stuck at DISPATCH_ATTEMPT_STARTED / READY); internal tokens in Telegram 221 ("TREND DOWN", "2026-12-09T12:00Z").
- 82: BTC setup of 23 Nov 03:58Z posted with no chart (TRADINGVIEW_SNAPSHOT_TIMEOUT); the BTC plan page of 22 Nov has no chart.
- CC-672: UNKNOWN_WRITE copies (X binding mismatches, Notes composer, Threads/Facebook PUBLISHING_OLDER_THAN_24_HOURS); LinkedIn copies stale on CC684_LINKEDIN_PLAN_PAGE_NOT_CONFIRMED.
- 98: the 22 Nov Sunday wrap missing on LinkedIn, the company page, Notes and X (due before the hand-posting start).
- CC-732 queue alarms (PLAN_TRANSITION_REPLACED_BY_RESULT and others) were not re-judged; outside this brief.
- The stored pixel rule itself (`neo_endpoint_executor_v1.compare_public_images`, RGB_BLUR075_TILE32_LUMA60_V1) is in another owner's file: it still records MISMATCH on re-encoded images. The checks now treat that as unverified; the rule needs a scale-aware threshold from its owner.
- The 158 scenario-case flag stays on every pre-CC-755 post ("Main/Alternative" wording): a true flag until posts carry the voice contract.
