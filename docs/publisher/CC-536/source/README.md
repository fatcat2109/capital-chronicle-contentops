# Desk odds and desk record

CC-533 adds the [plain-book reference](plain-book/README.md), its walk-forward
comparison, compact pack block and CC-476 weekly columns. The current table uses
CC-521's audited arithmetic. Its committed six-market census is retained; the
plain book consumes CC-522's dated 11-market runtime table and per-market costs.

Jim, 12 Nov 2026: "Tìm ra lõi tối ưu nhất cho Main, sau đó áp dụng vào thay đổi ngay, không chờ."

Every analyst pack (`tools/product/role_pack_v1.py`) now carries two evidence blocks and three reading lines:

- `desk_odds`: what plain trade behaviours paid on the six first-phase markets over ten years of daily bars, in R
  after costs, with both half-periods; construction tables for stop width, entry, exit and hold; and today's trend
  yardstick per market, computed from the pack's own completed D1 bars.
- `desk_record`: how the desk's analyst scored when its decisions were played forward (the blind replay of 4 to 10
  November 2026). The learning loop adds live rows.

Both are evidence. Nothing here arms, refuses or sizes a trade (Jim's decisions 125 and 128).

## Files

| File | What |
|---|---|
| `desk_odds_v1.json` | The measured table. Built by `tools/product/desk_odds_census_v1.py` |
| `desk_record_v1.json` | The replay record, each pass counted once |
| `tools/product/desk_odds_v1.py` | Reads both, adds today's yardstick, returns the blocks and the three lines |
| `tests/test_desk_odds_v1.py` | The trade arithmetic, the yardstick, the table's shape and hash, the pack seam |

## Rebuild the table

```
python -B -m tools.product.desk_odds_census_v1 --store "A:\Capital Chronicle\Runtime\OfficialRates\cc-078-20261101\state\intake\completed-bars\bars.sqlite3"
```

It reads the history store read-only (the D1 series of `statistics-service.json`: Yahoo's EURUSD=X, JPY=X, GC=F,
CL=F, ES=F and BTC-USD) and rewrites `desk_odds_v1.json`. A rebuild after new bars changes the counts slightly.

## Reproducing the CC-521 audit

```
python -B -m tools.product.desk_odds_audit_v1 --store "A:\Capital Chronicle\Runtime\OfficialRates\cc-078-20261101\state\intake\completed-bars\bars.sqlite3"
python -B -m tools.product.desk_odds_census_v1 --store "A:\Capital Chronicle\Runtime\OfficialRates\cc-078-20261101\state\intake\completed-bars\bars.sqlite3" --source-manifest data/research/desk-odds/audit/baseline_table.json --audit data/research/desk-odds/audit/summary.json
```

The audit uses frozen source IDs, without fetching. The second command writes the existing daily-pack reader's
table. Its `what_this_is` carries the chance and walk-forward results in two sentences. Later builds retain the
dated audit sample and record whether their source IDs match it. [AUDIT.md](AUDIT.md) holds the results and limits.

The original README omitted definitions needed for an exact blind rebuild. The [blind review](audit/blind_readme_review.json)
was committed before inspecting the census. The independent calculator was then written against the reconciled
method below. Its exact original-table match is a source-reconciled replication, not an outcome-blind experiment.
The original table, including its earlier descriptions, is retained in [baseline_table.json](audit/baseline_table.json),
hash `08a47e5e58406d609bccd76017707aea9f810519afb83b7f2f1d363582eba226`.

## Exact method (CC-521)

### Inputs and clocks

For each market select the newest `known_epoch` D1 capture of its named Yahoo series; break ties by descending
`source_id`. `--source-manifest` pins the IDs in its `markets` map instead. Read bars in `open_epoch` order.
Require finite OHLC and `low <= min(open, close) <= max(open, close) <= high`; invalid rows raise market and date.
Signed continuous-futures prices are retained, including the two April 2020 oil bars. Spot FX and BTC prices
must be positive. Remove non-BTC Sundays by `session_date`, not UTC opening weekday. Keep all Bitcoin days.
There is no roll adjustment or imputation. Bulk capture-known-at is not original historical availability.

At completed close index `i`, normal day `A[i]` is the simple mean of the last 14 true ranges, including `i`:
`TR[j] = max(high[j]-low[j], abs(high[j]-close[j-1]), abs(low[j]-close[j-1]))`.
First ATR is at index 14. This is not Wilder smoothing. Signals are decided after close `i`.

The yardstick is UP (+1) if all four differences below are strictly positive, DOWN (-1) if all are strictly
negative, otherwise MIXED (0); it is 0 before index 60:
`close[i]-close[i-20]`, `close[i]-close[i-60]`, `close[i]-mean(close[i-19:i+1])`,
`close[i]-mean(close[i-49:i+1])`. `sign(x)` is +1, -1 or 0.

### All nine behaviours

Let `s` be the yardstick, `T120=sign(close[i]-close[i-120])`, `T60=sign(close[i]-close[i-60])`.
The prior 20-close range excludes `i`. Stop and target columns are multiples of `A[i]`.

| Code | Side at close i (0 if condition fails) | Stop | Target | Hold sessions | Trail |
|---|---|---:|---:|---:|---|
| LONG_WHILE_UP_20 | +1 if s=+1 | 1.5 | none | 20 | yes |
| SHORT_WHILE_DOWN_20 | -1 if s=-1 | 1.5 | none | 20 | yes |
| WITH_YARDSTICK_5 | s | 1.5 | 3 | 5 | no |
| AGAINST_YARDSTICK_5 | -s | 1 | 2 | 5 | no |
| BUY_PULLBACK_IN_UPTREND_10 | +1 if T120=+1 and `(close[i]-close[i-3])/A[i] <= -1.5` | 1.5 | none | 10 | yes |
| SELL_RALLY_IN_DOWNTREND_10 | -1 if T120=-1 and `(close[i]-close[i-3])/A[i] >= 1.5` | 1.5 | none | 10 | yes |
| BREAKOUT_WITH_TREND_20 | +1 if T60=+1 and close exceeds every prior 20 closes; -1 if T60=-1 and below every prior 20 closes | 2 | none | 20 | yes |
| FOLLOW_LARGE_DAY_3 | sign of one-session close change, if absolute change >= A[i-1] | 1 | none | 3 | no |
| FADE_LARGE_DAY_3 | opposite of FOLLOW_LARGE_DAY_3 | 1 | none | 3 | no |

Start at index 130. Require the full planned hold through `i+hold` to exist. Each market/behaviour next allows
a decision at `i+hold`, even when the previous stop exited early. Its last holding close can also be the next
decision close. Skip zero signals or zero ATR. Enter at `open[i+1]`.

### Trade arithmetic and within-bar ordering

Freeze `D=stop_width*A[i]` and cost `0.05/stop_width` R. Stop is `entry-side*D`; target, if any, is
`entry+side*target_width*A[i]`. Check each holding bar including the entry bar. On later bars, a gap beyond
the stop exits at that open; an open beyond the target fills at the target before testing the intraday range.
Otherwise take the stop when both barriers lie inside one bar and count ambiguity. This is the adverse
daily-bar bound; target-first sensitivity is an upper bound, not another observed path.

After a bar with no exit, trail behind the best close since entry by the original fixed `D`, tightening only;
the new stop becomes effective next bar. Without a barrier exit, use the last holding close. Net R is
`side*(exit-entry)/D - 0.05/stop_width`. The fixed cost is an assumption, not ten years of broker fill costs.

### Summary, halves and read values

Report n, mean R, nominal `t=mean/(sample_sd/sqrt(n))` with variance divisor `n-1` (t=0 with zero spread),
and means in both calendar halves. Round mean to 3 decimals, t to 1, halves to 2. All rows use the same
midpoint date, halfway from the earliest first session to the latest last session, rounded down: 2021-11-11
for this sample. Assign trades by decision date, before versus on/after midpoint. Pool trades, not market weights.

Apply in order: n<30 is THIN while retaining measured numbers; absolute mean <=0.03R is FLAT;
mean >0.03R, both calendar halves >0 and t>=2 is PAID_BOTH_HALVES; negative mean and both halves <0 is
LOST_BOTH_HALVES; remaining positive/negative rows are PAID/LOST. No observations give null values.
A missing half cannot read paid or lost in both. Nominal t does not correct for dependence or row selection.

### Four construction tables

Pool all markets; take the yardstick side on every fifth retained session, starting index 60. For hold h,
use `range(60, len(bars)-h-6, 5)`; skip zero yardstick/ATR. Trades overlap and each hold has its own endpoint.
Bitcoin has more observations. The grid's phase is fixed by each source's first bar. Win share is net R>0;
stopped share counts net R<=-1, including worse gaps. No IID t is reported for construction rows.

- **Stop width:** 0.3, 0.5, 0.75, 1, 1.5, 2 and 3 normal days; target twice the stop, hold 5, no trail.
  Report n, mean R, win share, stopped share, both-barrier share and `cost_r=0.05/width`.
- **Exit:** stop 1.5, hold 10, targets 1, 1.5, 2 and 3 R (1.5, 2.25, 3, 4.5 normal days), no trail; a fifth
  row has no target and trails on closes. Report n, mean R, win share.
- **Hold:** stop 1.5, no target, trail on closes; 3, 5, 10, 20 and 40 sessions. Report n, mean R, win share.
- **Entry:** stop 1.5, no target, trail, hold 10 from fill session inclusive, ATR frozen at decision i.
  Compare next open with limits 0.5/1 normal day against the signal and stops 0.5/1 normal day along it,
  measured from close i. Orders expire after bars i+1 through i+3. A limit fills at the better of open and
  level, a stop at the worse. Check the fill bar for a stop using its full range. For a stop entry this can
  count a pre-fill extreme as a stop: it is explicitly an adverse-path floor. The fill bar's open precedes
  an intraday fill and cannot be an earlier exit. Do not skip the fill day or use its completed ATR.
  No fill contributes 0 per signal, nothing per fill; charge cost only on fills. Report fill share, mean R
  per signal, mean R per fill and fill count.

## Limits

- Ten years of one regime: a bull market in gold, shares and Bitcoin. The long rows carry that drift.
- Daily bars: inside one bar the stop is taken before the target, so a very tight stop's figure is a floor.
- Continuous futures have unidentified roll discontinuities as well as real gaps. The audit measures gap
  sensitivity; the source has no constituent-contract roll ledger. The uniform 0.05-normal-day cost is
  compared with each market's captured cost-owner reserve in the audit and with today's cost in the pack.
- 54 market rows were looked at; some would look good by chance. A row with one bad half or few trades is weak.
- Stop width: about half of the gap between the 0.3 and the 1.0 row is the cost (`cost_r`), and the 0.3 row also
  counts every bar that held both the stop and the target as a stop. The pack line says so and leaves the
  construction to the analyst (Ops Live review, CC-506).
- A row within 0.03R of zero reads FLAT, whatever its halves or t (unless n<30, which is THIN).
