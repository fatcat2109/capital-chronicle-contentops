# Our analysis at the public level as model estimates (CC-262, Jim's decision 72 b)

Schema 1.4.0 (`CapitalChronicleDeskRecordExportV1_4.schema.json`) is 1.3.0 with the changes below. Every export now
declares 1.4.0; documents under 1.0.0 to 1.3.0 still validate against their own files. The schema file is generated
from 1.3.0 by a scripted transformation, so every other definition is unchanged.

## Two code-owned rights classes

- `CC_MODEL_ESTIMATE`: Capital Chronicle's computed outputs. On a public Field its use label is
  `PUBLIC_MODEL_ESTIMATE_NOT_ADVICE`, and every such Field carries `estimate_label` ("Capital Chronicle model estimate")
  and `notices` (decision 40's two lines: "Analysis, not financial advice." and "Capital Chronicle may hold positions in
  the markets it covers."). A shown, non-null estimate cites at least one source.
- `CITED_THIRD_PARTY_FACT`: one third-party figure cited with its source and date (a consensus figure). Public with
  attribution; its source row names the provider, the page and the date.

The exporter sets both classes itself (`_Sources.add_owned`); an input never declares them. The private-only classes are
unchanged, and the projection still drops any Field that cites a private-only source.

## What is public now, and what stays private

| Value | 1.4.0 |
|---|---|
| Surprise against consensus (`measures[].surprise_vs_expectation`) | public model estimate, against the cited figure; `surprise_basis` says which |
| One consensus figure per release (`event_cards[].consensus_citation`: NFP payrolls, CPI m/m, PPI m/m) | public cited fact with provider and date |
| The consensus table (`measures[].expectation`, `expectation_basis`) and the CC-068 rows | private (`MARKET_CONSENSUS_PRIVATE_ONLY`) |
| Main's frozen analysis (`asset_dossiers[].maintained_analysis`, a `ModelAnalysis` object) | public model estimates, with `source_run` (committee request or T2 screen, run id, frozen time, cutoff) |
| The committee's scenario set (`scenarios[]`, with `weight_percent` and `weight_label`) | public model estimates; the weights are uncalibrated heuristic shares, never relabelled as probabilities |
| The CC-265 quant card (`quant_card`: z-scores, ATR, betas and correlations, CC-011's release betas) | public model estimates with each metric's window, dates, method, inputs and missing cause |
| The modelled GEX regime and at most four key levels (`options_positioning.regime`, `key_levels`) on US500 and SPX | public model estimates; a newer case whose identification failed is named in `newer_case` |
| GEX aggregates and raw engine output (`net_gex`, `gross_gex`, `walls`, `flip`, `coverage`) | private (`OPTIONS_GEX_PRIVATE_ONLY`) |
| CC-266 anchors from the NY Fed Staff Nowcast and the FOMC SEP (`event_cards[].expectation_anchors`) | public cited official expectations (`CITED_THIRD_PARTY_FACT`, label "Cited official expectation", provider and release date); their terms allow commercial use with attribution |
| CC-266 anchors from the Atlanta Fed, Cleveland Fed and Philadelphia Fed | private (`OFFICIAL_SOURCE_CONTRACT_PENDING`): non-commercial terms, and the export has no free-only level (Ops Product, decision 74) |
| Open plans and the analysis' `plan_levels`, DEMO results, provenance | private |

A committee view reaches the public level only when it is a no-entry call (ABSTAIN, NO_TRADE, HOLD) or a conditional
call whose condition is the run's own structured watch: the price condition, timeframe and expiry, the direction
(bullish or bearish), the horizon in trading sessions and the invalidation level (the adverse-side levels and the
stop). A favourable-side cancel, such as "the move ran to the target without a retest", is entry management and stays
private. A WATCH, EXPRESS or OPEN without such a condition keeps its stance, direction and texts private.

Main's text is never rewritten. A text that states its run's profit target, an R multiple, a size or another DEMO
execution detail stays private under the same key (`DEMO_DERIVED_PRIVATE`), and the private `withheld` Field names the
cause (decision 40). An asset with no frozen analysis keeps `maintained_analysis` null with `NO_FROZEN_ANALYSIS_HELD`.

## The public-text check

`check_public_text` (and its copies in Codex Web and Publisher) blocks only:

- DEMO and execution identifiers, by name and by value: the DEMO logins, the broker server, account balance and
  margin, lot sizes, tickets, fills, a dollar P&L, order levels named as stop-loss or take-profit, R multiples and
  position sizes (the size tier, risk as a share of the account);
- bulk raw third-party data: four or more values copied from one private table or series (by dataset and provider),
  an option-chain row (a strike with its open interest or implied volatility), a prediction-market number;
- secrets (keys, tokens, private keys).

It passes a cited price, move or yield, a consensus figure with its source and date, and a Capital Chronicle model
level in any wording ("Positive gamma regime, flip at 6800", "Our forecast for CPI is 0.3%"), whatever private value
that number also equals. The word bans (consensus, forecast, beat, miss, surprise, gex, gamma, in line with), the
vendor-name rule and the private-number rule are gone.

## Inputs

`export_run(..., analysis_requests_root=<the committee's requests folder>, t2_runs_root=<the T2 runs folder>,
quant_cards=<CC-265 Tier1QuantCardV1 file>, gex_file=<CC-038/CC-240 InternalSpxGexCasesV1 file>,
expectation_anchors=<CC-266 official_expectation_anchors_v1 file>)`; the CLI takes the same options. An anchor sits
on an NFP, CPI or PPI card when its measure matches the card's (unemployment and payrolls for NFP, CPI and core CPI
for CPI) and its period covers the release's reference month (that month, its quarter or its year). Every other row,
and any row known after the export clock or without a published value, is left out and noted in
`producer.inputs` as `omission:anchor <anchor_id> <cause>`. Anchors never enter surprise arithmetic. Only records frozen and completed by the export clock are read: a committee request with its final
decision freeze, decision and Primary record; a T2 screen whose run ended. The regenerated fixture,
`tests/fixtures/desk_record_export_v1/desk_record_export_v1_4.fixture.json`, is the 5 Nov replay of these real inputs
on a copied state root, marked as a fixture with its sentinels.
