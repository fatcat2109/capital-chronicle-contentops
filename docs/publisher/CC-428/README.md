# CC-428 — external forecast rehearsal and partner pilot

The closed-round rehearsal is built. It uses Main's held numbers and makes no
submission. The partner shortlist and offer are being completed in this item.

## Forecast result

The [result summary](dry-run-summary.json) covers 60 distinct visible posts from
[MiniBench 19 October 2026](https://www.metaculus.com/tournament/minibench-2026-10-19/),
which ended 6 November. The page advertises 59 questions. Both counts are retained;
the listing discrepancy is not repaired by dropping a post or guessing a question ID.
This is a retrospective mapping and serialization rehearsal, not an external score.

Main supplied 42 typed probabilities across the six markets and four retained
CPI/payroll scenario sets. The result has 60 abstentions, zero exact matches,
zero network calls, zero submissions, and no external score or rank.

- 55 questions fall outside the six markets, CPI and payroll targets.
- Three ask about Brent; the desk's six-market oil forecast is WTI.
- Two ask about BTC. Their complete resolution contracts and underlying API
  question IDs were not exposed by the public listing. The retained current desk
  versions also postdate the October questions and have different thresholds/horizons.

The source inventory keeps every admitted probability, target component, original
reference/cutoff, source pointer and SHA256 beside those outcomes. A quote time,
registration time or data cutoff is not used to backdate a later source version.
The full answers and binary source snapshot are retained locally under
`A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc428-external-score-pilot`.
The raw platform question list and full inputs are excluded from the public delivery.
The event inventory contains only Main's own estimates and target/band definitions;
raw consensus, prediction-market data, execution and outcome rows are not compiled
into comments or requests.

## Implementation and validation

[The consumer](../../../live_contentops/metaculus_forecast_v1.py) matches the exact
instrument, measure, unit, interval, resolver and conditioning, keeps post and
question IDs distinct, supports binary, numeric CDF and multiple-choice bodies,
and compiles the documented atomic forecast/private-comment API request. It
does not estimate a distribution, fit a CDF to a point, complement a probability,
or reuse a conditional trading probability as an unconditional price forecast.

The [CLI](../../../scripts/run_metaculus_dry_run.py) reads Main's public output
directly. Its CC-428 command has no credentials, network client or send switch;
the backlog expressly requires a dry run. Later live API dispatch belongs to the
existing sole publication owner after the account/terms step, not a new publisher.

```powershell
python scripts/run_metaculus_dry_run.py --questions 'A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc428-external-score-pilot\round-questions.json' --plan-export 'A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc428-external-score-pilot\inputs\plan-status.public.json.gz' --event-matrix 'A:\Capital Chronicle\ResearchRuns\main-event-forecast-scores\bundles\US_CPI_20261110\event-scenario-matrices.json' --event-matrix 'A:\Capital Chronicle\ResearchRuns\main-event-forecast-scores\bundles\US_NFP_20261106\event-scenario-matrices.json' --output 'A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc428-external-score-pilot\dry-run.json'
```

The [focused tests](targeted-tests.xml) pass 22 cases. They exercise the actual CLI
consumer, source-number preservation, hash verification, question/group IDs,
deadline/look-ahead rejection, incompatible propositions/distributions, conflicting
inputs, duplicate questions and the existing public-text/link/time guards.
The first test output is retained separately; its two fixture errors were corrected.
The changed files also pass Ruff's `F` checks. No broad suite was run.

## Execution record

This branch was advanced to Publisher's operating HEAD
`4b7db97cebf926248c63dcac30c849ceee9c9706` before implementation. The fresh remote
default was older than the operating code. Using the operating base preserves the
current producer contracts and destination rules.

The observed launch command for PID 2964 configured `gpt-6.1-sol` with effort `max`:
`CONFIGURED_NOT_OBSERVED`. Process creation was 11 November 2026 16:32:56 GMT+7.
No new editorial model/API call, account, terms acceptance, outreach, publication,
schedule or desktop control was performed. Existing telemetry WIP remains outside
this item's commits. The source/rules review uses the no-red-tape and BrowserOS Neo
skills; read-only primary-source web results supplement individual sites that
returned a connection reset or HTTP 403.
