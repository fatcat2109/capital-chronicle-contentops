# Desk-record export, schema v1 (CC-014)

Claude Ops, 30 Oct 2026. Schema: `CapitalChronicleDeskRecordExportV1.schema.json` (JSON Schema 2020-12). Reference projection and checks: `tools/product/desk_record_projection_v1.py`. Fixture: `tests/fixtures/desk_record_export_v1/desk_record_export_v1.fixture.json`. Tests: `tests/test_desk_record_export_schema_v1.py`.

The export is the one record every surface reads: the webapp (CC-045, CC-073), ContentOps (CC-043) and the scorecard. No surface runs its own analyzer. The deterministic export that writes it after every run is a separate Builder item (CC-014, due Thu 5 Nov). It must validate against this schema and pass the same checks on real fact packs.

## Fields

Every value a reader may show is a **Field**:

| Key | Meaning |
|---|---|
| `value` | A string, number, boolean or null. Only two Field kinds hold structured values, each with closed items: SEC filings (`FilingsField`) and series observations (`ObservationsField`). `null` only with `missing_cause`. |
| `rights_class` | Where the value comes from and what its rights allow. |
| `visibility` | `public` (free surfaces), `pro` (paid surfaces, once Jim opens them) or `private` (never leaves internal use). |
| `use_label` | How a shown value is labelled: attribution, the "analysis, not financial advice" notice, display-only widget, Pro, or private. |
| `source_ids` | The `sources[]` rows it comes from. Public and Pro official values cite at least one. |
| `unit`, `decimals` | Unit; display precision. Every official number carries `decimals`: show `1.0` as `1.0`, not `1`. |
| `missing_cause` | Why a value is null. Internal only. |

Ids, units, periods and record types are structure. They are never rendered as text.

Some positions accept only some visibilities, whatever the rights class says:

- Never public or Pro (private-only): open plans, arms, positions, orders, DEMO results, a decision's rationale, GEX, consensus and expectations, and surprises against them.
- Never public (Pro or private): maintained analysis, scenarios, pre-event branches and a decision's invalidation.

## Rules for readers

1. Validate against the schema file for the export's `schema_version`. Unknown keys fail.
2. Show nothing before `project(doc, {"public"})` (free surfaces) or `project(doc, {"public", "pro"})` (Pro surfaces) from `desk_record_projection_v1`. It keeps a Field only when its visibility is allowed and it cites no private-only source, removes `missing_cause`, drops any container that held Fields and keeps none (an open plan, the options block, a decision's DEMO and provenance blocks) and keeps only the sources that kept Fields cite. Import it, or port it with its tests; do not write your own.
3. Private-only rights classes (the schema forces `private`): `DEMO_DERIVED_PRIVATE`, `MARKET_CONSENSUS_PRIVATE_ONLY`, `OPTIONS_GEX_PRIVATE_ONLY`, `DERIVED_FROM_PRIVATE_ONLY`, `RIGHTS_MISSING`, `FRED_SOURCE_RIGHTS_BLOCKED`, `BROKER_PROXY_RAW_PRIVATE`, `INTERNAL_PROVENANCE`, `CODEX_DIGEST_INTERNAL` and `OFFICIAL_SOURCE_CONTRACT_PENDING`.
4. Public classes follow the code-owned contracts in `tools/product/subscriber_publication_v1.py` (BLS, BEA, Treasury, Fed Board, CFTC, SEC, broker-proxy interpretation). EIA data and company investor-relations facts have no contract there yet, so they are `OFFICIAL_SOURCE_CONTRACT_PENDING` and private. That is why NVDA's earnings date is private in the fixture. The export (Builder) adds reviewed contracts first, then a new schema version opens them.
5. Show numbers exactly as `value` with `decimals` and `unit`. Show each source's `attribution` and `disclaimer` with any public value that cites it.
6. Cite our records as `export_id#record_id`, adding `/measure_id`, `/metric_id`, `/update_id` or `/section_id` and then the Field key.
7. Build charts only from `data_series`. Their observations accept official classes only, cite at least one source, and run in ascending order from `window.start` to `window.end`. Each chart records its `series_id`, `series_code` and window, and shows the window: a series can be old (the fixture's Treasury series ends 27 Aug 2026, all the live root's governed file holds). Broker prices stay in the TradingView widget.
8. A `null` value renders as unavailable.
9. All clocks are UTC (`Z`). Show readers their local time. `check_clocks` holds: no record is known before a source it cites, and nothing is later than the export's `generated_at_utc`.

## Rules for the producer

Public and Pro text never states a consensus-relative judgement (in line, beat, miss, surprise, forecast), a GEX reading or a trading level, and never quotes a number from a private Field. The schema cannot see inside text. `check_public_text` catches the mechanical cases (terms, consensus-vendor names, private numbers with three or more significant digits). The export's test on real fact packs runs it together with `check_references` and `check_clocks`.

## The fixture

`fixture` is `true`. A build from it shows a "fixture, not current data" banner and is never published. Its private fields carry `fixture_sentinels` (`999.111`, `999.222`, `999.333`, `FIXTURE-SENTINEL-PRIVATE-7Q4`): a public build fails if any of them appears in its output. A real export carries no sentinels.

Real inputs, read-only:

- Q3 2026 Employment Cost Index: every value parsed from Table A of the BLS release as captured at 12:30:21.938 UTC on 30 Oct. The 10-quarter history comes from the BLS API file the dossier retrieved at 10:01:28 UTC.
- Tonight's arrival run: USDJPY and XAUUSD ABSTAIN, nothing armed.
- CC-068's October payrolls consensus (40K, myfxbook, private), commit `4177741d`.
- CC-038's SPX GEX aggregate for 23 Oct (private), commit `155eb0bd`. Walls and flip are null: `STRIKE_LEVEL_RESULTS_NOT_RETAINED`.
- CC-036's NVDA filings and next earnings date (17 Nov 22:00 UTC, private until a company-IR contract exists). NVDA's annual revenue is null on purpose: CC-036 picks a fiscal-2022 value as the latest (`LATEST_FISCAL_YEAR_FACT_UNRESOLVED_CC036`; CC-036 is reopened).
- Treasury 10-year par yields from the live root's governed curve file.
- The November release dates pinned in `tier1_event_window_pin_v1`.

Synthetic values: the sentinels and the open plan that carries them, and the calendar importance (our own label). The TradingView symbols (`NASDAQ:NVDA`, `SP:SPX`, `FX:USDJPY`, `OANDA:XAUUSD`) are display identifiers; CC-045 checks them against its symbol list.

## Versions

`schema_version` is fixed per schema file. Any change, even an added optional key, is a new version with its own schema file, because every object is closed. Removing or renaming a key, or loosening a visibility rule, is a new major version. Making any private-only class public needs counsel (CC-024) and Jim's message, then a new version.
