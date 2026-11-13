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
| Filled-position horizon | explicit `time_exit_utc`, then `horizon_end_utc`, `forecast_probabilities.horizon_end_utc`, `scenario_analysis.horizon_end_utc` | 13 Nov, 8:15 AM ET |

All MGC prices come from its complete instrument mapping. Without that mapping, new copy names Gold and explicitly labels its spot close condition; it never presents spot prices as MGC prices. Entry and invalidation numbers are bound to individual source pointers; price rounding uses the exported tick. Scenario odds retain their separate explicit source and never use a probability complement.

## Verification

- [Gold thread and alert checks](alerts-and-thread.xml): 22 passed, including the existing two-API coordinator replay, chart requirement, unchanged alert payload and reply recovery.
- [Editorial and public-copy checks](editorial-and-guard.xml): 169 passed. The gold replay recomposes the first post, reply and title, checks both clocks, rejects the observed wording, and proves the real queue passes the frozen source into the page consumer.
- Tests use isolated stores and controlled model/transport returns. This run made no editorial model call. Launch arguments observed on process 31460: `gpt-6.1-sol`, effort `max`, **CONFIGURED_NOT_OBSERVED**; runtime model/effort are not observed.

Integration and next-thread public readback are pending. The next natural Main registration must produce its own Telegram root and reply; their exact URLs belong here before DONE. No old post is edited or test plan published to satisfy that acceptance.

## 14 November continuation

The retained build was reapplied on the operating HEAD `1d0748e3` as `backlog/cc-549-plan-thread-consistency-squashed`, preserving the later Discord reply fix. The first current-base replay passed 22 checks in [thread-alerts-current.xml](thread-alerts-current.xml). Launch arguments for process 31928 name `gpt-6.1-sol`, effort `max`, **CONFIGURED_NOT_OBSERVED**; actual model and effort telemetry is unavailable. The existing two telemetry files remain outside this delivery.

The continuation found and repaired a result regression: freezing first-alert terms must not hide a later Main-signed R result. A result row now retains its exact later public outcome and hash separately from its original levels; the write-boundary check binds it to the same plan and registration. [The failing replay](result-source-red.xml) and [three passing recovery checks](result-and-thread-recovery-green.xml) cover this. The broader consumer run had 51 passes and two failures in an old Discord fixture that still required the invalid starter reference removed by installed CC-432; that fixture now checks the accepted thread behavior. Its original failures remain in [thread-consumers-current.xml](thread-consumers-current.xml).
