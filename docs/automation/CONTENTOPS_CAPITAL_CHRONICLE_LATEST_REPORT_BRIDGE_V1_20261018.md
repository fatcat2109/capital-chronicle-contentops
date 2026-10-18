# Goal 17 — latest Main report into ContentOps editorial input

Owning plan: [latest-report bridge](CONTENTOPS_CAPITAL_CHRONICLE_LATEST_REPORT_BRIDGE_V1.md).
Scope: ContentOps consumer only; implementation checkpoint, not a product-status owner.

## Current result

**The exact Main remote producer bytes are bound to an actual substantive editorial input.**
Main [PR #232](https://github.com/fatcat2109/Headline-Raw-data-json/pull/232), producer commit
`7c976da8688986bd95bbc536b6631b29183afb88`, contains XNGUSD v2 / CORRECTION and its frozen
v1 parent. All seven delivered files match their immutable Git blobs byte for byte. Main's
latest pointer selects v2. Report hash:
`89a4db7efe3b476d0ca5a1a5c8d5dfdc5af7f4170a63deed501bce718a836b47`.

The correction distinguishes the weekly injection average from the stock-level average;
source numbers and the 2026-10-18T13:03:41Z cutoff are unchanged. The earlier local v1
snapshot at ContentOps `def86891344937197639df8542510a005d3c452f` predates Main's final
closed-input/contagion projection and generated-time changes. It is historical, not the
current latest report. The final frozen parent and correction are retained separately under
`tests/fixtures/main_goal17_report/producer_v2/`; no old evidence was overwritten.

[Immutable producer readback](CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/immutable_producer_binding.json)
binds the exact Main source, schema, report/envelope, artifact revision and latest pointer.
[Actual v1-to-v2 execution](CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/actual_v2_correction_integration.json)
records the actual-clock temporary-store integration; its local execution provenance is
closed by the separate immutable readback, using identical bytes.
[Current XNGUSD editorial input](CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/XNGUSD_v2_editorial_input.json)
contains all seven claims and their evidence/section mappings in the existing Simple handoff.

| Actual observed outcome | Count |
| --- | ---: |
| Received events, including one exact redelivery | 3 |
| Consumed report versions / duplicate no-ops | 2 / 1 |
| Latest editorial inputs / claims / article sections | 1 / 7 / 7 |
| Planned derivative input intents | 8 |
| Drafts / writer calls / compiled derivatives / public writes | 0 / 0 / 0 / 0 |
| Missing claims / blocked results | 0 / 0 |

The parent was superseded before delivery and returned `REPORT_NOT_DELIVERABLE`. v2 reached
the existing writer prompt in `FOLLOW_UP_UPDATE` mode with its parent hash and affected
receipt lineage. An exact redelivery returned `DUPLICATE_NOOP`. No writer/model was invoked.
The eight planned input intents are not compiled derivatives or a qualified article.

## Reused owners and implementation

- Main remains sole wire/schema/hash and analytical owner. ContentOps validates exact UTF-8
  bytes, duplicate JSON keys, nonfinite values, schema/revision, seals, scope, clocks, claim
  hashes, supporting evidence, rights, query lineage and private-context exclusion. External
  schema references cannot trigger hidden network retrieval.
- The existing `ContentOpsDurableStore` artifact, work-item, outbox and lease APIs own
  last-seen/version/delivery state. No new database, table, migration, journal or scheduler.
  `internal:cc-report-receipt` and `internal:cc-report-editorial-input` use non-public statuses.
- Duplicates, older versions, equal-version/different-byte conflicts, correction/invalidation
  parent hashes and crash resume retain history. A newer received version prevents stale
  pending delivery. Each operation uses a unique lease owner, including concurrent attempts
  with the same receipt ID. No-material-change emits no new input/model intent.
- The brief carries exact claims, report/evidence hashes, horizons, proxy/basis-risk limits,
  uncertainty, what changed and watch conditions into existing Simple `capital_chronicle_context`.
  A report candidate joins supplied intake; published memory, existing selector/source/writer
  budgets and the sole publisher retain ownership. Input mapping is report -> claim -> evidence
  -> article section -> eight planned derivative input intents.
- Named research gaps reuse the DB-first resolver. `NeoNamedGapRecovery` connects the existing
  installed-Neo/MCP preflight and rendered-source recovery for one named `rendered_context` gap.
  This task made no Neo call. Browser context cannot grant historical PIT, public rights or
  Main analytical truth; new evidence requires a new Main report version.

## Verification and proof boundaries

All **41 current consumer tests passed** after adding the actual Main v2 correction sequence.
The earlier 39-consumer + 27-adapter + 36-Simple bundle passed **102 tests**; unchanged adapter
and Simple evidence was reused. Focused Ruff passed. Exact staged producer fixture bytes were
verified against their raw SHA-256 declarations; scoped binary attributes prevent Git newline
normalization. Existing coordinator recovery skipped the internal inputs with zero transport
calls and publication backlog. The earlier actual CLI import returned `ADMITTED`.

The report retains OBSERVED_SOURCE_FACT / CC_ANALYSIS / CONDITIONAL_SCENARIO distinctions,
EIA-original rights, 5/21/63-session scenarios, hold/invalidation conditions, null forecasts,
and retrieval-time PIT limitations. It does not establish a current CFD quote, market surprise,
order, executable economics or independent underlying-event confirmation. Source-page and
rights acquisition hashes inherit Main's sealed provenance; ContentOps did not reacquire them.

Earlier receipts remain dated evidence, not current-latest status:
[scaffold rejection](CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/scaffold_rejection.json),
[initial admitted local snapshot](CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/actual_local_integration.json),
[pre-correction local snapshot](CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/actual_final_run_integration.json),
and [earlier CLI readback](CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/cli_actual_readback.json).
The initial future-cutoff scaffold is a negative control, not another admitted real report.

## Repository delivery

Consumer [PR #87](https://github.com/fatcat2109/capital-chronicle-contentops/pull/87) contains
implementation, focused tests, exact producer fixtures, evidence and this owning handoff.
The final remote head and exact-head CI readback are recorded in its body after push.
CI run `39133046040` passed both jobs at `def86891344937197639df8542510a005d3c452f`;
that earlier result does not stand in for the later correction test or final PR head.

CodeGraph was regenerated with the existing generator at source commit
`055e6e8110fefb7128cf17cfc4a474d5a8f7b931`; its documented check returned `CODEGRAPH_CURRENT`.
Generated graph freshness is not operating or interoperability proof. Later fixture/evidence
binding changes do not change indexed source. No duplicate index was initialized.

No runtime, schedule, provider/model, database-owner, broker, publication, merge or deployment
action occurred. Local/remote integration, passing tests and an open PR do not prove those states.

## Discovery synchronization and bounded handoff

**Control Tower synchronization remains PENDING.** Its existing scoped non-database synchronizer
writes a separate shared checkout and requires selected Main/ContentOps PR heads and immutable
handoff blobs. This task owns ContentOps only. No broad collector or shared registry overwrite
was performed. This checkpoint is the durable discoverable input for its existing owner:

- Main producer: PR #232, exact source commit `7c976da8688986bd95bbc536b6631b29183afb88`,
  `docs/research/analysis_reporting/goal17/HANDOFF.md` and `export/contract-artifact-revision.json`.
- ContentOps consumer: PR #87, this checkpoint, `producer_v2/producer_binding.json` and
  `immutable_producer_binding.json`; select the final PR head from the verified PR readback.

The next separately owned action is that scoped discovery synchronization. Routine runtime,
writer execution, publication, merge and deployment remain outside this consumer delivery.
