# CC-521: independent odds-table audit

The source-reconciled independent calculator reproduces all 54 original market rows, all nine pooled rows and all 22 construction rows exactly. The original README alone did not define an exact replication; that failure was frozen before source review. The corrected census now matches the independent calculator as well.

Five of 54 corrected market rows read PAID_BOTH_HALVES. A shared 60-calendar-day block null produces 0.978 such rows on average (95% range 0 to 3), but none of the eight named tests survives the 54-row familywise comparison at 5%. The first-five-year selector chooses three Bitcoin rows; two have positive later means, pooled +0.100R over 362 dependent later trades, and none has a later nominal t of 2. These are useful base rates with asset drift and path limits, not calibrated probabilities or prospective proof.

## Scope and identity

- Item: CC-521 only; Codex Data builds, Ops Live integrates. No model subprocess, broker operation, schedule change, live-root write or other-chat message. The analysis-input boundary is Jim decisions 125 and 128; the existing pack reader uses the rebuilt output.
- Base: `6c36f29eacda8704f2d0b7add6657c122be00b48`, the deployed Main head at admission. Remote default `main` was `a1c685983bf26dd0585d1c9e18c065ec865de416` and lacked this deployed odds implementation, so the deployed base was used.
- Author process launch readback: `--model gpt-6.1-sol`, `model_reasoning_effort=max`; CONFIGURED_NOT_OBSERVED (launch arguments, not inference-time telemetry). Original author: Advisor fork on Fable 5.2, as recorded by CC-521.
- Classification: PARTIAL_CAPABILITY_REUSE_COMPONENTS. Reuse the census, store, table and daily-pack reader; add independent arithmetic, quantified attacks, regression fixes and evidence weight in the reader.
- Codegraph status was STALE_CRITICAL; it was only a locator. Current source, exact CC-506 history and the actual pack seam were inspected. No generated graph files changed.
- Input: read-only held bar store at the README path; exact source IDs and acquired-at clocks are in the table and [blind review](audit/blind_readme_review.json). No history was fetched or altered. Raw inputs retain their private redistribution restriction; these computed outputs are used by the existing pack.
- Fixed calendar split: `2021-11-11`; start/end across sources `2016-11-11` / `2026-11-11`. EURUSD runs through 11 Nov; the other five through 10 Nov. These are bulk captures, not historical release vintages.

## Replication sequence and comparison

1. Read the original README and the bar-store schema/rows only. Its missing definitions included the complete behaviour list, yardstick equation, normal-day estimator, execution timing, construction grids and split/t definitions. The review was committed and pushed as `bfc2256fc` before reading the census.
2. Do not invent canonical values from that incomplete method. After freezing the finding, inspect the original implementation, reconcile the complete method in [README.md](README.md), and write [the independent calculator](../../../tools/product/desk_odds_replication_v1.py) without importing production odds functions.
3. Reproduce the original algorithm and compare each published field: n, mean, t, both halves, label; then every column of the four construction tables. [comparison.json](audit/comparison.json) records all 85 exact matches. There are zero original-replication discrepancies over 0.02R or 2% of n, and zero smaller discrepancies. This is explicitly source-reconciled, not the requested blind numeric replication.
4. Correct the confirmed faults, rebuild on the same source IDs and independently calculate the corrected version. The tests compare every corrected market/pooled/construction field and exercise the actual pack reader.

## Confirmed faults and regression fixes

| Fault | Correction and evidence |
|---|---|
| README cannot specify an exact rebuild | Added the full estimator, nine signals, chronology, grids, costs, summary and labels. Preserved the original README hash and pre-source-review finding. |
| Pending entry skips the fill bar and sizes its stop with fill-day completed ATR | Freeze ATR at signal close, start on the actual fill bar, count ten sessions from that fill. An adversarial bar whose eventual ATR changes 1 to 10 or 1,000 still stops at the original 1.5-day distance. Pending stop entries remain an explicit adverse D1 path bound. |
| Two negative-price oil bars silently deleted | Keep finite, coherent signed continuous-futures OHLC. Oil count 2,511 to 2,513; its rally-short mean rises +0.101R to +0.356R with both bars retained. Invalid OHLC now names its market/date instead of disappearing. |
| Every row defines its own halves by median trade date | One fixed calendar midpoint, 11 Nov 2021, for every market and pooled row. Two read labels change below. |
| Intraday stop can override a target already reached at a later bar open | Later open is processed before unknown high/low order. A long opening at 103 beyond a 102 target returns +1.95R even if that bar later trades below a 99 stop. Ambiguous bars that open between barriers retain stop-first. |
| Last two eligible decision indices are discarded | Include each full planned hold through the final available bar. A 136-bar fixture admits the five-session trade from index 130 to 135. |
| Population rather than sample deviation used in nominal t | Use n-1; clearly label t nominal IID. This does not remove serial/cross-market dependence; the block test below models that dependence explicitly. |
| Tiny positive high-t rows bypass the promised FLAT rule | Apply the absolute 0.03R band before PAID_BOTH_HALVES; n<30 remains THIN with its measured values visible. Tests cover positive and negative tiny means. |
| Census and pack can disagree on what a Sunday is | Census drops non-crypto session-date Sundays, not UTC Sunday opens; all BTC weekends remain. No source session-date Sunday exists in the five non-BTC samples. The observed FX Monday bars are preserved. |
| Reader text hardcodes the old construction rankings | It now directs the analyst to the current rows, own cost, ambiguity share and audit text. The rebuilt table carries the chance and walk-forward figures at the same point of use. |

## Attacks

### Look-ahead

Changing all future OHLC after the midpoint changes zero historical signals or ATR values across 7,305 checked market-close prefixes. The completed close legitimately enters its own signal and rolling ATR; large-day signals use the previous ATR. The confirmed forward-information error was the pending-entry fill-day ATR, corrected above. A full source prefix and a future-mutated prefix are also regression-tested. Historical capture clocks are retained separately; this audit does not reconstruct original point-in-time vintages.

### Continuous futures gaps and negative oil

Use an observable sensitivity screen: a candidate discontinuity is abs(open - previous close) > one prior ATR. Exclude a trade if that gap lies in its 14-session volatility input or actual holding interval. This is a sensitivity, not an adjusted replacement series: no contract IDs or roll ledger exist to distinguish rolls from real overnight news. No roll date, adjustment or economic gain is invented.

| Market | >1 prior ATR gaps | >2 prior ATR gaps | Largest gap / prior ATR | LONG_UP: all n, mean R | Excluding exposed trades: n, mean R |
|---|---:|---:|---:|---|---|
| XAUUSD | 62 | 7 | 3.4496 | 76, +0.391 | 52, +0.321 |
| USOIL | 12 | 4 | 3.8617 | 57, +0.167 | 52, +0.062 |
| US500 | 16 | 1 | 2.8007 | 87, +0.113 | 74, +0.065 |

All nine rows per market have the same gap screen in [attacks.json](audit/attacks.json), `markets.*.gap_sensitivity`. Gold LONG_UP changes from PAID_BOTH_HALVES to PAID on that screen; the screening itself is selected with hindsight and removes real moves too.

CL=F has signed bars on 20 and 21 April 2020. Deleting just these two bars under the corrected engine reduces SELL_RALLY_IN_DOWNTREND_10 from +0.356R to +0.101R (n=35 both ways). Retaining them also changes subsequent ATRs and shifts the oil construction grid, which samples by retained index. Its pooled rally-short mean therefore moves -0.029R to +0.018R. The rows remain proxy futures results; this is not a reconstruction of a broker CFD through negative oil.

### Bitcoin calendar and FX day boundaries

Bitcoin has 3,651 daily bars including 522 Saturdays and 522 Sundays. Twenty Bitcoin sessions span about 20 calendar days; twenty five-day-market sessions span about 28 days before holidays. Reindexing Bitcoin onto weekdays leaves 2,607 bars; LONG_WHILE_UP_20 changes n=96, +0.801R to n=61, +0.889R. This changes the strategy clock and its observations; it is a sensitivity, not an improved estimate. All nine seven-day/five-day comparisons are in `bitcoin_five_day_sensitivity`. Pooling trades also gives Bitcoin more weight.

Both FX series metadata name Europe/London, and every stored open is 00:00 in that zone: UTC 00:00 or 23:00 according to the offset. This describes the retained provider timestamp/session convention, not independently verified intraday OHLC construction or the broker day. The audited ten-year snapshots are D1; no ten-year intraday recut was performed, and no synthetic recut is presented.

| Market | Bars | UTC 00:00 | UTC 23:00 | UTC Sunday opens, all Monday sessions | Actual session-date Sunday stubs | LONG_UP after incorrect UTC-Sunday deletion |
|---|---:|---:|---:|---:|---:|---|
| EURUSD | 2532 | 1047 | 1485 | 293 | 0 | n=53, -0.025R, FLAT |
| USDJPY | 2438 | 1014 | 1424 | 280 | 0 | n=60, -0.011R, FLAT |

The census uses `session_date`. The pack today-yardstick still reads its own completed broker D1 bars via its existing owner; this audit does not reinterpret broker time using the Yahoo convention. A synthetic regression verifies that non-BTC Sunday sessions are removed and Bitcoin Sundays are kept.

### Stop versus target within a bar

The two extremes bound an unresolved daily path; no intra-bar probability is inferred. Later opening gaps have known temporal precedence after the fix.

| Stop, normal days | n | Stop-first mean R | Target-first upper-bound mean R | Ambiguous-bar share | Cost R |
|---|---:|---:|---:|---:|---:|
| 0.3 | 1892 | -0.217 | +0.026 | 0.08 | 0.17 |
| 0.5 | 1892 | -0.040 | +0.004 | 0.01 | 0.10 |
| 0.75 | 1892 | -0.005 | +0.011 | 0.01 | 0.07 |
| 1.0 | 1892 | +0.028 | +0.034 | 0.00 | 0.05 |
| 1.5 | 1892 | +0.033 | +0.038 | 0.00 | 0.03 |
| 2.0 | 1892 | +0.027 | +0.029 | 0.00 | 0.03 |
| 3.0 | 1892 | +0.021 | +0.021 | 0.00 | 0.02 |

At a 0.3-day stop the unresolved ordering changes the mean by 0.243R, from -0.217R to +0.026R. The default remains the adverse bound. At a 1.5-day stop it changes only 0.005R. Pending stop entries also use a fill-day adverse bound; an extreme before the entry can be counted as a stop because D1 cannot establish the ordering.

### Cost sensitivity using the cost owner we hold

All six current reserves are taken from the real daily pack, captured 12 Nov 17:20:57 GMT+7. [cost_inputs.json](audit/cost_inputs.json) binds its hash, source path, commission, reserve, ATR and swap basis. These are captured commission/specification plus an adverse-execution reserve, not ten years of realized fills. Nothing treats the 0.05 table assumption as measured broker truth. Exact sensitivity is net_R_new = net_R_old - (market_cost_normal_days - 0.05) / stop_width. No return path or signal changes.

| Market | Own reserve, normal days | LONG_UP at 0.05 | LONG_UP at own captured reserve |
|---|---:|---:|---:|
| EURUSD | 0.070450 | -0.075R | -0.088R |
| USDJPY | 0.062504 | +0.271R | +0.262R |
| XAUUSD | 0.048272 | +0.391R | +0.392R |
| USOIL | 0.024536 | +0.167R | +0.184R |
| US500 | 0.107619 | +0.113R | +0.075R |
| BTCUSD | 0.092434 | +0.801R | +0.772R |

Every one of the 54 rows has this repricing in `cost_sensitivity`; the next pack already carries each market's live cost in `cost_summary`, alongside the rebuilt table. CC-522 owns replacing the uniform census cost with each market's cost and widening the table; this delivery supplies its arithmetic comparison and does not duplicate that item. No historically constant reserve is inferred from a current observation.

### Chance, dependence and 54 inspected rows

For each of the 54 market rows center its net trade returns at zero; multiply residuals by Rademacher signs shared across markets and rows in calendar blocks; recompute mean, sample t, fixed-calendar halves and the >0.03R read band. Seed 521; 2,000 draws; 60-calendar-day blocks. Shared signs preserve contemporaneous market dependence and within-block dependence; block edges approximate longer dependence. A 54-row family test compares each observed t with the largest positive t in each shared draw. One-sided row p values compare means. Both use (1 + exceedances)/(draws + 1).

| Block calendar days | Expected paid rows out of 54 | Central 95% count interval | P(null count >= 5 observed) |
|---|---:|---|---:|
| 20 | 1.083 | 0 to 4 | 0.0095 |
| 60 | 0.978 | 0 to 3 | 0.0080 |
| 120 | 0.679 | 0 to 3 | 0.0020 |

The 60-day null produces at least one apparent winner in 61.2% of draws. Its five-row count p is 0.0080, conditional on these strategies and this centered symmetric-shock null; it is not a probability that any named row is alpha.

| Named test | n | Mean R | Nominal t | One-sided block p | Familywise p, 54 rows |
|---|---:|---:|---:|---:|---:|
| EURUSD/LONG_WHILE_UP_20 | 57 | -0.075 | -0.57 | 0.7186 | 1.0000 |
| USDJPY/LONG_WHILE_UP_20 | 66 | +0.271 | 1.45 | 0.1124 | 0.9640 |
| XAUUSD/LONG_WHILE_UP_20 | 76 | +0.391 | 2.14 | 0.0135 | 0.4823 |
| USOIL/LONG_WHILE_UP_20 | 57 | +0.167 | 0.87 | 0.1934 | 1.0000 |
| US500/LONG_WHILE_UP_20 | 87 | +0.113 | 0.73 | 0.2564 | 1.0000 |
| US500/BUY_PULLBACK_IN_UPTREND_10 | 60 | +0.355 | 2.04 | 0.0165 | 0.5717 |
| BTCUSD/LONG_WHILE_UP_20 | 96 | +0.801 | 2.79 | 0.0005 | 0.0855 |
| BTCUSD/BREAKOUT_WITH_TREND_20 | 114 | +0.531 | 2.86 | 0.0005 | 0.0710 |

None of these eight named tests has familywise p<0.05. The null is conditional on the already chosen 54 behaviours; it does not count undisclosed earlier trials, remove asset drift, guarantee symmetric residuals or prove local stationarity. It is a dependence/selection attack, not prospective performance evidence or a new trade gate.

### First five years chosen, last five years read

Use the same split, 11 Nov 2021. A training trade must have its entire planned hold end strictly before the split. Choose market/behaviour rows with training n>=30, mean>0.03R and nominal t>=2; lock the chosen codes, start the test flat and process only decision dates on/after the split. Holdout prices cannot change training selection; that invariance is regression-tested. This is a retrospective fixed-split read, not a selection frozen in 2021.

| Market / row | Training n | Training mean R | Training t | Later n | Later mean R | Later t |
|---|---:|---:|---:|---:|---:|---:|
| BTCUSD / LONG_WHILE_UP_20 | 50 | +1.053 | 2.4 | 46 | +0.528 | 1.4 |
| BTCUSD / WITH_YARDSTICK_5 | 240 | +0.207 | 3.0 | 258 | -0.019 | -0.3 |
| BTCUSD / BREAKOUT_WITH_TREND_20 | 55 | +0.812 | 3.1 | 58 | +0.291 | 1.1 |

All 3 selected rows are Bitcoin rows; 2 stay positive. Together: 362 later trades, mean +0.099917R at the uniform 0.05-normal-day cost. None has later nominal t>=2. This is a pooled dependent trade mean, not a portfolio return; changing Bitcoin's regime is a material concentration. The training and test rows for every one of the 54 candidates are retained in `walk_forward.rows`.

### Calendar-year results

Every market/behaviour/year is in [attacks.json](audit/attacks.json), `annual`, including n, mean, nominal t, both within-year halves and THIN years with their numbers retained. The table below shows LONG_WHILE_UP_20 as n / mean R. 2016 has no admitted observations after warmup; 2026 is partial through each source cutoff. Annual t values are descriptive and not independent tests.

| Year | EURUSD | USDJPY | XAUUSD | USOIL | US500 | BTCUSD |
|---|---|---|---|---|---|---|
| 2016 | 0 / absent | 0 / absent | 0 / absent | 0 / absent | 0 / absent | 0 / absent |
| 2017 | 7 / -0.182 | 4 / +0.026 | 5 / +1.434 | 5 / +0.559 | 8 / +1.415 | 13 / +2.192 |
| 2018 | 5 / -0.240 | 7 / +0.126 | 6 / -0.030 | 7 / -0.252 | 8 / -0.722 | 5 / -0.521 |
| 2019 | 6 / -0.616 | 5 / -0.647 | 10 / +0.305 | 7 / -0.157 | 9 / +0.437 | 8 / +1.764 |
| 2020 | 10 / +0.372 | 3 / -0.200 | 10 / +0.178 | 6 / +0.530 | 9 / +0.631 | 13 / +0.697 |
| 2021 | 3 / -0.809 | 10 / -0.160 | 5 / +0.021 | 8 / +0.159 | 12 / -0.274 | 12 / +0.221 |
| 2022 | 3 / +0.009 | 9 / +1.652 | 6 / -0.330 | 6 / -0.516 | 2 / -0.184 | 5 / -0.901 |
| 2023 | 7 / +0.036 | 9 / +0.574 | 8 / +0.078 | 5 / -0.009 | 10 / +0.048 | 12 / +1.794 |
| 2024 | 5 / -0.024 | 7 / +0.136 | 11 / +0.305 | 5 / +0.361 | 12 / +0.132 | 14 / +0.436 |
| 2025 | 8 / -0.035 | 6 / +0.171 | 12 / +1.128 | 2 / -0.252 | 10 / -0.104 | 8 / +0.162 |
| 2026 | 3 / +0.249 | 6 / +0.049 | 3 / +0.753 | 6 / +1.164 | 7 / -0.381 | 6 / +0.122 |

## Rebuilt rows and changes

Only two market read labels change:

| Market | Row | Original read | Rebuilt read | Reason |
|---|---|---|---|---|
| EURUSD | LONG_WHILE_UP_20 | LOST_BOTH_HALVES | LOST | Calendar halves -0.16R / +0.02R replace trade-count halves -0.09R / -0.06R. |
| USOIL | SHORT_WHILE_DOWN_20 | LOST_BOTH_HALVES | LOST | Calendar halves +0.07R / -0.19R replace -0.01R / -0.15R; signed oil also changes paths. |

The original source-reconciled comparison has no differences at all. In the corrected table, the only mean changes over 0.02R are USOIL SELL_RALLY_IN_DOWNTREND_10 (+0.255R) and its pooled row (+0.047R), both explained by signed oil retention. No market or pooled n changes by more than 2%. Half-mean changes reflect the common calendar split; rounded t changes reflect sample deviation and the corrected paths. The oil construction grid also shifts after two restored sessions. Every corrected field follows below, so changes under those thresholds remain visible.

Each numeric cell is `n / mean R / t / first half R / second half R / read`. Original and rebuilt values use their respective documented half definitions.

| Market / behaviour | Original | Rebuilt |
|---|---|---|
| EURUSD / LONG_WHILE_UP_20 | 57 / -0.075 / -0.6 / -0.09 / -0.06 / LOST_BOTH_HALVES | 57 / -0.075 / -0.6 / -0.16 / 0.02 / LOST |
| EURUSD / SHORT_WHILE_DOWN_20 | 61 / -0.237 / -1.7 / -0.16 / -0.31 / LOST_BOTH_HALVES | 61 / -0.237 / -1.7 / -0.13 / -0.33 / LOST_BOTH_HALVES |
| EURUSD / WITH_YARDSTICK_5 | 348 / -0.094 / -2.3 / -0.06 / -0.13 / LOST_BOTH_HALVES | 348 / -0.094 / -2.3 / -0.08 / -0.11 / LOST_BOTH_HALVES |
| EURUSD / AGAINST_YARDSTICK_5 | 348 / -0.03 / -0.5 / -0.02 / -0.04 / FLAT | 348 / -0.03 / -0.5 / -0.01 / -0.05 / FLAT |
| EURUSD / BUY_PULLBACK_IN_UPTREND_10 | 28 / null / null / null / null / THIN | 28 / -0.028 / -0.2 / 0.25 / -0.23 / THIN |
| EURUSD / SELL_RALLY_IN_DOWNTREND_10 | 28 / null / null / null / null / THIN | 28 / 0.024 / 0.1 / -0.25 / 0.26 / THIN |
| EURUSD / BREAKOUT_WITH_TREND_20 | 82 / -0.082 / -0.7 / -0.19 / 0.02 / LOST | 82 / -0.082 / -0.7 / -0.19 / 0.01 / LOST |
| EURUSD / FOLLOW_LARGE_DAY_3 | 168 / -0.099 / -1.6 / -0.15 / -0.05 / LOST_BOTH_HALVES | 168 / -0.099 / -1.6 / -0.13 / -0.07 / LOST_BOTH_HALVES |
| EURUSD / FADE_LARGE_DAY_3 | 168 / -0.079 / -1.2 / -0.1 / -0.06 / LOST_BOTH_HALVES | 168 / -0.079 / -1.2 / -0.11 / -0.05 / LOST_BOTH_HALVES |
| USDJPY / LONG_WHILE_UP_20 | 66 / 0.271 / 1.5 / 0.2 / 0.34 / PAID | 66 / 0.271 / 1.5 / -0.15 / 0.56 / PAID |
| USDJPY / SHORT_WHILE_DOWN_20 | 45 / -0.162 / -1.1 / -0.09 / -0.24 / LOST_BOTH_HALVES | 45 / -0.162 / -1.1 / -0.16 / -0.16 / LOST_BOTH_HALVES |
| USDJPY / WITH_YARDSTICK_5 | 333 / -0.067 / -1.5 / -0.11 / -0.02 / LOST_BOTH_HALVES | 334 / -0.068 / -1.5 / -0.12 / -0.03 / LOST_BOTH_HALVES |
| USDJPY / AGAINST_YARDSTICK_5 | 333 / -0.069 / -1.2 / -0.07 / -0.06 / LOST_BOTH_HALVES | 334 / -0.067 / -1.1 / -0.1 / -0.04 / LOST_BOTH_HALVES |
| USDJPY / BUY_PULLBACK_IN_UPTREND_10 | 33 / -0.282 / -1.4 / -0.47 / -0.11 / LOST_BOTH_HALVES | 33 / -0.282 / -1.4 / -0.45 / -0.17 / LOST_BOTH_HALVES |
| USDJPY / SELL_RALLY_IN_DOWNTREND_10 | 27 / null / null / null / null / THIN | 27 / -0.136 / -0.7 / -0.02 / -0.33 / THIN |
| USDJPY / BREAKOUT_WITH_TREND_20 | 80 / -0.077 / -0.7 / -0.26 / 0.11 / LOST | 80 / -0.077 / -0.7 / -0.26 / 0.08 / LOST |
| USDJPY / FOLLOW_LARGE_DAY_3 | 196 / -0.101 / -1.6 / -0.01 / -0.19 / LOST_BOTH_HALVES | 196 / -0.101 / -1.6 / -0.02 / -0.17 / LOST_BOTH_HALVES |
| USDJPY / FADE_LARGE_DAY_3 | 196 / -0.083 / -1.2 / -0.11 / -0.06 / LOST_BOTH_HALVES | 196 / -0.083 / -1.2 / -0.1 / -0.07 / LOST_BOTH_HALVES |
| XAUUSD / LONG_WHILE_UP_20 | 76 / 0.391 / 2.2 / 0.29 / 0.49 / PAID_BOTH_HALVES | 76 / 0.391 / 2.1 / 0.35 / 0.43 / PAID_BOTH_HALVES |
| XAUUSD / SHORT_WHILE_DOWN_20 | 41 / -0.197 / -1.1 / 0.16 / -0.53 / LOST | 41 / -0.197 / -1.1 / 0.1 / -0.51 / LOST |
| XAUUSD / WITH_YARDSTICK_5 | 349 / 0.053 / 1.0 / -0.0 / 0.11 / PAID | 349 / 0.053 / 1.0 / 0.01 / 0.09 / PAID |
| XAUUSD / AGAINST_YARDSTICK_5 | 349 / -0.106 / -1.6 / -0.08 / -0.13 / LOST_BOTH_HALVES | 349 / -0.106 / -1.6 / -0.1 / -0.11 / LOST_BOTH_HALVES |
| XAUUSD / BUY_PULLBACK_IN_UPTREND_10 | 62 / -0.083 / -0.6 / -0.26 / 0.09 / LOST | 62 / -0.083 / -0.6 / -0.29 / 0.15 / LOST |
| XAUUSD / SELL_RALLY_IN_DOWNTREND_10 | 19 / null / null / null / null / THIN | 19 / -0.022 / -0.1 / -0.06 / 0.03 / THIN |
| XAUUSD / BREAKOUT_WITH_TREND_20 | 82 / 0.182 / 1.2 / 0.07 / 0.29 / PAID | 82 / 0.182 / 1.2 / 0.12 / 0.24 / PAID |
| XAUUSD / FOLLOW_LARGE_DAY_3 | 278 / 0.039 / 0.6 / 0.05 / 0.03 / PAID | 279 / 0.04 / 0.6 / 0.02 / 0.06 / PAID |
| XAUUSD / FADE_LARGE_DAY_3 | 278 / -0.011 / -0.2 / -0.0 / -0.02 / FLAT | 279 / -0.015 / -0.2 / 0.03 / -0.06 / FLAT |
| USOIL / LONG_WHILE_UP_20 | 57 / 0.151 / 0.8 / 0.19 / 0.12 / PAID | 57 / 0.167 / 0.9 / 0.13 / 0.21 / PAID |
| USOIL / SHORT_WHILE_DOWN_20 | 55 / -0.083 / -0.6 / -0.01 / -0.15 / LOST_BOTH_HALVES | 55 / -0.096 / -0.7 / 0.07 / -0.19 / LOST |
| USOIL / WITH_YARDSTICK_5 | 333 / 0.015 / 0.3 / 0.08 / -0.05 / FLAT | 333 / 0.02 / 0.4 / 0.08 / -0.04 / FLAT |
| USOIL / AGAINST_YARDSTICK_5 | 333 / -0.136 / -2.2 / -0.23 / -0.04 / LOST_BOTH_HALVES | 333 / -0.137 / -2.2 / -0.21 / -0.07 / LOST_BOTH_HALVES |
| USOIL / BUY_PULLBACK_IN_UPTREND_10 | 45 / -0.227 / -1.5 / -0.08 / -0.36 / LOST_BOTH_HALVES | 45 / -0.227 / -1.5 / -0.07 / -0.39 / LOST_BOTH_HALVES |
| USOIL / SELL_RALLY_IN_DOWNTREND_10 | 35 / 0.101 / 0.5 / 0.02 / 0.17 / PAID | 35 / 0.356 / 1.0 / 0.64 / 0.17 / PAID |
| USOIL / BREAKOUT_WITH_TREND_20 | 82 / 0.063 / 0.5 / 0.13 / -0.0 / PAID | 82 / 0.065 / 0.5 / 0.13 / -0.0 / PAID |
| USOIL / FOLLOW_LARGE_DAY_3 | 229 / -0.153 / -2.2 / -0.11 / -0.19 / LOST_BOTH_HALVES | 226 / -0.155 / -2.2 / -0.12 / -0.19 / LOST_BOTH_HALVES |
| USOIL / FADE_LARGE_DAY_3 | 229 / 0.052 / 0.8 / -0.05 / 0.16 / PAID | 226 / 0.07 / 1.0 / -0.02 / 0.16 / PAID |
| US500 / LONG_WHILE_UP_20 | 87 / 0.113 / 0.7 / 0.27 / -0.04 / PAID | 87 / 0.113 / 0.7 / 0.31 / -0.09 / PAID |
| US500 / SHORT_WHILE_DOWN_20 | 30 / -0.3 / -1.9 / -0.17 / -0.43 / LOST_BOTH_HALVES | 30 / -0.3 / -1.8 / -0.22 / -0.35 / LOST_BOTH_HALVES |
| US500 / WITH_YARDSTICK_5 | 378 / -0.006 / -0.1 / 0.03 / -0.04 / FLAT | 378 / -0.006 / -0.1 / 0.05 / -0.06 / FLAT |
| US500 / AGAINST_YARDSTICK_5 | 378 / -0.111 / -1.9 / -0.17 / -0.05 / LOST_BOTH_HALVES | 378 / -0.111 / -1.9 / -0.21 / -0.02 / LOST_BOTH_HALVES |
| US500 / BUY_PULLBACK_IN_UPTREND_10 | 60 / 0.355 / 2.1 / 0.42 / 0.29 / PAID_BOTH_HALVES | 60 / 0.355 / 2.0 / 0.57 / 0.21 / PAID_BOTH_HALVES |
| US500 / SELL_RALLY_IN_DOWNTREND_10 | 24 / null / null / null / null / THIN | 24 / -0.007 / -0.0 / -0.67 / 0.47 / THIN |
| US500 / BREAKOUT_WITH_TREND_20 | 91 / 0.027 / 0.2 / 0.01 / 0.05 / FLAT | 91 / 0.027 / 0.2 / 0.03 / 0.02 / FLAT |
| US500 / FOLLOW_LARGE_DAY_3 | 232 / -0.095 / -1.3 / -0.13 / -0.06 / LOST_BOTH_HALVES | 233 / -0.099 / -1.4 / -0.17 / -0.04 / LOST_BOTH_HALVES |
| US500 / FADE_LARGE_DAY_3 | 232 / 0.073 / 0.9 / 0.05 / 0.1 / PAID | 233 / 0.079 / 1.0 / 0.09 / 0.07 / PAID |
| BTCUSD / LONG_WHILE_UP_20 | 96 / 0.801 / 2.8 / 1.04 / 0.56 / PAID_BOTH_HALVES | 96 / 0.801 / 2.8 / 1.01 / 0.56 / PAID_BOTH_HALVES |
| BTCUSD / SHORT_WHILE_DOWN_20 | 73 / 0.297 / 1.2 / 0.73 / -0.12 / PAID | 73 / 0.297 / 1.2 / 0.8 / -0.07 / PAID |
| BTCUSD / WITH_YARDSTICK_5 | 499 / 0.09 / 1.9 / 0.2 / -0.02 / PAID | 499 / 0.09 / 1.9 / 0.21 / -0.02 / PAID |
| BTCUSD / AGAINST_YARDSTICK_5 | 499 / -0.078 / -1.5 / -0.16 / 0.0 / LOST | 499 / -0.078 / -1.5 / -0.17 / 0.01 / LOST |
| BTCUSD / BUY_PULLBACK_IN_UPTREND_10 | 63 / 0.071 / 0.4 / 0.14 / 0.0 / PAID | 63 / 0.071 / 0.4 / 0.1 / 0.04 / PAID |
| BTCUSD / SELL_RALLY_IN_DOWNTREND_10 | 59 / -0.092 / -0.6 / -0.24 / 0.05 / LOST | 59 / -0.092 / -0.6 / -0.29 / 0.04 / LOST |
| BTCUSD / BREAKOUT_WITH_TREND_20 | 114 / 0.531 / 2.9 / 0.76 / 0.3 / PAID_BOTH_HALVES | 114 / 0.531 / 2.9 / 0.78 / 0.29 / PAID_BOTH_HALVES |
| BTCUSD / FOLLOW_LARGE_DAY_3 | 384 / 0.207 / 2.5 / 0.21 / 0.2 / PAID_BOTH_HALVES | 384 / 0.207 / 2.5 / 0.19 / 0.22 / PAID_BOTH_HALVES |
| BTCUSD / FADE_LARGE_DAY_3 | 384 / -0.017 / -0.3 / -0.01 / -0.03 / FLAT | 384 / -0.017 / -0.3 / -0.01 / -0.03 / FLAT |
| ALL_SIX / LONG_WHILE_UP_20 | 439 / 0.316 / 3.6 / 0.34 / 0.29 / PAID_BOTH_HALVES | 439 / 0.318 / 3.6 / 0.33 / 0.31 / PAID_BOTH_HALVES |
| ALL_SIX / SHORT_WHILE_DOWN_20 | 305 / -0.071 / -0.9 / 0.11 / -0.25 / LOST | 305 / -0.074 / -0.9 / 0.12 / -0.24 / LOST |
| ALL_SIX / WITH_YARDSTICK_5 | 2240 / 0.005 / 0.3 / 0.03 / -0.02 / FLAT | 2241 / 0.006 / 0.3 / 0.04 / -0.03 / FLAT |
| ALL_SIX / AGAINST_YARDSTICK_5 | 2240 / -0.088 / -3.7 / -0.12 / -0.05 / LOST_BOTH_HALVES | 2241 / -0.087 / -3.7 / -0.14 / -0.04 / LOST_BOTH_HALVES |
| ALL_SIX / BUY_PULLBACK_IN_UPTREND_10 | 291 / 0.001 / 0.0 / 0.01 / -0.01 / FLAT | 291 / 0.001 / 0.0 / 0.02 / -0.02 / FLAT |
| ALL_SIX / SELL_RALLY_IN_DOWNTREND_10 | 192 / -0.029 / -0.3 / -0.17 / 0.11 / FLAT | 192 / 0.018 / 0.2 / -0.1 / 0.12 / FLAT |
| ALL_SIX / BREAKOUT_WITH_TREND_20 | 531 / 0.132 / 2.3 / 0.15 / 0.12 / PAID_BOTH_HALVES | 531 / 0.132 / 2.3 / 0.15 / 0.12 / PAID_BOTH_HALVES |
| ALL_SIX / FOLLOW_LARGE_DAY_3 | 1487 / -0.002 / -0.1 / -0.0 / -0.0 / FLAT | 1486 / -0.003 / -0.1 / -0.0 / -0.0 / FLAT |
| ALL_SIX / FADE_LARGE_DAY_3 | 1487 / -0.007 / -0.3 / -0.02 / 0.0 / FLAT | 1486 / -0.004 / -0.2 / -0.01 / 0.0 / FLAT |

All four construction tables (column orders are in the JSON and README):

| Table / row | Original numeric columns | Rebuilt numeric columns |
|---|---|---|
| stop_width / 0.3 | 1896 / -0.219 / 0.32 / 0.68 / 0.08 / 0.17 | 1892 / -0.217 / 0.32 / 0.68 / 0.08 / 0.17 |
| stop_width / 0.5 | 1896 / -0.032 / 0.37 / 0.62 / 0.01 / 0.1 | 1892 / -0.04 / 0.37 / 0.62 / 0.01 / 0.1 |
| stop_width / 0.75 | 1896 / 0.019 / 0.41 / 0.53 / 0.0 / 0.07 | 1892 / -0.005 / 0.4 / 0.54 / 0.01 / 0.07 |
| stop_width / 1.0 | 1896 / 0.037 / 0.45 / 0.43 / 0.0 / 0.05 | 1892 / 0.028 / 0.44 / 0.44 / 0.0 / 0.05 |
| stop_width / 1.5 | 1896 / 0.039 / 0.5 / 0.27 / 0.0 / 0.03 | 1892 / 0.033 / 0.49 / 0.27 / 0.0 / 0.03 |
| stop_width / 2.0 | 1896 / 0.033 / 0.51 / 0.16 / 0.0 / 0.03 | 1892 / 0.027 / 0.5 / 0.16 / 0.0 / 0.03 |
| stop_width / 3.0 | 1896 / 0.023 / 0.51 / 0.06 / 0.0 / 0.02 | 1892 / 0.021 / 0.5 / 0.06 / 0.0 / 0.02 |
| entry / at the next open | 1.0 / 0.111 / 0.111 / 1891 | 1.0 / 0.117 / 0.117 / 1887 |
| entry / limit 0.5 normal day better, good for 3 sessions | 0.6 / 0.078 / 0.13 / 1133 | 0.61 / 0.071 / 0.116 / 1144 |
| entry / limit 1 normal day better, 3 sessions | 0.34 / 0.006 / 0.016 / 645 | 0.35 / 0.016 / 0.045 / 665 |
| entry / stop entry 0.5 normal day further, 3 sessions | 0.6 / 0.095 / 0.158 / 1139 | 0.6 / 0.111 / 0.186 / 1127 |
| entry / stop entry 1 normal day further, 3 sessions | 0.36 / 0.066 / 0.182 / 686 | 0.35 / 0.054 / 0.154 / 663 |
| exit / target 1.0R | 1891 / 0.025 / 0.53 | 1887 / 0.017 / 0.53 |
| exit / target 1.5R | 1891 / 0.044 / 0.49 | 1887 / 0.037 / 0.48 |
| exit / target 2.0R | 1891 / 0.064 / 0.47 | 1887 / 0.058 / 0.47 |
| exit / target 3.0R | 1891 / 0.08 / 0.47 | 1887 / 0.077 / 0.46 |
| exit / no target, stop trailed on closes | 1891 / 0.111 / 0.43 | 1887 / 0.117 / 0.42 |
| hold / 3 | 1897 / 0.034 / 0.49 | 1892 / 0.019 / 0.48 |
| hold / 5 | 1896 / 0.063 / 0.48 | 1892 / 0.06 / 0.47 |
| hold / 10 | 1891 / 0.111 / 0.43 | 1887 / 0.117 / 0.42 |
| hold / 20 | 1888 / 0.155 / 0.38 | 1883 / 0.164 / 0.38 |
| hold / 40 | 1876 / 0.171 / 0.38 | 1872 / 0.176 / 0.38 |

A pending stop entry 0.5 normal day further changes its mean per fill from +0.158R to +0.186R (+0.028R). That combines the corrected fill-day/ATR chronology, restored signed oil, grid phase and opening chronology. No fill is fabricated; fill counts and the per-signal denominator remain visible.

## Consumer and validation

- Targeted command: `python -B -m pytest -q tests/test_desk_odds_v1.py tests/test_desk_odds_audit_v1.py tests/test_role_pack_v1.py`; 40 passed in 7.95 s, one pytest process, 12 Nov 2026. Each confirmed arithmetic/loader/label fault has a regression example; tests also check independent full-table equality, seeded resampling, holdout selection and the daily-pack seam.
- Rebuilt content hash: `7758cd662c3244d00740ac929dda5395bfb32eb2dae85a8783826f9446720aa8`; original `08a47e5e58406d609bccd76017707aea9f810519afb83b7f2f1d363582eba226`. The new table's `what_this_is` is exactly the two sentences in [summary.json](audit/summary.json).
- A local replay copied the real 12 Nov daily request's named inputs; source hashes were unchanged before/after. Existing `role_pack_v1.write` used the rebuilt table and exact caveat text. Build 2.084 s, 41 reading-plan reads, longest line 20,937 bytes / 40,000 allowed. All six measured-market rows and construction blocks match the table. [consumer_check.json](audit/consumer_check.json) records the paths/hashes; raw copied inputs remain local and uncommitted.
- This proves the delivered reader uses the output. It does not claim integration or a natural later analyst run. Ops Live integrates the branch, then the next daily pack must carry this content hash and the same chance/walk-forward sentences; its analyst can weigh the rows with the own-cost block already provided. No Claude CLI is started here.
- Delivery remains BUILT_UNMERGED pending that Ops live step and natural consumer readback. No schedule change, deployment or live-root mutation was performed.
