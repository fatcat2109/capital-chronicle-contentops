# CC-515: minute consumer recovery

CC-515 is integrated in the Publisher operating root. The first normal minute result closes 73 old obligations and reports zero waiting posts older than 24 hours. It retains every original payload and public dispatch identity. The first complete post-install day remains to be measured; no full-day request-count success is claimed.

The second-stream delivery was based on operating HEAD `e16ddb8caf45cd859d6584c82425a1425967b86d`. The first Publisher stream integrated it onto `b896aaa9f129cd338ffafdb1543b753cf5554dc8`. Exact source, tests, live and rollback tags are in `integration.json`; schedules are unchanged.

## Changed behavior

- Original status and transition seals, their snapshot join, schema names and duplicate plan identities still fail closed. A row-level contract error removes only its plan and related transitions from an in-memory consumer projection. Main validates the remaining rows. Original files/hashes stay bound; separate projection hashes record the filtered view.
- Each rejected row retains its plan ID, original field path and first cause in the existing incident table and minute record. No status or number is guessed. An unavailable or unknown plan never revives an older transition.
- A child of a definitely unwritten parent settles that destination immediately. An unconfirmed parent beyond the existing 24-hour limit also settles its child. Old READY/PUBLISHING copies leave automatic minute work; a partially delivered post closes as SETTLED, never falsely PUBLISHED.
- Confirmed IDs, uncertain dispatch states, immutable payloads and action claims stay intact. Explicit exact-object readback remains available. Automatic coordinator recovery and stored Neo draining omit closed obligations. Recent uncertainty still receives readback and cannot obtain another blind send.
- Run roots precede their children. Card and browser budgets select the newest eligible work. Historical API-complete PUBLISHED roots with unfinished browser copies obey the same late-state limit.
- Every new definite no-write with a returned fixed cause records that cause against its dispatch in the existing readback audit. A first failure of the day can no longer erase the cause of subsequent attempts.

## Retained queue and current export

`queue-replay.json` replays the 20:32:13 GMT+7 read-only snapshot into a small temporary store. It closes 72 of 87 pending roots, leaves 15, and leaves zero waiting roots older than 24 hours. All original root payload hashes and every copied dispatch/public identity remain identical. No publication method is invoked. The replay is not a live cleanup result.

`export-readback.json` records the real Main reader accepting 86 plans and 169 transitions at 20:17:53 GMT+7 on 12 November. Its original capture was 20:17:23 GMT+7 (31 seconds old at completion). No row was rejected in that current snapshot. Controlled tests supply the unknown-row cases.

`main-reader-isolation.json` exercises Main's actual installed reader with a separately sealed private fixture from its newer 87-plan export. One EUR/USD plan receives an unfamiliar status only in that temporary file; the reader retains the other 86 plans, excludes that plan's transitions and returns its exact rejection cause. Neither source file is written.

## Channel causes, 10–12 November GMT+7

This is a partial-day snapshot, observed at 12 Nov 2026 20:18:48 GMT+7. Counts use the dispatch table’s original attempt clock; later readbacks are separate observations. A request packet differs from its internal request/start/return records. On 12 November the audit sees 634 request packets and 1901 total internal Neo records at this snapshot.

| Destination | Confirmed | Definite no-write | Uncertain/pending/retry | First causes of definite no-writes |
|---|---:|---:|---:|---|
| discord | 22 | 20 | 2 | `ATTEMPT_CAUSE_NOT_RETAINED` × 16; `DISCORD_CALL_THREAD_BOT_TOKEN_UNAVAILABLE` × 2; `EVERY_POST_IMAGE_REQUIRED:discord` × 1; `TRADINGVIEW_FIRST_IMAGE_WRONG_TYPE` × 1 |
| facebook_page | 36 | 1 | 0 | `EVERY_POST_IMAGE_REQUIRED:facebook_page` × 1 |
| instagram_business | 36 | 0 | 0 | None |
| linkedin | 0 | 4 | 1 | `ATTEMPT_CAUSE_NOT_RETAINED` × 1; `EVERY_POST_IMAGE_REQUIRED:linkedin` × 1; `TRADINGVIEW_FIRST_IMAGE_WRONG_TYPE` × 1; `TRANSPORT_TLS_HANDSHAKE_UNAVAILABLE` × 1 |
| linkedin_company | 0 | 3 | 0 | `LINKEDIN_NON_API_AUTOMATION_PROHIBITED` × 3 |
| substack | 9 | 1 | 3 | `ATTEMPT_CAUSE_NOT_RETAINED` × 1 |
| substack_notes | 11 | 7 | 3 | `ATTEMPT_CAUSE_NOT_RETAINED` × 4; `CC401_STALE_STATUS_NOTE_UNCLAIMED` × 3 |
| telegram | 65 | 0 | 0 | None |
| threads | 57 | 1 | 2 | `EVERY_POST_IMAGE_REQUIRED:threads` × 1 |
| x | 6 | 17 | 1 | `NEO_COMPOSER_PREPARATION_FAILED` × 2; `NEO_REGISTERED_PROFILE_UNAVAILABLE` × 5; `TRADINGVIEW_FIRST_IMAGE_WRONG_TYPE` × 6; `X_NON_API_AUTOMATION_PROHIBITED` × 4 |
| youtube | 0 | 6 | 0 | `YOUTUBE_NON_API_AUTOMATION_PROHIBITED` × 6 |

Old policy refusals are facts about those attempts. Decision 112 restored X; decision 121 restored company LinkedIn and YouTube. Their old policy no-writes remain closed under the no-backfill decision.

X’s leading retained cause is `TRADINGVIEW_FIRST_IMAGE_WRONG_TYPE` on six old drawn fact-card packages. Those frozen assets cannot be relabelled or silently replaced under decision 82. CC-459/463/465 already give new packages the TradingView/template path; this change stops old packages consuming every new tick. The five `NEO_REGISTERED_PROFILE_UNAVAILABLE` attempts and two composer failures retain their own source epoch. Existing CC-436 repair/retry proof remains available for a fresh eligible copy; it does not reopen stale work.

For Discord, the bot-token thread cause is local configuration of legacy registered cards. CC-437 already chooses the webhook channel for newly queued cards. This delivery settles their unsendable children without changing frozen thread parents. For Notes, three `CC401_STALE_STATUS_NOTE_UNCLAIMED` closures were deliberate stale-copy cancellations; closing their dependent minute work is the repair. The other unrecorded attempts are not assigned an invented platform cause.

LinkedIn’s recorded `TRANSPORT_TLS_HANDSHAKE_UNAVAILABLE` precedes HTTP in its official adapter. This is a connection/TLS constraint; no authentication failure, platform restriction or accepted write is inferred. Old missing/wrong images keep their exact refusal; existing new-image producers remain the path for new posts.

Company LinkedIn and YouTube each have `NO_NEW_ARTICLE_INTENT_SINCE_CC454_INSTALL`, verified against outbox creation after installation at 07:08:20 GMT+7 on 11 November. Their stored attempts are the earlier policy no-writes. There is no new public post to read back. CC-454 already wires both article transports; decision 121 bars backfill and adding call cards for a canary. The next existing article supplies their public readback or exact failure. The current route suspension file is empty; a platform restriction is not claimed.

Twenty-two older definite no-writes have no precise first cause in their retained attempt record. The audit searched exact native request/return pairs, per-dispatch readbacks, reconciliations, day-failure incidents and minute-run records. `ATTEMPT_CAUSE_NOT_RETAINED` describes that evidence gap; it is not an inferred failure and does not block new work. The new per-dispatch cause record prevents recurrence.

## Exact no-write attempts

Each row links an exact dispatch to its retained first cause. `channel-health.json` contains the source record/path for every cause and all distinct later causes.

| Destination | Dispatch | First cause |
|---|---|---|
| substack_notes | `dispatch_2e5a55e29f03ca70094eb5f39ea4496a` | `CC401_STALE_STATUS_NOTE_UNCLAIMED` |
| substack_notes | `dispatch_1e8b666c608b9df5feaf073366aaf47d` | `CC401_STALE_STATUS_NOTE_UNCLAIMED` |
| substack_notes | `dispatch_76be49b9c3b261491b10d1b849a2cbe0` | `CC401_STALE_STATUS_NOTE_UNCLAIMED` |
| x | `dispatch_e77511fa0b8d00eed57b1f3441a13d76` | `X_NON_API_AUTOMATION_PROHIBITED` |
| x | `dispatch_ce7b300f39c0bceb0b470bbbf6d1fa63` | `X_NON_API_AUTOMATION_PROHIBITED` |
| x | `dispatch_88de3e5ad3c9cfd8a70844fe78bce773` | `X_NON_API_AUTOMATION_PROHIBITED` |
| x | `dispatch_85a9e8d5a33dcf9e0c1bc199ae9e9260` | `X_NON_API_AUTOMATION_PROHIBITED` |
| youtube | `dispatch_a2d9c1a9cc88607400b5422dd72bf451` | `YOUTUBE_NON_API_AUTOMATION_PROHIBITED` |
| youtube | `dispatch_5147b0b8405e76baaea4cf29b22f1c86` | `YOUTUBE_NON_API_AUTOMATION_PROHIBITED` |
| youtube | `dispatch_62350db132f54a0a56aaba3113bb8d69` | `YOUTUBE_NON_API_AUTOMATION_PROHIBITED` |
| discord | `dispatch_3c4e250327010a53aefcdb639f1a254f` | `DISCORD_CALL_THREAD_BOT_TOKEN_UNAVAILABLE` |
| substack_notes | `dispatch_d29d1ad24731f32f4881877bf125a459` | `ATTEMPT_CAUSE_NOT_RETAINED` |
| x | `dispatch_1fcc1170e164b0ee51a8ef540a8ffdfd` | `NEO_COMPOSER_PREPARATION_FAILED` |
| discord | `dispatch_8488c1ee023346b322ed3a2969398498` | `DISCORD_CALL_THREAD_BOT_TOKEN_UNAVAILABLE` |
| substack_notes | `dispatch_b59a32210485e974a508c68a8eedbc91` | `ATTEMPT_CAUSE_NOT_RETAINED` |
| x | `dispatch_716fd6a3874b63452853c187c513c4e8` | `NEO_COMPOSER_PREPARATION_FAILED` |
| youtube | `dispatch_bf84a6573a0359a677181b545d4d0670` | `YOUTUBE_NON_API_AUTOMATION_PROHIBITED` |
| linkedin_company | `dispatch_f543957b3d6021d669f6e2e3ffc0207d` | `LINKEDIN_NON_API_AUTOMATION_PROHIBITED` |
| youtube | `dispatch_f533d0a86be939edca0d6533b8ef760b` | `YOUTUBE_NON_API_AUTOMATION_PROHIBITED` |
| linkedin_company | `dispatch_6c0b9765fe70321e9f7c40511bde130c` | `LINKEDIN_NON_API_AUTOMATION_PROHIBITED` |
| youtube | `dispatch_b2d14293ada5a2990013f175c313543e` | `YOUTUBE_NON_API_AUTOMATION_PROHIBITED` |
| linkedin_company | `dispatch_cf89f2238980631f627ed341ca075b53` | `LINKEDIN_NON_API_AUTOMATION_PROHIBITED` |
| discord | `dispatch_4823c673a528ccf2857c55d8afc64232` | `ATTEMPT_CAUSE_NOT_RETAINED` |
| discord | `dispatch_f12d6e4d487e1bc499fb50abb689d20f` | `ATTEMPT_CAUSE_NOT_RETAINED` |
| discord | `dispatch_d148a76912d60e00c899c8f5ccdeccd5` | `ATTEMPT_CAUSE_NOT_RETAINED` |
| discord | `dispatch_62bf1328c28c3b425c97719a81620859` | `ATTEMPT_CAUSE_NOT_RETAINED` |
| substack_notes | `dispatch_63cdfa22db65e4c8391f3a985e3a59bb` | `ATTEMPT_CAUSE_NOT_RETAINED` |
| x | `dispatch_8f929fba39ad5f3f269469e2f8651a8f` | `NEO_REGISTERED_PROFILE_UNAVAILABLE` |
| discord | `dispatch_b1088b90fafe7725f52b84141e87686c` | `ATTEMPT_CAUSE_NOT_RETAINED` |
| discord | `dispatch_3bbe00bd35f8fd64a43d28c3f2fe9c15` | `ATTEMPT_CAUSE_NOT_RETAINED` |
| discord | `dispatch_3fa8a7154c644618d7e437f95e9eacf1` | `ATTEMPT_CAUSE_NOT_RETAINED` |
| discord | `dispatch_4f1f0fb1933f51532061167c838a5978` | `ATTEMPT_CAUSE_NOT_RETAINED` |
| discord | `dispatch_c48eedb7980c11d5b6740084f94138a1` | `ATTEMPT_CAUSE_NOT_RETAINED` |
| substack_notes | `dispatch_90a275ffb1f5f6d221fd40f385ae3cbe` | `ATTEMPT_CAUSE_NOT_RETAINED` |
| x | `dispatch_14beeb9dc225efbc67ee63905a517e40` | `NEO_REGISTERED_PROFILE_UNAVAILABLE` |
| discord | `dispatch_8cfe311dbd3098af0d9d9f228b96a2a3` | `ATTEMPT_CAUSE_NOT_RETAINED` |
| discord | `dispatch_d8842c518873000c4ba649c3778b06a0` | `ATTEMPT_CAUSE_NOT_RETAINED` |
| discord | `dispatch_8ebfd9f6c680f953e0086629c7c7367c` | `ATTEMPT_CAUSE_NOT_RETAINED` |
| discord | `dispatch_1fca55431092f5d31f03efcee9739a9a` | `ATTEMPT_CAUSE_NOT_RETAINED` |
| discord | `dispatch_1d37bcdb468e5127a4a8d182c6278aa6` | `ATTEMPT_CAUSE_NOT_RETAINED` |
| discord | `dispatch_58cdd90cddb919be90132fa7f339fd90` | `ATTEMPT_CAUSE_NOT_RETAINED` |
| x | `dispatch_b8807cda44a5be651045faa478a4706e` | `NEO_REGISTERED_PROFILE_UNAVAILABLE` |
| discord | `dispatch_bceb8ea99d001518c788bd6a65270b67` | `ATTEMPT_CAUSE_NOT_RETAINED` |
| x | `dispatch_fe41ead4a763c55d9fe1c2c97b960593` | `NEO_REGISTERED_PROFILE_UNAVAILABLE` |
| x | `dispatch_9b8ef682833593935aa5953af0c841ed` | `NEO_REGISTERED_PROFILE_UNAVAILABLE` |
| linkedin | `dispatch_28a484646fa8beeb8fe712bfb6449d67` | `TRANSPORT_TLS_HANDSHAKE_UNAVAILABLE` |
| facebook_page | `dispatch_fb8d6dfa39df1e85edc6b69f50ee1cee` | `EVERY_POST_IMAGE_REQUIRED:facebook_page` |
| threads | `dispatch_ac218aeb4b7b763d9c57993b0e069283` | `EVERY_POST_IMAGE_REQUIRED:threads` |
| linkedin | `dispatch_4598e9f4d0a9b251ffc834bad461ddb4` | `ATTEMPT_CAUSE_NOT_RETAINED` |
| discord | `dispatch_086aeb35307769b705368faccc2acaaf` | `TRADINGVIEW_FIRST_IMAGE_WRONG_TYPE` |
| linkedin | `dispatch_33c8914bb5e0d6cdd77d9491f0e7f32d` | `TRADINGVIEW_FIRST_IMAGE_WRONG_TYPE` |
| x | `dispatch_39c748f94e3a74da224f69b9046c80dc` | `TRADINGVIEW_FIRST_IMAGE_WRONG_TYPE` |
| discord | `dispatch_900ed1c9ac43e68ed3da5652b377439d` | `EVERY_POST_IMAGE_REQUIRED:discord` |
| linkedin | `dispatch_ca4ae91f74467997d458e63151ccd92d` | `EVERY_POST_IMAGE_REQUIRED:linkedin` |
| x | `dispatch_478932297f67ea7dfabf30282223b47f` | `TRADINGVIEW_FIRST_IMAGE_WRONG_TYPE` |
| x | `dispatch_7f9f09be6d45f275d0b8e6fa9091aaf1` | `TRADINGVIEW_FIRST_IMAGE_WRONG_TYPE` |
| x | `dispatch_b234934dfcf7f3ed0c714475f7fa6cf8` | `TRADINGVIEW_FIRST_IMAGE_WRONG_TYPE` |
| x | `dispatch_29eb59803216530bd6e7199922fc74d6` | `TRADINGVIEW_FIRST_IMAGE_WRONG_TYPE` |
| x | `dispatch_785293c62a56e121a3d46a31446e438b` | `TRADINGVIEW_FIRST_IMAGE_WRONG_TYPE` |
| substack | `dispatch_eb2b3966e02acc41dff6e05958a7f067` | `ATTEMPT_CAUSE_NOT_RETAINED` |

## Validation and integration

The final targeted runs pass 258 distinct cases: 42 minute/Discord, 52 endpoint, 118 coordinator and 46 export/image cases. The final queue adjustment also passes 9 selected cases. Exact results are in `validation.json` and the named XML files. Test fixture repairs isolate newer minute-entry dependencies and supply the proper image boundary for transport-only fixtures. The real image contract keeps its separate asset tests; no production guard is relaxed.

`test-isolation-correction.json` records an outdated CLI fixture that reached the real public export and editorial CLI during an interrupted test run. One temporary writer return completed; the remaining child was stopped. These returns are excluded from product and passing-test evidence. The CLI fixtures now explicitly replace the unrelated consumers. No public outcome is claimed from that test.

The first Publisher stream must merge this branch into the operating HEAD, rerun the targeted changed-path checks, tag the install and read one normal minute result. Confirm zero pending roots older than 24 hours; measure the next full day’s distinct internal request packets below 200; preserve every fresh post and exact uncertain dispatch. Then record the next X, member LinkedIn and company LinkedIn article/plan outcomes, and the next YouTube article outcome. This branch does not claim those future observations.

Launch arguments observed in the existing process configured `gpt-6.1-sol` and `model_reasoning_effort="max"`: CONFIGURED_NOT_OBSERVED for actual model telemetry. Deterministic implementation requires no editorial generation. The test-isolation correction records the unintended temporary invocation separately.

## Publisher integration, 12 November 2026

The first Publisher stream resumes the exact pushed delivery on operating HEAD `b896aaa9f129cd338ffafdb1543b753cf5554dc8`, retaining the CC-511 and CC-512 integrations. The integration branch is `backlog/cc-515-minute-consumer-integrate`. The serial merge checks and the interrupted, excluded run are recorded in `integration.json`.

The existing minute result now includes `pending_post_queue`: its current count, the count older than 24 hours and the oldest age. A targeted test drives settlement through the live `publish_ready` consumer and reads that same result field from `record_run`. The new observer, `observe_live.py`, reads the existing store in SQLite read-only mode and retains exact root payload hashes, public dispatch identities, request-packet and internal-record counts, and the recent minute results. It creates no scheduler, coordination queue or public object.

`live-before-integration.json` is the 21:05:09 GMT+7 baseline: 87 pending roots, 72 older than 24 hours, and 668 request packets already created on 12 November. A cumulative count cannot fall below 200 later that same day. The first complete post-install GMT+7 day is 13 November, ending 14 November 00:00 GMT+7. A short post-install observation is reported separately and cannot certify that full-day acceptance claim.

The merge `33f5ad09b615b3d205e955f120c82cb976093417` is installed at 21:18:37 GMT+7. Live and rollback tags are `contentops-live-20261112-cc515` and `contentops-rollback-20261112-cc515`. The merge passed 259 targeted cases; four installed queue cases also passed. The installed source and all eight unrelated WIP hashes match `installed-source-readback.json`.

The first normal minute result at **21:21:55 GMT+7** reports **73 SETTLED, 14 pending, zero older than 24 hours** and zero stored browser requests. `live-after-integration.json` retains the result; `live-preservation-proof.json` proves every baseline root and payload, all baseline dispatch states/public identities, and all 15 previously recent roots remain. One recent root settled its definite no-write destination; fourteen remain in the active queue. The one internal request after installation was an existing plan-page Notes readback, not an old status-card request (`requests-after-install.json`). The full-day count remains unobserved.

The new minute result also exposes a separate local derivative defect: a retained plan-page packet with an omitted fundamental layer raises a literal `KeyError('fundamental')` while composing its Telegram/Notes links. The Publisher integration corrected that consumer to omit absent source layers under CC-466's current contract. Other retained results name `outcome.score.result_r` absent, `PLAN_CARD_REPLY_PARENT_CHANGED`, and `SUBSTACK_PLAN_PAGE_NOT_CONFIRMED`; their exact causes stay attached.

The preserved request after the first install belonged to the 10 November Notes plan-page link `plan-analysis-link-plan_79ec7bb46eb37b474f0f2c04-substack_notes`. The same 24-hour automatic-work limit now covers plan-page links and run indexes as well as status-card roots. Settling changes the internal work statuses and adds its cause to the existing incident table; it never changes the original payload or dispatch certainty. Recent links continue, and the same exact-object readback remains available for late `UNKNOWN_WRITE` copies. The targeted test exercises both the consumer and stored-browser drain, with a recent live control.

Acceptance is split by observation, not by code delivery. The installed row and queue consumers pass their tests and the normal minute run proves the stale queue cleanup. The full-day target is still **NOT OBSERVED**, with its exact next check at **14 November 00:00 GMT+7**. The item remains open for that observation; no Ops review, credential action, schedule change or manual test post is required.

| Destination | Latest exact cause retained in the normal minute result |
|---|---|
| X plan links | `PLAN_ANALYSIS_PARENT_NOT_CONFIRMED`; the unsent current setup also has `SUBSTACK_PLAN_PAGE_NOT_CONFIRMED`. Historical wrong-image/profile causes remain in the attempt table above. |
| LinkedIn member | `DESTINATION_FAILED_ET_DAY_SKIP`; its bound first attempt records `TRANSPORT_TLS_HANDSHAKE_UNAVAILABLE` before HTTP. No platform restriction or accepted write is inferred. |
| LinkedIn company | `NO_NEW_ARTICLE_INTENT_SINCE_CC454_INSTALL`; decision 121 keeps historical refusals closed and does not add call-card posts. |
| YouTube | `NO_NEW_ARTICLE_INTENT_SINCE_CC454_INSTALL`; the next natural article supplies the allowed route's outcome. |
| Discord | Earlier bot-token thread failures keep their cause; new cards use CC-437's existing channel route. Current old child packages retain `PLAN_CARD_REPLY_PARENT_CHANGED` rather than being sent under a different parent. |
| Substack Notes | The old plan-page `UNKNOWN_WRITE` automatic readback now obeys the same 24-hour settlement limit. Its exact dispatch and explicit readback remain. |

The normal minute result at **21:40:55 GMT+7** observes the old Notes plan-page link as SETTLED, with zero stored-browser requests and zero waiting roots older than 24 hours. `live-final-readback.json` preserves that observation. The final two-case regression also proves general automatic coordinator recovery omits a settled link, a recent uncertain link remains eligible, exact readback still runs, and the existing minute record retains the settlement cause. It passed in 3.03 seconds during the short-test window.

Final code is `4662828b8b198624a01101d9ca21b6f394fb6b31`, installed and tagged `contentops-live-20261112-cc515-recovery-verified`. Six installed implementation files and all eight unrelated WIP hashes match `installed-source-readback.json`. The final installed link/recovery control passed two cases in 4.39 seconds. No browser, application control, Claude invocation, chat message or schedule change was used by this integration run.

The latest observed scheduled result at **21:43:11 GMT+7** remains **14 pending, zero older than 24 hours, zero stored-browser requests**. `live-completion-readback.json` shows 681 cumulative request packets on 12 November and none created during its short interval after final source installation. It also retains the settled old Notes link. The minute process began before the final cause-record formatting change; that exact formatting has the installed two-case test, with its next natural result still separate. The short interval does not prove the next complete day is below 200. The item is **OPEN for live acceptance observation**, with the full-day check due **14 November 00:00 GMT+7** and the next naturally eligible article/plan outcomes retaining their destination causes. All implementation and integration work is pushed and live; no Ops review is pending.

