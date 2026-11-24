# Relaunch rehearsal, 24 Nov 2026 (Builder L, Ops Product)

Branch `backlog/relaunch-rehearsal-20261124`, cut from the live head `231d31d97d5a6d436d48b0974aaadf61d9a4efcb`.
Jim, 24 Nov 00:27Z: speed up, and test and audit each item, so that combined they run smoothly.

## Outcome

- **With the five fixes on this branch, the combined relaunch ran smoothly in the rehearsal.**
  - No flood: the first hour sends two dated results.
  - The first day adds two CC-603 follow-ups.
  - The 20 Nov USD/JPY result posts once, on every destination.
- **On the live head as it stands, the relaunch would have gone wrong in five ways.** All five are fixed and tested
  below:
  1. If the USD/JPY chart capture failed, the promised USD/JPY result would never have posted.
  2. An announced BTCUSD plan that ended during the pause would never have been shown to readers.
  3. None of the nine CC-603 follow-ups would ever have posted.
  4. The first daily wrap would have taken a scenario line as its title.
  5. The wrap would have led with a plan that expired a week earlier.
- **Not rehearsed:** the browser (Neo) side. Substack pages, the wrap's Substack article and LinkedIn need a live Neo
  endpoint. X and Notes stay with Jim by hand.

## How it was run (copies only)

- **Store:** a copy of `contentops_daily_app_v1.sqlite3`, made with the backup API from a `mode=ro` connection.
- **Main's export:** `plan-status.public.json` and `plan-transitions.public.json` as of 24 Nov 07:37Z. Each tick
  re-dated them to 30 seconds before that tick. No plans after 24 Nov exist in the rehearsal.
- **Bars:** a copy of `bars.sqlite3`.
- **Pause folder:** a fresh copy of `control/pause-20261123`, taken after Ops Product added `--relaunch`. Its
  manifest was pointed at the copied routes file and copied stop files.
- **The restore:** `restore_contentops.py --relaunch` ran on the copy at Mon 30 Nov 02:00Z. `schtasks` was stubbed;
  it would have enabled the three tasks and started the keepalive. It wrote `restored.json` with
  started_at 02:00:01Z.
- **Routes after the restore:** every route is open except x, substack_notes and linkedin_company
  (`JIM_POSTS_BY_HAND_20261123`) and youtube.
- **Each tick:** a fresh process ran the real entry points:
  - `scripts/plan_status_posts.py --publish`: plan posts, results, corrections, CC-603 follow-ups with CC-778,
    plan pages, the pinned scorecard, X reply drafts and the reply bot;
  - `live_contentops.market_wrap_job_v1 --publish`;
  - `scripts/manual_desk_tick.py`: the desk packs, with the TradingView idea pack;
  - `scripts/run_day_readback.py --sweep --stored-only`: the evening checks.
- **Sandbox:** an audit hook refused every socket, child process, browser and write outside scratch. Every send was
  answered by a recorder:
  - API destinations: `CanonicalDestinationTransportRuntimeV1.publish` and `readback` returned success with a fake
    object id;
  - the Telegram bot and the pinned scorecard: Bot API stubs, with a fake private chat;
  - Cloudinary: verification stubbed;
  - TradingView: a generated PNG, and every USDJPY capture fails, to test the fallback card.
  - A path shim copied each A: file the job read into scratch (read-only, 60 MB cap), so stored A: paths resolved to
    copies. Nothing was written to A:.
- **Fake clock:** 30 Nov 02:00, 02:01, 02:02, 02:31, 03:01, 03:02, 03:03 and 12:15 (the evening checks), then 13:05
  (wrap), 1 Dec 02:00, 02:01 and 03:05, and wraps on 1 and 2 Dec at 13:05.
- **Harness:** `C:\CapitalChronicleScratch\builder-l-tools\` (`rehearse.py`, `sandbox.py`, `redirect.py`,
  `run_seq.ps1`). Per-tick results stay in `C:\CapitalChronicleScratch\builder-l-data\run1\ticks\`.

## What each route would send, tick by tick (final branch head)

API sends count copies. Discord sends two per post: the post in the plan's thread, and a channel copy that links to
the thread. A Threads post is a root plus its replies, sent in one call.

| Tick (UTC) | Public sends | Other |
|---|---|---|
| 30 Nov 02:00 (restore, tick 1) | **USD/JPY result** and **BTCUSD plan ending**, each on Telegram 1, Discord 2, Facebook 1, Threads 1 (root + replies), Instagram 1. That is 12 API copies. X and Notes: DEFINITE_NO_WRITE (by hand). | Pinned scorecard: 1 edit (t.me/CapitalChronicle/134), read back. Desk: 2 packs, held 30 min for their page. 9 CC-603 follow-ups held (`CC778_BACKFILL_FIRST_HOUR_AFTER_RESTORE`). Wrap: `WRAP_WINDOW_ELAPSED_WITHOUT_PACKET` (29 Nov weekly). Reply bot: 0 drafts (749 targets older than 15 min). 2 Neo read-back requests (the two old X and Notes reads). |
| 02:01 (tick 2) | none | queued nothing new; 1 Neo read-back (the BTC plan's Substack page) |
| 02:02 | none | nothing |
| 02:31 | none | Jim's private chat: 2 posting packs released after 30 min without a page (23 messages with photos). |
| 03:01 (one hour later) | none | first follow-up's move chart captured (USOIL call of 9 Nov) |
| 03:02 | **CC-603 follow-up** (USOIL, 9 Nov): Telegram 1, Discord 1, Threads 1 (+1 reply) | |
| 03:03 | none | second capture (EURUSD call of 9 Nov) |
| 12:15 (evening checks) | **CC-603 follow-up** (EURUSD, 9 Nov): Telegram 1, Discord 1, Threads 1 (+1 reply) | Day read-back sweep: pause `PARTLY_PAUSED`, restored_at 02:00Z |
| 13:05 (daily wrap slot) | none in the rehearsal | Wrap staged and stopped at Neo's Substack identity check: `CANONICAL_NOT_CONFIRMED`, nothing dispatched. 7 follow-ups `BACKFILL_PACED`, next due 1 Dec 03:02Z. |
| 1 Dec 02:00 | none | 2 Neo read-backs (the same two reads on the new UTC day). Follow-ups still paced. |
| 1 Dec 02:01 | none | nothing |
| 1 Dec 03:05 | none (the third follow-up posts in the next minute) | US500 follow-up of 10 Nov waits (`CC778_CHART_MARKET_CLOSED_AT_RESOLUTION:SP:SPX`); next one (USOIL, 10 Nov) captured |

**Totals:**
- **First hour:** 2 public posts on each of Telegram, Facebook, Threads and Instagram, and 4 Discord messages (2 posts
  and 2 thread pointers). Nothing on X, Notes, LinkedIn, Substack or YouTube.
- **First day:** the same, plus 2 follow-ups on Telegram, Discord and Threads. The daily wrap goes too if Neo is up.

## No-flood checks

- **No stale setup or fill:**
  - The WAITING plan `plan_7c24bb53` (registered 23 Nov) posted nothing. Its page stays `CANONICAL_PENDING`
    (`PLAN_ANALYSIS_FINAL_STATUS_REQUIRED_AFTER_ENTRY_WINDOW`).
  - BTCUSD FILLED `plan_add6d622`: `FILL_CONFIRMATION_ALREADY_PUBLISHED_OR_PENDING`.
  - 11 fills: `POSITION_CLOSED_BEFORE_FILL_ANNOUNCEMENT`.
  - 30 plans: `PLAN_NEVER_ANNOUNCED`. These include the two plans registered during the pause (US500
    `plan_ec64af71`, USD/JPY `plan_fce3e094`).
  - The 23 Nov row `plan-status-post-e646d4dd` (PUBLISHING, older than 24 h) was settled with no send.
- **Results that ended inside the pause stay in the scorecard:** none of the scored ones went to the feed. On the
  live head, three results were held as `JIM_PAUSE_RESULT_SHOWN_IN_SCORECARD`, but none of the three is in the
  scorecard (defect 2):
  - two were never announced;
  - one is the announced BTCUSD plan that was invalidated (`plan_1d9bc560`).
  On the branch, the BTCUSD ending posts once and is dated by its result frame ("Bitcoin, plan of 22–23 Nov"). The
  other two are `PLAN_NEVER_ANNOUNCED`.
- **CC-603 backfill:** nothing in the first hour (all nine `BACKFILL_HELD` until 03:00:01Z). Then two a day, oldest
  call first: 03:02Z and 12:15Z, with the next due at 1 Dec 03:02Z.
- **Corrections:** none queued. `corrections_complete` was true and no correction row was created, so none can post
  twice.
- **Second tick:** queued nothing. The 02:01 tick and every later minute tick queued no plan row.

## The promised 20 Nov USD/JPY result (`plan_4bcfb1182f0fff4f8254172c`)

- **Main's score:** CLOSED/SCORED EXPIRED, result_r −0.0833, resolved 23 Nov 03:00:16Z.
- **Queued and sent:** queued at the first tick (it is in `PROMISED_RESULT_PLANS`) and sent once on every API
  destination. No later tick sent it again.
- **Heading and copy:** headed "USD/JPY, plan of 20–22 Nov", in the scenario voice, with no target line.
- **X and Notes:** refused before any write (routes kept for Jim). Jim's private desk received the pack at 02:31.
- **Image:** the USDJPY capture was set to fail, so every copy carries the plan fact card (16:9; Instagram 4:5).

**Telegram, Facebook, Instagram and the Discord thread post** (identical text):

```text
USD/JPY, plan of 20–22 Nov: closed at its time exit. Result: -0.1R.
Scenarios: Base case (55%): USD/JPY is below 159.114 at Mon 23 Nov, 1:00 AM ET, and a break of the 158.87-159.03 shelf runs toward lower levels.
Bull case (45%): USD/JPY holds the 159 handle on carry demand and returns toward 159.6 after Waller.
Base case driver: Risk-off repatriation, BoJ hike expectations and MoF warnings near 160 force carry bets on a rise out below the 17 Nov low 158.868.
What would undo the base case: An 15-minute close above 159.60 before entry.
Macro: Risk-off against the rate gap, signals are mixed.
Event and cause: Risk-off repatriation, BoJ hike expectations and MoF warnings near 160 force carry bets on a rise out below the 17 Nov low 158.868.
Priced in: Fed hike 100%.
Positioning and sentiment: Carry bets on a rise added 11-19 Nov.
Technical: Lower highs from 159.841, low 159.025, no close below 159.0.
Updated 22 Nov 22:00 ET.
Entry condition: price breaks through 158.88 (breakout).
Cancel if spot price closes above 159.6 before entry.
Entry opens Fri 20 Nov, 3:15 AM ET.
Entry can start until Fri 20 Nov, 3:45 PM ET.
Filled positions close by Mon 23 Nov, 1:00 AM ET.

Capital Chronicle offers analysis only, not financial advice or recommendations. Capital Chronicle may hold positions in the markets it covers.
```

**Discord channel copy** (the same text, then the thread link):

```text
Plan thread: <https://discord.com/channels/1519310996030750782/1573250800006725695>
```

**Threads** (root, then replies in one chain):

```text
USD/JPY, plan of 20–22 Nov: closed at its time exit. Result: -0.1R.
Scenarios: Base case (55%): USD/JPY is below 159.114 at Mon 23 Nov, 1:00 AM ET, and a break of the 158.87-159.03 shelf runs toward lower levels.
Bull case (45%): USD/JPY holds the 159 handle on carry demand and returns toward 159.6 after Waller.

Capital Chronicle offers analysis only, not financial advice or recommendations. Capital Chronicle may hold positions in the markets it covers.

[reply 1]
Base case driver: Risk-off repatriation, BoJ hike expectations and MoF warnings near 160 force carry bets on a rise out below the 17 Nov low 158.868.
What would undo the base case: An 15-minute close above 159.60 before entry.
Macro: Risk-off against the rate gap, signals are mixed.

[reply 2]
Event and cause: Risk-off repatriation, BoJ hike expectations and MoF warnings near 160 force carry bets on a rise out below the 17 Nov low 158.868.
Priced in: Fed hike 100%.
Positioning and sentiment: Carry bets on a rise added 11-19 Nov.
Technical: Lower highs from 159.841, low 159.025, no close below 159.0.
Updated 22 Nov 22:00 ET.

[reply 3]
Entry condition: price breaks through 158.88 (breakout).
Cancel if spot price closes above 159.6 before entry.
Entry opens Fri 20 Nov, 3:15 AM ET.
Entry can start until Fri 20 Nov, 3:45 PM ET.
Filled positions close by Mon 23 Nov, 1:00 AM ET.
```

**Notes on this text** (Main's wording, not changed here):
- "Priced in: Fed hike 100%." is the first clause of Main's field "Fed hike 100%; BoJ 58% held (19 Nov), higher per
  an unconfirmed digest." In this rehearsal Antigravity was refused, so the deterministic layer copy was used. Live,
  Antigravity writes these lines.
- "An 15-minute close" is Main's typo.

## Chart fallback examples

**Plan post** (the USD/JPY result above; both captures failed): every destination carries
`plan-fact-card-bad628af0fa9b508eb98` (16:9; Instagram 4:5). Its title is "USD/JPY: plan result — expired"
and its facts are:

```text
Instrument: USD/JPY
Prices: Plan-price levels
Result: expired
Entry zone: 158.8–158.88
Invalidation: Above 159.6
Status: Scored
As of: Sun 22 Nov, 22:00 ET
```

It shows no target. It is bound to the failure with `plan_chart_fallback`, cause
`TRADINGVIEW_SNAPSHOT_WORKER_FAILED:SimulatedFailure`.

**Article** (CC-777): the stored article "Tanker strikes, US strikes on Iran and a softer word from Trump: what markets carry into Monday and a CPI week" (`outbox_255f4904f75a440fa44aa3ad2753e4b2`, market USOIL) was run
through `prepare_contract_article`, with both capture attempts failing.
- It leads with its own data card `post-facts-94430843735feda9f950` (`source_bound_data_card`, `post_key_facts`).
- The card is bound by `article_chart_fallback` with the same cause. There is no text-only fallback.
- Its first facts are the article's own lines (see observation O5).

**Page:** no plan page published in the rehearsal (Neo down). The page path is covered by Builder E's
`test_prerelaunch_chart_fallback_20261123.py`.

## Defects

All five are fixed on this branch, each with a test in `tests/test_relaunch_rehearsal_20261124.py`.

1. **The promised USD/JPY result never posts if its chart capture fails** (`9422cffc`).
   - Cause: `plan_facts` read `row["scored_call_count"]`, which card-format (format 4) result rows never carry. The
     fallback card raised KeyError, and the post stayed NOT_STARTED on every tick. This was seen on the live head at
     the first tick.
   - Fix: the count line appears only when the row has one.
   - Tests: 3 new; 411 tests in the 18 files that cover the fact-card path pass.
2. **An announced plan that ended inside the pause was shown nowhere** (`2e6e8cc6`).
   - The pause rule skipped every result inside the window "as shown in the scorecard". But the scorecard lists only
     scored results and unscored expiries.
   - Example: BTCUSD `plan_1d9bc560` was posted on 23 Nov 03:55Z (Telegram 231, Discord, Facebook, Threads,
     Instagram) and invalidated at 05:43Z. Its ending was dropped.
   - Fix: hold back only results whose plan the scorecard lists. Everything else takes the normal path: an announced
     card gets its one dated ending, and an unannounced plan stays `PLAN_NEVER_ANNOUNCED`.
   - Tests: 2 new; 811 tests in the 31 files that cover the card queue and the pause pass.
3. **No CC-603 follow-up would ever post after the relaunch** (`a145ac86`).
   - Each prepared follow-up froze the pinned record line it was prepared with. The relaunch's first scorecard update
     changed the counts, and `validate_intent` refused every follow-up with `CC603_PUBLIC_RECORD_CHANGED_BEFORE_WRITE`
     on every later run. In the rehearsal, from 03:02 onward, it was all day.
   - Fix: `refresh_record` replaces the row's record and its one record line before any destination copy exists,
     through `finalize_outbox_payload_before_dispatch`. Copies already made stay frozen, and the write check is
     unchanged.
   - Tests: 2 new; 316 tests in the follow-up files pass. Follow-up text as posted at 03:02:

```text
Original, 09 Nov 2026 04:13 ET: “If price trades into 90.2–90.45, the desk is bearish on US crude oil (WTI) over the period to Wed 11 Nov, 07:00 ET. Invalidated if price moves above 91.6.”
By the 09 Nov 06:15 ET price bar, price reached 87. Our entry zone never traded; this was a directional view, with no trade.
The price check uses the original plan's prices; the TradingView chart shows the move in its own market feed.
Original: https://t.me/CapitalChronicle/100
Pinned call record: 2 hits, 7 stopped, 58 expiries; 67 results, 17 scored.
Record: https://t.me/CapitalChronicle/134

Chart: TradingView

Capital Chronicle offers analysis only, not financial advice or recommendations. Capital Chronicle may hold positions in the markets it covers.
```

4. **The daily wrap's title became a scenario line** (`60a1f5d2`).
   - The scenario loop added on 23 Nov (`082394d0`) reused the variable `heading`. The 30 Nov edition was titled
     "Bull case (45%): USD/JPY returns to 159.5-159.8 as the equity rebound extends. — November 30, 2026".
   - Fix: the loop has its own variable. The 1 Dec rehearsal edition is titled "Pre-US Market Wrap — December 1,
     2026".
   - Tests: 2 new; 74 wrap tests pass.
5. **The wrap's scenarios came from the newest plan of any status** (`3b8fd194`).
   - The 1 Dec edition led its Scenarios section with the USD/JPY plan that expired on 23 Nov ("below 158.965 at Thu
     26 Nov").
   - Fix: the scenario comes from the newest plan that the wrap itself lists as open. The 2 Dec rehearsal edition
     used the open gold plan.
   - Tests: 1 new; 75 wrap tests pass.

## Observations (not changed)

- **O1 (content, Main):** the two notes on the USD/JPY text above: Main's clipped "Fed hike 100%" field and the "An
  15-minute" typo. Check the live Antigravity lines at the relaunch.
- **O2 (wording):** the BTCUSD ending says "price did not reach the entry zone". Main ended it INVALIDATED (its
  cancel level traded before entry), so the line is accurate but does not name the cause.
- **O3 (by design):** the US500 follow-up of 10 Nov (`9b071613`) waits indefinitely: its move resolved outside the
  S&P 500 cash session (`CC778_CHART_MARKET_CLOSED_AT_RESOLUTION`). It holds no pacing slot.
- **O4 (partial post):** `refresh_record` works only before the first copy. If the record changed between one
  follow-up's destinations, the rest would still refuse. This is unlikely, because the API destinations go in one
  call.
- **O5 (old cards):** the 9 Nov article's data card carries Markdown `**` and a section heading as facts. A CC-777
  fallback would lead with that card.
- **O6 (evening checks):** expect these flags on relaunch day. Several are rehearsal artefacts (no public HTTP,
  stored-only sweep):
  - CC-672 `PLAN_COPY_OVER_TEN_MINUTES_LATE` for the two dated results;
  - decision 113 `CONFIRMED_FULL_ANALYSIS_PAGE_UNAVAILABLE`;
  - CC-684 `LINKEDIN_ACCOUNT_COPY_MISSING` ×2;
  - decision 82 `POSTED_CHART_READBACK_UNAVAILABLE` (UNVERIFIED).
- **O7 (Neo):** the wrap posts Substack first through Neo. If Neo is not up at 13:00Z, that day has no wrap
  (`CANONICAL_NOT_CONFIRMED`, nothing dispatched).

## Read-backs (CC-683 and CC-774)

- **Two old stored reads,** `plan-status-post-f5c31cea` (X) and `plan-status-post-7e284f36` (Notes): one read-back
  request and one end row each on 30 Nov 02:00, then none until the new UTC day (1 Dec 02:00, one each).
- **The BTCUSD plan page (Substack):** one at 02:01, then none.
- **Every other tick wrote no read-back request.** All reads stayed within two a day per read and repeated nothing
  within the day.

## Not covered by this rehearsal

- **Neo browser routes** (the endpoint was refused): Substack pages, the wrap's Substack article, LinkedIn, and the
  X and Notes read-backs beyond their end rows.
- **Model calls** (Antigravity, Codex) were refused, so the layer copy and the wrap ran on their deterministic
  fallbacks.
- **Main's export reader child** was replaced by a direct JSON read with the same contract check.
- **Provider and Cloudinary responses** were faked as success. The TradingView PNGs were blank, so price-scale
  checks ran as not compared.
- **No new Main plans after 24 Nov** exist in the copy.

## For Ops Product's real relaunch read-back

1. Merge these five fixes before the restore, or expect defects 1 to 5. Defect 3 alone keeps all nine CC-603
   follow-ups off for good.
2. Run `restore_contentops.py --relaunch` and confirm `restored.json` exists. The first minute should queue only the
   USD/JPY result and the BTCUSD ending: `plan_status_post_runs/runs-YYYYMMDD.jsonl`, phase PLAN_EXPORT_QUEUE.
3. Read the USD/JPY result back once on Telegram, Discord (thread and channel), Facebook, Threads (root and three
   replies) and Instagram. Check the heading "USD/JPY, plan of 20–22 Nov", no target, and the chart or fact card.
4. Confirm that the pinned record (t.me/CapitalChronicle/134) was edited once and still reads back.
5. Check that no CC-603 follow-up appears before restore + 1 h. Then check one at about +62 min, and none after the
   second until 24 h after the first.
6. At +30 min, check that Jim's private chat received the two posting packs and nothing older.
7. Check the 13:00Z daily wrap: title "Pre-US Market Wrap — <date>", scenarios from an open plan, Substack through
   Neo.
8. Count `internal:native-neo-tool` READBACK rows per read and UTC day. Expect at most two per read; none repeat
   within the day.
