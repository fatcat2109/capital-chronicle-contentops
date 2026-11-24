# CC-785 delivery: the X-list feed reads new posts within seconds and heals itself

Branch `backlog/cc-785-x-list-feed-lag-20261124`, built by Claude Builder M for Ops Product on 24 Nov 2026 (00:44-01:20Z). It contains Ops Product's live hotfix 06fed062, merged and folded in. There is no tag and no merge into the live root.

## Outcome

- The runner keeps one CDP session open on the list tab. It reads the `ListLatestTweetsTimeline` responses the page fetches by itself, including between ticks, and it ticks at once when new posts arrive. The old runner reloaded the page once a minute, then waited 4 s and closed the socket.
- A quiet page gets X's own "load new posts" key (`.`) every 15 s. A full reload happens only after 60 s with no timeline response, and never more than once a minute (the old rate).
- In market hours (Sun 21:00Z to Fri 22:00Z) the runner ticks every 15 s; outside them, every 60 s.
- Self-heal:
  - After 2 failed captures in a row it replaces the list tab through `/json/new`.
  - After 3 it recreates the tab through the browser target (`Target.createTarget`) and raises the P1.
  - While failures go on, it repeats the browser step at most every 5 minutes.
  - The next good capture clears the P1.
- The export carries a `health` block, so a consumer can never read silence as "no news".
- A STOP file ends the runner within 15 s, even when a call blocks mid-tick.

## Causes, fixes and tests

All tests use fakes. None of them touches port 9222, X or `A:\Capital Chronicle\Runtime`.

| Cause (log of 19-24 Nov, 6,198 records) | Fix | Tests (`tests/test_x_list_feed_cc785.py` unless named) |
|---|---|---|
| 0. **The largest one, found in the log:** 904 `NO_TIMELINE_RESPONSE_WITHIN_SETTLE` and 124 `MINUTE_CAPTURE_TIMEOUT`. A loaded Chrome answered after the 4 s settle, and the runner had already closed the socket. Re-enabling Page and Network every minute also timed out at 10 s. | Kept session: a late response is still read. Settle of up to 15 s, ending 1 s after the first response. Body and attach timeouts of 20 s. The network buffer is capped at 16 MB. | `test_a_timeline_response_after_the_settle_is_still_read`, `test_the_page_own_fetches_are_read_between_ticks_without_a_reload` |
| 1. Tab replacement: `PUT /json/new` had 5 s, Chrome needed 6 s, and orphan tabs were left behind. | Create gets 20 s and close gets 10 s. If the reply is lost, the runner adopts the new list tab from the catalog. It then closes the failed tab and every other list tab, so exactly one stays; it also does this on attach. It never closes a tab that is not the list. | `test_replacement_adopts_a_tab_whose_reply_came_late_and_closes_orphan_list_tabs`, `test_attaching_closes_list_tabs_left_behind_so_one_stays`, `test_an_unrelated_x_tab_is_never_closed`, `test_a_close_failure_keeps_the_new_tab_preferred_after_a_restart` |
| 2. A slow browser was counted as dead, and the runner waited 30 minutes. | Three probe attempts (3 s, 6 s, 12 s; hotfix's `PROBE_ATTEMPTS = 3`). The relaunch wait is 120 s (the hotfix's value). | `test_a_slow_probe_is_not_a_dead_browser`; cc258 `..._relaunches_every_two_minutes`; `tests/test_x_list_feed_hotfix_cc785.py` (both of its tests kept) |
| 3. The PowerShell owner check ran every time it had failed, and under load it found no owner. | The owner is proved natively (TCP table via `GetExtendedTcpTable`, command line via `NtQueryInformationProcess`, start time via `GetProcessTimes`), in 2-3 ms on this machine. PowerShell remains only the fallback. The runner then rechecks that the same PID with the same start time holds port 9222; a change triggers a new proof. The canonical-profile rule is unchanged. | `test_the_owner_check_uses_the_native_read_before_powershell`, `test_the_port_owner_is_proved_once_then_rechecked_by_pid_and_start_time`, `test_without_the_native_read_the_owner_proof_holds_for_its_half_hour`, `test_the_native_listener_read_finds_this_process_on_its_own_port` (real TCP table, own socket) |
| 4. No working self-heal and no alarm. | Two-step heal and the P1 (above). Quiet listening ticks neither count toward nor reset the streak. | `test_two_failed_captures_replace_the_tab...`, `test_a_third_failure_recreates_the_tab_through_the_browser_target_and_raises_the_p1`, `test_failures_after_the_third_retry_the_browser_step_every_five_minutes`, `test_login_redirects_stay_reauth_required`, `test_quiet_listening_neither_counts_nor_resets_a_failure_streak` |
| Acceptance replay, 23 Nov 13:54-14:03Z (states from the saved log) | Heal step 1 at 13:56:55.725Z (before 13:57Z), step 2 and P1 at 13:57:46.949Z, P1 cleared at the 14:03:51Z capture. | `test_replay_of_the_23_nov_failure_run_heals_before_1357` |
| 5. Ops Product, 24 Nov: the old runner ignored STOP for 150 s. | The waits (drain, probe retries) check STOP. A watchdog thread ends the process with `os._exit(0)` when STOP has been present for 15 s and the loop still runs. The feed writes are atomic replaces, and the OS releases the lock. | `test_stop_ends_a_runner_whose_call_blocks_mid_tick`, `test_a_stop_cuts_the_settle_wait_short`, `test_the_runner_gives_its_capture_the_stop_check` |
| Exactly-once | The same dedup keys as before; a post seen both by listening and by a reload is written once. | `test_the_page_own_fetches_...` (last lines); cc258 `test_minute_capture_appends_each_post_once...` |

The launch command of a relaunched ingestion Chrome now adds `--disable-background-timer-throttling`, `--disable-backgrounding-occluded-windows` and `--disable-renderer-backgrounding`, so the page's own polling keeps running while its window is hidden. Test: `test_a_relaunched_ingestion_chrome_keeps_its_page_timers_running_when_hidden`. This applies only after the next Chrome launch; the Chrome running now (PID 14200) keeps its flags.

Test runs: one pytest process at a time, on the branch head with 06fed062 merged.
- Feed files: `test_x_list_feed_cc785.py`, `test_x_list_feed_cc258.py`, `test_x_list_feed_hotfix_cc785.py` and `test_security_scans.py`, 43 passed.
- Covering files: `test_contentops_ingestion_bootstrap_v1`, `test_contentops_profile_continuity_lock_v1`, `test_daily_app_operator_trigger_v1`, `test_platform_rules_cc393`, `test_security_scans`, `test_x_reply_bot_entry_cc464`, `test_x_reply_pack_cc455` and `test_x_list_private_main_permission_v1`, 101 passed.
- Feed consumers: `test_heavy_news_quotes_cc467`, `test_heavy_news_quote_transport_cc467`, `test_x_reply_bot_cc464`, `test_x_reply_tabs_cc458`, `test_daily_trend_board_cc537`, `test_manual_desk_cc748` and `test_substack_daily_note_cc468`, 184 passed.
- Not run: the full suite.

The CC-595 tab tests in `test_x_list_feed_cc258.py` encoded the old rule (3 socket failures, 10-minute cooldown). They are replaced by the CC-785 tests above.

## Expected lag and request count (NOT VERIFIED on the live tab until the first market hour)

- **Baseline** (19-24 Nov log and the export): post-to-ingest median 51 s, p90 730 s, p99 8,868 s. Of 6,198 captures, 1,189 failed (19%).
- **If X's page polls the list by itself, or the `.` key loads new posts:** about 1-16 s from the list to the sidecar (the tick at most 15 s, plus 1 s), so a p90 near 15-20 s. No reload happens while timeline responses keep arriving. Requests: at most 4 timeline calls a minute (one per key press, only after 15 quiet seconds). Before the change, every minute brought one full page load with all its API calls.
- **If neither works:** one reload a minute, as before. Lag is then 0-60 s plus about 1-15 s of settle, a p90 of about 60 s. That is at the acceptance line, not safely under it. The key presses send no network request when they do nothing.
- **What the log measures:** each record's `capture` now has `refresh` (`reload` / `light` / null), `api_requests` (X API requests the tab sent during the tick, from `Network.requestWillBeSent`) and `light_refresh.hits/misses`. One market hour shows which case holds. If `misses` keep rising and `hits` stay at 0, the `.` key does nothing on the list page. The relaunch flags, or Ops' own choice, are then the next lever.

## The stale marker (`health` in `x_list_feed_v1.json`; CC-786 reads it)

| Field | Meaning |
|---|---|
| `state` | `OK`, `STALE` or `P1` |
| `stale` | true when the last good read is at least `stale_after_seconds` old (60 s in market hours, 180 s outside), or when 2 or more captures failed in a row |
| `stale_since_utc` | while stale: the last time a timeline response was read (the runner start if none); null when fresh |
| `last_good_capture_utc`, `last_good_age_seconds` | the latest timeline read; kept across runner restarts |
| `failure_streak`, `first_failure_utc`, `failure_cause` | failed captures in a row, when the run began, and the latest `STATE:DETAIL` |
| `last_heal` | the latest heal record (method, old and new target, adopted, closed ids) |
| `p1`, `last_p1` | the raised alarm (raised time, streak, cause, a plain sentence), and the last one with `cleared_utc` |
| `interval_seconds`, `market_hours`, `reading_rule` | the tick in force; the rule "STALE or P1 = data missing or stale (C7), never no news" |

`x_list_shock_flags_v1.json` keeps its list shape for CC-087, so a stale feed cannot be read from it. Readers take the feed's `health`.

## The P1 alarm path

**Finding:** ContentOps has no P1 path for runtime faults today. Its one incident store, the durable store's `incidents` table, holds publication dispatch outcomes. The only machine-level P1 that reaches Ops is the session-start hook's disk line (`C:\Users\bullw\.claude\hooks\cc_ops_state.py`, `disk_line`).

What this delivery writes:
1. `health.p1` in the export, which CC-786 makes Main read.
2. A log record with `"p1": {"event": "RAISED" | "CLEARED", ...}` in `runner_v1.log`.

To put it in front of Ops at each session start, Ops Product may add this to the hook. It is user-level and outside ContentOps, so I did not edit it:

```python
def x_feed_line():
    try:
        health = json.load(open(r"A:\Capital Chronicle\Runtime\ContentOps\x_list_feed\x_list_feed_v1.json", encoding="utf-8")).get("health") or {}
    except (OSError, ValueError):
        return "X-LIST FEED: export unreadable. "
    if health.get("p1"):
        return "P1 X-LIST FEED: " + health["p1"].get("plain", "") + " "
    return f"X-list feed stale since {health['stale_since_utc']}. " if health.get("stale") else ""
```

## Steps for Ops Product to go live

1. Integrate the branch head (the merge commit 071e7670 and this note's commit, after 06fed062). The live-step helper refuses a merge history, so squash it with `commit-tree` onto the live head as usual. Re-run the three feed test files there.
2. Restart the runner. Check the PID first: today PIDs 5692 and 19628, started 21 Nov; Ops restarted it at 01:00:51Z, so re-read the PIDs.
   - Create `A:\Capital Chronicle\Runtime\ContentOps\x_list_feed\STOP`. With the old code, wait up to 150 s, then confirm both `run_x_list_feed.py` processes are gone. If one remains, check its PID, start time and command line before ending it.
   - Delete STOP, then start the runner detached the usual way (WMI `Win32_Process.Create`), with the same command line: `"A:\Capital Chronicle\Runtime\ContentOps\v1-runtime\venv\Scripts\pythonw.exe" -B "A:\Capital Chronicle\ContentOps\scripts\run_x_list_feed.py"`.
3. Check within 2 minutes:
   - The log shows `refresh: "reload"` and `CAPTURED` on the first tick, then ticks every 15 s, and `health.state` is `OK` in the export.
   - The capture Chrome has exactly one list tab.
4. Check after one market hour: the lag p90 (`lag_seconds` of rows ingested after the restart), `light_refresh.hits/misses` and `api_requests` per minute.
5. Optional, Ops' call: restart the ingestion Chrome so the new background flags apply. Do it only with the book's news needs in mind; the sign-in stays in the profile.
6. **Rollback:** create STOP, restore the previous live tag (06fed062, `contentops-live-20261124T005718Z-integrate`) and start the runner again. The export's new `health` key is ignored by the old code, which reads only `capture.last_tab_replacement`.
