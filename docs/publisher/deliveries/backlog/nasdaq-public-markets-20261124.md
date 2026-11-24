# CC-788: the Nasdaq 100 as the seventh core market in every ContentOps output

Builder N for Ops Product, 24 Nov 2026. Branch `backlog/nasdaq-public-markets-20261124`: code `f8188fed`, cut from the live
ContentOps head `06fed062` and merged with the moved live head `51284715` (Builder M's X-list files only; no overlap). Jim, 24 Nov 2026, before 01:04:50Z: «Ngoài ra hãy thêm nasdaq vào danh sách các tài
sản được Capital Chronicle Main cover.» Ops Live owns the Main side; this delivery is ContentOps only. Nothing was
posted, no browser was opened, and no store, task, runner or file under `A:\Capital Chronicle\Runtime` was
written. Stores were read read-only.

Also in this delivery (Ops Product's addition of 24 Nov): CME FedWatch odds stay in words in public copy, like
Kalshi's and Polymarket's (section 7).

## 1. Symbol, name and precision

| Field | Choice | Source |
| --- | --- | --- |
| Main asset id | `USTEC` | Exness symbol; Main's candidate is `cand_macro_ustec` (Main `data/research/record/plan-outcomes.csv`) |
| Public name | "Nasdaq 100" ("the Nasdaq 100" in running copy) | decision 107; `plan_status_posts_v1.BROKER_NAMES` already said "the Nasdaq 100" |
| TradingView chart | `NASDAQ:NDX` (cash index) | follows US500's `SP:SPX`. The desk's reviewed map (Main commit `083f35ad0`, `reviewed-tradingview-symbols.json`) lists `OANDA:NAS100USD`, a CFD feed, which decision 107 rules out for ContentOps exactly as it ruled out `OANDA:SPX500USD` for the S&P 500 |
| Overnight rule (CC-778) | the S&P 500's: cash bars 09:30-16:00 ET; outside them the chart compares at the last 16:00 ET close | `call_followups_v1.CASH_SESSIONS`, `publication_image_contract_v1.comparison_clock` (now `CASH_INDEX_MARKETS`) |
| Digits / tick | 2 digits, tick 0.01 index points | Main `docs/research/database_foundation/exness_cfd_launch_scope_v1/EXNESS_CATALOG_METADATA_REFRESH_20260918.json` (USTEC `digits: 2`, "US Tech 100 Index"); Main `data/research/cc-579/cc037-costs.json` (USTEC `tick_size: 0.01`, known 26 Oct 2026) |
| Public quote | cash `^NDX` (Yahoo) for maps and chart checks; `NQ=F` for the wrap's futures moves | the S&P 500 pattern (`^GSPC` / `ES=F`) |
| Price-difference limit | 0.15%, the S&P 500's equity-index starting value | CC-463; no simultaneous USTEC/NDX pair is held to calibrate it |
| Futures/ETF names (decision 107) | NQ or MNQ futures, QQQ | `public_instruments_v1` |

## 2. Module decisions

| Module | Decision | Reason |
| --- | --- | --- |
| `plan_status_posts_v1` | MARKETS and TITLES gain USTEC | the core list every plan post, card, scorecard, follow-up and weekly record reads |
| `plan_analysis_pages_v1` | owner candidate `USTEC` -> `cand_macro_ustec` | analysis pages find Main's own candidate |
| `plan_call_card_media_v1`, `plan_call_cards_v1`, `plan_reader_copy_v1`, `weekly_scored_calls_v1`, `capital_chronicle_desk_record_source_v1` | no change | they read `posts.MARKETS` / `posts.TITLES` / `tv.SYMBOLS` |
| `daily_trend_board_v1` | MARKETS and PRICE_PLACES (2) gain USTEC, for boards captured from 26 Nov 2026 (ET). A board with no Nasdaq row shows "Nasdaq 100 unavailable"; a partial row stops the board like any market's | dated so issued boards keep their bytes (`validate_link` re-projects them); unavailable rather than a guess |
| `pinned_result_scorecard_v1` | PLAN_TICKS USTEC 0.01 | Main's tick when a plan lacks `target_tick_size` |
| `image_template_inputs_v1` | MARKETS/ORDER gain USTEC; `SIX_ORDER` for earlier maps; a seven-row map may show the Nasdaq 100 unavailable; a missing Nasdaq implication never breaks an event image | the map is a core-market output; one gap must not remove it for the six |
| `image_templates_v1` | seven-row map layout (tighter line gaps), "Unavailable" row, alt text "Seven markets"; six-row maps keep the exact offsets | checked: a six-row table renders identical pixels and text boxes with the live head's code and this branch's (W and T) |
| `image_quality_v1` | no change | `template_acceptance` reads ORDER, so it now asks for 14 reviewed PNGs |
| `market_wrap_sources_v1` | MARKETS gains USTEC (`USTEC_FUTURES`, aliases ustec/ndx/nasdaq/nas100); the cash-close quote rule covers USTEC | wrap rows, Main outlooks (`cand_macro_ustec`) and the map |
| `market_wrap_editorial_v1` | `title_market` "Nasdaq 100 E-mini futures (NQ)"; map rows; moves card spacing `732 // len(MARKETS)` (122 px for six, unchanged) | wraps are frozen by bytes, so earlier packets are untouched |
| `event_reaction_source_v1`, `cpi_reaction_page_v1` | MARKETS and LABELS gain USTEC | held CC-441 rows show; absent rows are skipped, never inferred |
| `article_scenarios_v1` | MARKETS = six + USTEC; a scenario set carries the six, or the six plus USTEC when Main's report gives a Nasdaq implication | a report without one keeps a missing row, never an invented implication; stored articles stay valid |
| `reader_article_contract_v1` | daily-note table needs a Nasdaq row when the data cutoff is from 26 Nov 2026 00:00Z | earlier contracts replay unchanged |
| `main_report_projection_source_v1` | the pre-US wrap quote set needs the six, accepts USTEC; USTEC quote age like US500 | a missing Nasdaq quote is a missing row |
| `tradingview_snapshot_v1` | SYMBOLS/NAMES gain `NASDAQ:NDX` "Nasdaq 100 index" | section 1 |
| `tradingview_plan_overlay_v1` | VERIFIED_MARKETS stays at six for now | CC-459 admits a market only with two real guest captures in `docs/publisher/CC-459/six-market-scale-proof.json`; none exists for NDX (no browser in this build). Until then a Nasdaq chart is posted without drawn levels; the levels stay in the text. The CC-459 proof test now runs over VERIFIED_MARKETS, so adding the captures and the one id is the whole step |
| `tradingview_idea_v1` | MARKETS gains USTEC, aliases NDX/NAS100; `USTEC` joins the allowed codes like US500 | without it every Main sentence naming USTEC was cut and the pack was withheld (seen in a smoke run) |
| `publication_image_contract_v1` | MAX_DIFFERENCE_PCT USTEC .15; cash-index clock | section 1 |
| `chart_price_reference_v1` | no change | market-generic; reads USTEC's held M1 history and the public `^NDX` quote |
| `public_instruments_v1` | INSTRUMENTS, MARKET_PATTERNS, guidance and the forbidden-code list gain USTEC | decision 107 |
| `public_market_quote_v1` | `USTEC` (^NDX) and `USTEC_FUTURES` (NQ=F); the old `NDX` id becomes an alias of `USTEC`; frozen `NDX` observations stay valid | one provider symbol keeps one cache file; two ids would refuse each other's observations |
| `x_reply_fact_sources_v1` | LABELS, PLACES (2), the native-bar market set and the public fact id (USTEC -> NDX) | reply facts can now use USTEC's plan quote and M1 bars before a public quote |
| `x_reply_fact_policy_v1` | the NDX pattern also matches USTEC, NAS100, US100 | |
| `x_reply_tabs_v1` | topic pattern for USTEC calls | |
| `x_reply_base_rates_v1`, `x_reply_topics_v1` | no change | they already cover the Nasdaq 100 under the reply id NDX |
| `v1_simple_gemini_newsroom_v1` | the writer may set `market_asset` USTEC | the snapshot path then uses `NASDAQ:NDX` |
| `vietnamese_gold_note_v1` | left alone | a gold-only note for Jim's separate community brand |
| `contentops_foundation_library_v1` | no change | USTEC was already an index asset |
| `public_decision_checks_v1` (CC-690) | no change | it reads `tv.SYMBOLS`, so a Nasdaq post's chart is now checked (it was UNMAPPED) |
| `manual_desk_v1`, `scenario_voice_v1` | no change | no market list |
| `event_article_guard_v1` | FedWatch rule only (section 7) | |

## 3. Data gaps

| Gap | Effect now | Owner |
| --- | --- | --- |
| USTEC has no rows in the completed-bars `bars` table (`...\completed-bars\bars.sqlite3`, read with `mode=ro` at about 01:20Z: six symbols to 23 Nov 05:00Z). It does have `history_sources` (D1: 8, M1: 342) | call follow-ups (CC-603) cannot prove a Nasdaq move and stay ineligible with their cause; reply facts and chart checks use the M1 history | Codex Data: capture USTEC M15 native bars like the six |
| Main's desk board (`desk-board.public.json`) has no USTEC row yet | from 26 Nov the board and the map print "Nasdaq 100 unavailable" | Ops Live (Main board) |
| No held D1 archive for `NQ=F` under the wrap's market-history folder | the wrap makes one bounded public request, or reports the gap for that row | Codex Data |
| Main scenario sets name six markets | articles keep six until Main writes a Nasdaq implication | Ops Live |
| No simultaneous USTEC/NDX price pair | the 0.15% chart limit is the S&P 500's starting value | Ops Product, after the first live captures |

## 4. Tests

New: `tests/test_nasdaq_core_market_cc788.py` (core tables, names, chart, precision, cash clock, quote alias,
reply facts, trend board with seven rows / unavailable / partial / dated, the registered board's fact card,
TradingView idea pack, daily checks, morning maps W and T with seven, unavailable and six rows, wrap map,
daily-note table, instruments rule, scenarios, event reactions); `tests/test_nasdaq_plan_posts_cc788.py`
(setup, fill and result through the real queue and every destination payload, compared line for line with an
S&P 500 plan of the same levels; no target, no `USTEC`, notices once, grouped and dated); a CC-691 golden test
for a Nasdaq plan reply; `tests/test_fedwatch_odds_in_words_20261124.py` and one projection case.

Run on this branch (covering files of every changed module, 171 files, one process at a time):
- First full pass: 4,150 passed, 4 skipped, 14 failed. Every failure was a test pinned to the old rule, none a
  defect: six-market counts (trend board of 16 Nov, the wrap table, the TradingView symbol map, the cash-close
  clock for USTEC), a weekly-scorecard fixture built from ORDER (seven calls now make three pages of three; the
  fixture keeps six), the reply supplement now reading Main's `USTEC` price before a public quote, the CC-459
  proof test parametrised over all chart symbols (now over VERIFIED_MARKETS), and CC-584's FedWatch example
  (section 7). Those tests were updated with the reason in a comment.
- Rerun of those 15 files plus every overlay user: 433 passed.
- The live head passes the full suite, so these were the only new failing ids.
- Six-row morning-map table: identical pixels and text boxes from the live head's code and this branch's
  (W and T masters), checked with `python -I -B` against `A:\Capital Chronicle\ContentOps` read-only.

## 5. What is left

- No `NASDAQ:NDX` guest capture was taken (no browser in this build). Two real captures (16:9 and 4:5) added to
  CC-459's proof, plus `USTEC` in `tradingview_plan_overlay_v1.VERIFIED_MARKETS`, turn on drawn levels for
  Nasdaq charts; until then they go out without drawn levels. Owner: Ops Product (relaunch rehearsal).
- The image template's acceptance now asks for 14 reviewed PNGs (seven markets, two masters).
- The dated starts (boards from 26 Nov ET, daily-note tables from 26 Nov 00:00Z) assume this goes live before
  then; Ops Product may move them.
- Main's side (analysis, plans, plan-status export, desk board) is Ops Live's.

## 6. Stored items

Issued boards, wraps, images and posts keep their bytes: boards and daily-note contracts are dated, wraps and
images are checked by frozen bytes, a six-row map re-renders identically, and the scenario rule still accepts
six-market sets.

## 7. CME FedWatch odds stay in words

`event_article_guard_v1.FEDWATCH_PATTERN` ("FedWatch", "CME FedWatch", and rate/hike/cut/hold probability
phrases) joins the Kalshi and Polymarket patterns in `plan_status_posts_v1.PRIVATE_RATIONALE` (the sentence is
dropped), `plan_analysis_pages_v1._PREDICTION` (a number with FedWatch provenance is refused),
`event_article_guard_v1` (a number beside the name is refused: `ODDS_SOURCE`), `market_wrap_sources_v1.safe_prose`
(the line is left out) and `main_report_projection_source_v1` (a span with a number beside it is refused). Words
such as "Rate futures lean toward a December hold." stay allowed. Reason: CME's Data Terms of Use allow website
data for personal, non-commercial use only; passing it on needs CME's written consent, redistribution a licence
(decision 44). Tests: `tests/test_fedwatch_odds_in_words_20261124.py` and the FedWatch case in
`tests/test_main_report_projection_source_v1.py`.

This reverses one earlier rule: CC-584's tests used "CME FedWatch prices a 55% chance of a rate increase" as the
example of a usable, named pricing fact on plan pages. That sentence is now refused; the two CC-584 tests use
"Fed funds futures" as the named source instead, and one asserts the FedWatch version is refused. A Main plan
whose priced-in paragraph quotes a FedWatch number will have that paragraph refused on its analysis page, so the
writer must put it in words.
