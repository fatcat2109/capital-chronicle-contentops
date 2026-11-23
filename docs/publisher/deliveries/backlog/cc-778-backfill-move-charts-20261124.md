# Delivery: backlog/cc-603-backfill-move-charts-20261124 (Builder K, CC-778, 24 Nov 2026)

Goal: the nine `CC603_PREPARED` follow-ups (Jim's 14 Nov "called it" request, CC-603) get a TradingView
chart of their own move by code, then post at most two a day, oldest call first, never inside Jim's pause
or the hour after it. Nothing was posted, sent or captured from the real TradingView site; no browser,
scheduled task, lane runner or file under `A:\Capital Chronicle\Runtime` was touched. The store was read
read-only (`mode=ro`).

- Branch: `backlog/cc-603-backfill-move-charts-20261124`
- Base: c868f0fe (the ContentOps live head)
- Code commit: e5ccec7d (this note follows it)
- Files:
  - `live_contentops/call_followups_v1.py` (request, capture, binding, pacing, minute-run wiring)
  - `live_contentops/tradingview_snapshot_v1.py` (historical window in `capture` and its worker)
  - `live_contentops/tradingview_plan_overlay_v1.py` (6 lines: `source_binding` reads a follow-up's
    zone and invalidation from its stored row, so the write boundary's redraw check matches)
  - `tests/test_call_followup_move_charts_cc778.py` (new)
  - `docs/publisher/CC-778/nine-capture-requests.json` (evidence from the live store, read-only)

## What the code now does

1. **Capture request.** `move_chart_request(row)` gives each follow-up its market (the reviewed
   TradingView symbol of `SYMBOLS`), a 15-minute interval (longer moves get 1h, 4h or daily), and a window:
   - it starts at least 1 hour before the call's bar, earlier when needed to show at least 12 hours;
   - it ends on the close of the bar that resolved the move (`visible_to_utc` = the resolution time);
   - so `held_chart`'s check `visible_from <= call published < resolved <= visible_to` holds.
   - The levels to draw are the call's entry zone and invalidation. The resolution level (a target) is
     never part of the request (decisions 40 and 157).
2. **Capture.** `capture_move_chart` calls the existing `tradingview_snapshot_v1.capture` with a new
   `visible_range` argument. The worker (same guest chart, same throwaway profile) sets the window with the
   chart page's own API (`TradingViewApi.activeChart().setVisibleRange`), hides the live last-price line and
   label where the page allows it, rests the cursor on the window's last bar and reads that bar's close from
   the legend. The parent refuses the download unless the read-back window starts at or before the call's bar
   and ends on the resolution bar with no later bar (`TRADINGVIEW_VISIBLE_RANGE_NOT_CONFIRMED`).
3. **Checks before binding.** The usual symbol, interval, PNG and size checks; then the price scale
   against the held plan-feed close of the 15-minute bar ending at the window's close (the BTC follow-up's
   `VISIBLE_WINDOW_CLOSE` check, 0.15% limit, 0.40% for WTI and Bitcoin). When either close is missing the
   chart is still bound with `NOT_COMPARED` and its cause, as for plan posts; WTI then draws no level.
4. **Levels.** When the capture's axis geometry passes CC-459's pixel checks, the existing overlay draws
   "Entry low", "Entry high" and "Invalidation" (edge markers when off the visible range). Otherwise the
   plain chart is bound and the cause is kept in the binding's `review.levels_cause`.
5. **Binding and release.** A passing capture writes `daily_app_outputs/call-followups/<key>/reviewed_chart.json`
   (the BTC shape: `asset`, `visible_from_utc`, `visible_to_utc`, plus `review` with every automatic check).
   The next minute run's `held_chart` takes it and the follow-up posts with its CC-603 dated copy unchanged.
   Follow-ups that go to Instagram also get a native 4:5 chart of the same window (`reviewed_portrait.json`)
   before their first post, because Instagram refused the BTC follow-up's 16:9 chart on 16 Nov.
6. **Failure.** Each attempt's cause is saved in `move_chart_capture_v1.json` beside the follow-up
   (an attempt cut off by the job's limit is named `TRADINGVIEW_CAPTURE_INTERRUPTED`). Two attempts make a
   round; a failed round waits 6 hours. The follow-up stays `CC603_PREPARED` and never posts text only
   (decision 82). A failed follow-up does not block the next one in line.
7. **Pacing.** In the existing minute run (`minute_due` -> `run_due`), before any capture or post:
   - Jim's pause holds everything: from 23 Nov 04:50Z until `control/pause-20261123/restored.json` exists
     (`plan_call_cards_v1.jim_pause_window`), then for one more hour (`CC778_BACKFILL_PAUSED`,
     `CC778_BACKFILL_FIRST_HOUR_AFTER_RESTORE`).
   - A follow-up already started (any dispatch) finishes first.
   - New ones start oldest call first, and only while fewer than two follow-ups started in the last 24
     hours (`CC778_BACKFILL_TWO_A_DAY`, with `next_due_utc`). Two in any 24 hours means at most two on any day.
   - At most one capture attempt per minute run.

## The nine (read from the live store, 24 Nov; full detail in `docs/publisher/CC-778/nine-capture-requests.json`)

All on 15-minute bars; times UTC; window = from -> to (to = the resolution bar's close).

| Order | Key | Market (chart) | Call | Window | Levels drawn | 4:5 too |
|---|---|---|---|---|---|---|
| 1 | 35a55222 | WTI (NYMEX:CL1!) | 9 Nov 09:13 | 8 Nov 23:30 -> 9 Nov 11:30 | zone 90.20-90.45, invalidation 91.60 (shifted by the measured chart-vs-plan offset) | no |
| 2 | af988bdf | EUR/USD (FX_IDC:EURUSD) | 9 Nov 09:18 | 9 Nov 08:15 -> 20:30 | zone 1.1166-1.1170, invalidation 1.1144 | no |
| 3 | 9b071613 | S&P 500 (SP:SPX) | 10 Nov 03:17 | 9 Nov 18:30 -> 10 Nov 06:30 | **waits:** `CC778_CHART_MARKET_CLOSED_AT_RESOLUTION:SP:SPX` | no |
| 4 | bb2dc2d3 | WTI (NYMEX:CL1!) | 10 Nov 03:17 | 9 Nov 18:45 -> 10 Nov 06:45 | zone 85.95-86.05, invalidation 86.80 (offset as above) | no |
| 5 | 2659ec1c | EUR/USD | 11 Nov 03:27 | 11 Nov 01:30 -> 13:30 | zone 1.1225-1.1245, invalidation 1.1282 | yes |
| 6 | f49e1e04 | Gold (FX_IDC:XAUUSD) | 11 Nov 06:34 | 11 Nov 04:45 -> 16:45 | zone 4,068-4,078, invalidation 4,110 | yes |
| 7 | 6cb9230a | USD/JPY (FX_IDC:USDJPY) | 11 Nov 06:34 | 11 Nov 01:45 -> 13:45 | zone 158.35-158.45, invalidation 157.80 | yes |
| 8 | f260f6f4 | EUR/USD | 11 Nov 06:35 | 11 Nov 01:15 -> 13:15 | zone 1.1192-1.1202, invalidation 1.1232 | yes |
| 9 | 813c70c1 | Gold | 11 Nov 16:26 | 11 Nov 07:30 -> 19:30 | zone 4,048-4,052, invalidation 4,090 | no |

- Every window passes `held_chart`'s check, and the held plan-feed close at each window's end exists in
  `bars.sqlite3` (read-only), so each scale check has its quote.
- Levels are drawn only when the capture's axis passes CC-459's checks; a level off the visible range gets
  an edge marker. No target is drawn.
- The S&P 500 call resolved at 01:30 ET, when the cash index (the reviewed chart, decision 107) has no bars.
  It waits with that cause instead of posting an empty chart. A futures chart (CME_MINI:ES1!) would show the
  move; it is not in the reviewed symbol map or the scale limits, so it was not added here.
- With the restore at time R: the first two post from R+1h (WTI 9 Nov, EUR/USD 9 Nov), then two a day;
  the eight that can post take four days.

## Tests

Command (one process each): `python -B -m pytest -q -p no:cacheprovider -rfE --basetemp=C:\CapitalChronicleScratch\builder-k-tmp <files>`
on the 43 test files that import `call_followups_v1` or `tradingview_snapshot_v1` (every overlay test is among them),
plus the new file on the branch.

- Live head c868f0fe (detached copy `C:\CapitalChronicleScratch\builder-k-base`): **1093 passed, 3 skipped, 0 failed** (13 min 45 s).
- This branch: **1113 passed, 3 skipped, 0 failed** (13 min 51 s). The 20 more are the new file. Failing ids: none on either, so equal.

New tests (`tests/test_call_followup_move_charts_cc778.py`, fake snapshot worker returning the retained
CC-603 gold download, no live service):
- each of the nine gets a capture request with its market, 15-minute interval and a window that passes
  `held_chart`'s check and ends on the resolution bar; the S&P 500 one waits with its cause (9 cases);
- a fake capture binds the window, the scale check (`VISIBLE_WINDOW_CLOSE`, 0% difference) and the three drawn
  levels (no target), then releases the follow-up, which posts with that image and its dated copy and ends PUBLISHED;
- a failed capture (page API absent, wrong window, wrong price scale) keeps the follow-up waiting with its cause,
  spends two attempts, waits 6 hours, then tries again; nothing posts (3 cases);
- an interrupted attempt is named before the next; a closed cash market spends no capture;
- pacing: oldest call first, a started one finishes first, a third start waits for the 24-hour slot;
- the pause and the first hour after the restore hold everything, in `backfill_hold` and through `run_due`;
- two follow-ups started in the last day hold the next one through the minute run;
- an Instagram follow-up tries its native 4:5 chart before posting, and a failed portrait never holds the others.

## What is left

- **The first real capture runs after the relaunch, and Ops Product reads it back.** The worker's new steps
  (the chart page's `TradingViewApi`, `setVisibleRange`/`getVisibleRange`, the legend's close, the
  last-price overrides) were written against TradingView's page without a live run, as the brief forbids one.
  If the page lacks the API, every capture fails with `TRADINGVIEW_CHART_API_ABSENT` and the follow-ups keep
  waiting; nothing posts without a chart. Read back: the first `reviewed_chart.json`, its image (window,
  no later candles, no live price label: `review.live_values_hidden`), and `move_chart_capture_v1.json`.
- **S&P 500 follow-up 9b071613** waits until someone decides on a futures chart for out-of-hours US500
  moves, or settles it as not posted.
- Instagram: the main plan still lists Instagram, so its 16:9 copy is refused locally
  (`INSTAGRAM_NATIVE_4X5_CHART_REQUIRED`, as on 16 Nov) before the bound 4:5 portrait posts. Unchanged
  behaviour, kept on purpose.
