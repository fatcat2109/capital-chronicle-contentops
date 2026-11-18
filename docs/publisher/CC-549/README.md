# CC-549: one plan thread, one set of terms

New plan alerts, their analysis reply and the page title name the same two conditions: **Spot close above 3,972.6; MGC invalidation above 4,004.4** in the retained gold replay. A close condition is not silently substituted for the named futures instrument's invalidation. The entry deadline is **13 November, 1:00 AM ET**; **8:15 AM ET** is when a filled position closes by. An expired-entry update says the entry window ended, without claiming a position closed.

The existing `CC543_V1` alert queue attaches `CC549_V1` only to new rows. It keeps the first alert's source plan for its page and subsequent state updates, so later instrument enrichment cannot change a thread's prices. Existing issued requests, prepared payloads and public objects retain their original dialect and bytes. The original Telegram [post 181](https://t.me/CapitalChronicle/181) and [reply 182](https://t.me/CapitalChronicle/182) are unchanged; neither proves this change live.

The page writer now receives an explicit **we/us/our** instruction, the exact structured terms and separate clocks. The existing binder supplies those structured facts; the MAX writer continues to author the explanation. New copy refuses first-person singular and the observed input-language defects: `supplied`, `provided`, `the pack`, `the review given`. A summary that merely watches or tracks an unspecified force is omitted. The ordinary source, rights, notices, chart, duplicate and uncertain-write checks still apply.

## Field mapping for the retained gold replay

The fixture is plan `plan_230a9464a193ca7a377d0c41`, registration `2e9a7170c25e5a90935cc4b02a88ace95af9ec63344785ce7074b5af42e2dece`. The public export captured at `2026-11-12T23:20:44.292855Z` has SHA256 `5eb7d047469b277623b7c6583bf85c623083ea553ce547b00ec8d6352c7ed0af`. The earlier issued page had no public-instrument levels; its exact summary is retained separately to test compatibility.

| Reader field | Main field | Display |
|---|---|---|
| Public instrument | `public_instrument.name/symbol/kind/contract_month` | Micro gold (MGC futures, Dec 2026) |
| Direction | `public_instrument.direction`, or the plan's explicit `direction` when absent | bearish |
| Instrument entry | `public_instrument.entries[0].zone_low/zone_high` | 3,954.4, rounded from 3954.3964602861997 to the exported 0.1 tick |
| Instrument invalidation | `public_instrument.invalidation_level` | 4,004.4 |
| Instrument target | `public_instrument.target_level` | 3,876.4 |
| Spot close condition | `invalidation_conditions[0].field/operator/threshold` | Spot close above 3,972.6 |
| Entry opens | `not_before_utc` | 12 Nov, 8:30 AM ET |
| Entry deadline | earliest of `entry_deadline_utc`, `expires_at_utc` | 13 Nov, 1:00 AM ET |
| Later signed result | `outcome.score.result_r`, `realized_r` or `r_multiple` when explicitly exported | Bound to its later public outcome snapshot; never inferred from STOPPED |
| Filled-position horizon | explicit `time_exit_utc`, then `horizon_end_utc`, `forecast_probabilities.horizon_end_utc`, `scenario_analysis.horizon_end_utc` | 13 Nov, 8:15 AM ET |

All MGC prices come from its complete instrument mapping. Without that mapping, new copy names Gold and explicitly labels its spot close condition; it never presents spot prices as MGC prices. Entry and invalidation numbers are bound to individual source pointers; price rounding uses the exported tick. Scenario odds retain their separate explicit source and never use a probability complement.

## Verification

- [Gold thread and alert checks](alerts-and-thread.xml): 22 passed, including the existing two-API coordinator replay, chart requirement, unchanged alert payload and reply recovery.
- [Editorial and public-copy checks](editorial-and-guard.xml): 169 passed. The gold replay recomposes the first post, reply and title, checks both clocks, rejects the observed wording, and proves the real queue passes the frozen source into the page consumer.
- Tests use isolated stores and controlled model/transport returns. This run made no editorial model call. Launch arguments observed on process 31460: `gpt-6.1-sol`, effort `max`, **CONFIGURED_NOT_OBSERVED**; runtime model/effort are not observed.

The corrected source is integrated and pushed in the operating root at `021a8c87323e9bda682627b4a87cc847dcbb7ddd`, applied at **00:17:57 GMT+7 on 14 November**. The live tag is `contentops-live-20261114-cc549`; the rollback tag is `contentops-rollback-20261114-cc549`, pointing to `1d0748e37082c91e299e8ab0b578950218bc1501`. [Integration evidence](integration.json) binds all six installed source files and confirms the eight preserved work files are unchanged. Both tags were pushed and read back.

The [installed consumer checks](installed-thread-consumers.xml) passed **57 tests**. The [installed read-only export render](installed-export-read.json) passed for **78 retained posts**, using the current `2.0.0` contract and zero new queue rows. The existing minute task recorded its first observed installed `IMMEDIATE_ALERTS / OK` phase at **00:19:32 GMT+7**. [Its task and process readback](task-readback.json) retains the active process and Task Scheduler result separately; no terminal completion is inferred for that in-flight run. No application was restarted and no schedule changed.

**Remaining cause: `NEXT_MAIN_PLAN_NOT_REGISTERED`.** The fresh public export has no registration after this integration; its latest registration is **00:40:00 GMT+7 on 13 November**. [The public Telegram readback](telegram-public-readback.json) still ends at [reply 182](https://t.me/CapitalChronicle/182). That original reply and [root 181](https://t.me/CapitalChronicle/181) are unchanged and do not prove the repair live. Main must naturally register its next plan; Publisher then records that new root and reply URL here and checks their terms before DONE. Both new-URL fields remain null. No old post is edited or test plan published to supply the missing sample.

## 14 November continuation

The retained build was reapplied on the operating HEAD `1d0748e3` as `backlog/cc-549-plan-thread-consistency-squashed`, preserving the later Discord reply fix. The first current-base replay passed 22 checks in [thread-alerts-current.xml](thread-alerts-current.xml). Launch arguments for process 31928 name `gpt-6.1-sol`, effort `max`, **CONFIGURED_NOT_OBSERVED**; actual model and effort telemetry is unavailable. The existing two telemetry files remain outside this delivery.

The continuation found and repaired a result regression: freezing first-alert terms must not hide a later Main-signed R result. A result row now retains its exact later public outcome and hash separately from its original levels; the write-boundary check binds it to the same plan and registration. [The failing replay](result-source-red.xml) and [three passing recovery checks](result-and-thread-recovery-green.xml) cover this. The broader consumer run had 51 passes and two failures in an old Discord fixture that still required the invalid starter reference removed by installed CC-432; that fixture now checks the accepted thread behavior. Its original failures remain in [thread-consumers-current.xml](thread-consumers-current.xml).

The current writer/copy checks passed [171 tests](editorial-guards-current.xml). The current page, Discord reply and distribution consumers passed [92 tests](page-replies-current.xml). A direct read of the held public export also composed all 75 six-market plans with complete levels without a term-binding error; this is retained-source coverage, not a new public post.

## 17 November live readback and source fix

The next Main plan is now registered: USD/JPY, `plan_30f3365059e996b2f0d1d79a`, at **13:28:43.661 GMT+7 on 17 November**. The earlier `NEXT_MAIN_PLAN_NOT_REGISTERED` cause is resolved. At **14:36:24 GMT+7**, BrowserOS Neo's public-channel readback confirms [root 188](https://t.me/CapitalChronicle/188) and [status reply 189](https://t.me/CapitalChronicle/189). Both use the same entry range, cancellation condition, target and two clocks. Neither uses first-person singular or the observed writer-input wording. Reply 189 says the entry was not triggered; it does not claim a filled position closed.

| Reader field | Frozen Main field | Display in both posts |
|---|---|---|
| Market | `asset_id`; incomplete `public_instrument` is not used for prices | USD/JPY |
| Entry range | `zone.minimum`, `zone.maximum` | 159.02–159.38 |
| Cancellation before entry | `invalidation_conditions[0].field/operator/threshold` | Spot plan cancelled on high at or above 160.3 before entry |
| Target | `target_level` | 158.05 |
| Entry deadline | `entry_deadline_utc`, earlier than `expires_at_utc` | Tue 17 Nov, 2:00 AM ET |
| Filled-position horizon | `forecast_probabilities.horizon_end_utc` | Wed 18 Nov, 1:30 PM ET |

**The analysis page and its analysis reply are still absent.** Reply 189 is a status result, not the required long analysis reply. The loaded Substack archive shows no page for this new plan. The [readback record](live-readback-20261117.json) retains both observed posts, their checks and null analysis URLs. The [source read](source-read-20261117.json), taken at **14:23:22 GMT+7**, records zero registered page rows and the runtime's exact `SOURCE_PAGE_PENDING / ValueError:PLAN_ANALYSIS_RUN_NOT_FOUND` result.

The Main run is present at `requests/request-dbc0b55a4b96d198`. Its sealed result matches the exported `analysis_result_hash`, and its freeze matches that same result. Main's combined `analysis-native.json` is present; the older `role-pack.json` and `role-evidence.json` are absent. The installed loader mistakes the absent old packaging for an absent run.

Commit `f08c81a6dde4adc86b3bdb51346d934260a08520` fixes this in the existing page loader. It finds the exact named run folder, retains any old role files that exist, and reads the current combined analysis. The existing sealed-result and freeze checks remain. A read of the actual frozen alert source now yields 32 safe source lines, including two exact original-analysis references in the page-writer prompt. This run made no editorial model call.

[The regression before the fix](single-pass-source-red-20261117.xml) reproduces the failure. [The targeted run after the fix](source-and-thread-green-20261117.xml) passes **61 tests** across the thread, page and editorial consumers, including the retained gold thread, old issued payload compatibility, original-analysis use by the real page-writer entry, and rejection of changed result/freeze bindings. One pytest process ran, without workers or shards; no full suite ran.

Delivery branch: `backlog/cc-549-live-readback-20261117`, cut from operating HEAD `de6c35d747e14701ea9b2c5d9af8d0c4ea475a80`. Launch arguments for process 14732 name `gpt-6.1-sol`, effort `max`, **CONFIGURED_NOT_OBSERVED**. Existing unrelated `local-evidence/` files remain outside this delivery.

**Delivery state: BUILT_UNMERGED (Ops review pending).** Under this second-stream run's instructions, no integration or live step was performed. The first Publisher stream integrates the pushed fix, then uses the existing page/reply path and records the canonical page and analysis-reply URLs before DONE. No existing public object was edited, and no schedule or application was changed.

## 18 November operating integration and public readback

The sealed single-pass loader went live at **12:08:07 GMT+7** in
`4d077f14782308ad78c279ca9a475c84951aa7f7`. The public readback exposed a second
issue in the preview. The retained Micro Bitcoin call was too long for the
one-message Threads preview, which dropped its conditional call and failed
the copy check. The preview now uses the publisher's chart-backed continuation
layout. The repair went live at **12:30:09 GMT+7** in
`fef4e9e35e8ee492127d54c84c134763c39d1a6a`. The
[operating record](operating-readback-20261118.json) records the live and rollback
tags, both installed source hashes and the public-channel readback.

Both [branch tests](integration-thread-consumers-20261118.xml) and
[operating-root tests](installed-thread-consumers-20261118.xml) passed 62
targeted checks. The installed CLI preview rendered 90 retained posts. The
Micro Bitcoin Threads preview preserved both invalidation levels and both
clocks across its two posts. The gold replay verified the setup, analysis
reply and page title against the same structured terms.

The [USD/JPY setup](https://t.me/CapitalChronicle/188) and
[status reply](https://t.me/CapitalChronicle/189) carry the same levels and
clocks. The [later correction](https://t.me/CapitalChronicle/192) records that
the price reached the entry zone. The [Bitcoin setup](https://t.me/CapitalChronicle/193)
also carries both invalidations and clocks. The coordinator reconciled its
previously uncertain delivery to the existing post after exact text and identity
readback. Its chart was visible. The public image bytes differed from the
frozen source image, so the reconciliation retains the media comparison limit.

The installed writer received 32 bound source lines from USD/JPY, including
two from Main's sealed original analysis. The live minute publisher later
returned `PAGE_COPY_NEEDS_REPAIR` for an unsupported number in the technical
section. The two actual writer returns retain `gpt-6.1-sol/max` as configured.
The integration and resumed CLI were configured for `gpt-6.2-sol/max`.
Served model and effort telemetry is unavailable for these calls.

**Live acceptance is blocked pending a new eligible Main plan.** The
**12:39:01 GMT+7** export had zero active plans in this publishing route.
The USD/JPY and Bitcoin plans are expired. Their canonical pages and linked
analysis replies are absent from the publication store. On the next eligible
registration, verify the canonical page and the exact linked reply under the
public Telegram setup.
