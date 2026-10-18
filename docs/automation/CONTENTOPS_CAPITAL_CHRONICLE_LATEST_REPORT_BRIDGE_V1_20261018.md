# Goals 17–18 — latest Main report into the ContentOps editorial workspace

Owning plan: [latest-report bridge](CONTENTOPS_CAPITAL_CHRONICLE_LATEST_REPORT_BRIDGE_V1.md).
Scope: ContentOps consumer only; implementation checkpoint, not a product-status owner.

Current Goal 18 delivery is recorded in the continuation below. Earlier Goal 17 counts describe
the input-only checkpoint and are not the current article/preview counts.

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

## Goal 18 continuation — report to article and Daily App path

**The exact Main v2 report now runs through the existing durable Simple workspace and Daily App
read model.** The importer binds report/envelope identity across report id, version, parent,
supersession id, case, run, asset scope, source snapshot, clocks, public claim projection,
horizons, hold/invalidation projection, changed-claim scope and content eligibility. A resealed
envelope claiming version 102 against the sealed v2 body is `BLOCKED` with
`REPORT_BODY_BINDING_MISMATCH:report_version`; it cannot become latest. Evidence clocks cannot
run after the envelope cutoff or retrieval time, and a correction cannot change its parent hash
independently of the body.

The durable workspace stores immutable selector/source/writer stage requests and results in the
existing artifact/outbox APIs. Successful stages replay by their request hash; a crash after a
provider result but before local result recording fails closed and does not call the provider
again. The shared <=6 source ledger can restore consumed requests. Duplicate, out-of-order,
no-material-change, correction, invalidation and all-claims withdrawal keep durable identities.
Old article/preview identities are marked superseded or withdrawn when a newer report arrives.
A no-change report does not create a new article or model intent.

The Daily App now has a report workspace that shows Main origin/version/hash/cutoff, claims and
evidence locators, epistemic uncertainty, horizons and proxy/cost limits, correction lineage,
canonical draft, eight native preview cards, preview identity and named blockers. It explicitly
labels controlled replay, pending canonical links and unpublished state. Independent newsroom
intake remains in the same Simple candidate pool; a report candidate does not become the only
source.

### Actual bounded runs

- Main producer: PR #232 / commit `7c976da8688986bd95bbc536b6631b29183afb88`; XNGUSD v2,
  report hash `89a4db7efe3b476d0ca5a1a5c8d5dfdc5af7f4170a63deed501bce718a836b47`, envelope hash
  `5714d55767085221950384036113bf26c2f49e0ef96e2f49c2834060a4f1fc4f`.
- The real host marker `A:\Capital Chronicle\Runtime\ContentOps\control\llm_operator_pause.flag`
  remains present. The manual draft script consumed the v1 parent/v2 correction with published
  memory read-only, persisted one editorial input, and stopped before provider work: 0 fresh
  calls, 0 drafts, 0 previews, blocker `LLM_OPERATOR_PAUSED`. Receipt:
  [current manual paused Simple cycle](CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/actual_manual_paused_simple_cycle.json).
  It records one persisted input and the existing seven-article published corpus accessed with
  `SQLITE_MODE_RO_QUERY_ONLY`, with production-store bytes unchanged. The earlier
  `actual_paused_simple_cycle.json` is retained as pre-workspace history.
- An earlier injected, explicitly labelled replay of the same v2 report passed the existing Simple
  selector/source/validator and native compiler: **1 qualified zero-write draft and 8 native
  preview packages**. Preview state is `PREVIEW_ONLY_UNDISPATCHED`, canonical URL is pending and
  no public write occurred. Receipt and output hashes:
  [replay_simple_v2](CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/replay_simple_v2/).
  Its `envelope_sha256` field records the raw envelope file hash `061c0e15...`; the envelope's
  canonical self-seal is `5714d557...`. These are distinct hashes of the same pinned bytes.
  Current workspace acceptance and identities come from `goal18_controls` below.
- The isolated integrated acceptance ran v1 then v2 and a duplicate: 2 controlled drafts,
  16 controlled preview packages, 1 duplicate no-op, v2 remained latest, and a resealed v102
  envelope was blocked. It ran with `KILL_SWITCH` in a temporary store, 0 fresh provider calls,
  0 public writes and no production store. Evidence:
  [controlled receipt](CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/goal18_controls/receipt.json),
  [current result](CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/goal18_controls/result.json),
  [Daily App snapshot](CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/goal18_controls/snapshot.json).

### Visual acceptance

Neo readback of the isolated Daily App workspace was rendered and inspected at desktop and
mobile viewport sizes. The desktop frame shows report v2, correction, Main producer commit,
report hash, controlled-output label, draft availability and 8/8 unpublished previews. The
previews frame shows Telegram and Discord native cards with pending canonical-link text and
lineage controls. The mobile frame shows the same workspace responsively with no horizontal
content loss. Captures:

- [desktop workspace](CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/goal18_controls/visual/desktop.jpg)
- [preview cards](CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/goal18_controls/visual/previews.jpg)
- [mobile workspace](CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/goal18_controls/visual/mobile.jpg)

### Verification

- Consumer, workspace and Daily App backend tests: **97 passed**.
- Existing Simple newsroom and evidence resolver regressions: **44 passed**.
- UI focused tests: **27 passed** (`report_editorial_workspace`, `daily_app_console`,
  `daily_app_runtime_cockpit`).
- UI production build: `npm run build` passed.
- Focused Ruff passed; `git diff --check` passed.
- The Daily App snapshot remains read-only over the existing store. No scheduler, runtime,
  provider, browser account, database-owner, publisher, merge or deployment action occurred.

### Completion audit and repository handoff

| Requirement | Current proof |
| --- | --- |
| Exact pinned Main contract and envelope/body binding | Immutable producer readback and local machine-schema validation; consumer/workspace tests cover identity, version, parent, clocks, asset/public-claim/horizon/condition scope and resealed v102 poison. |
| Existing selector/source/writer/validator/compiler/store/memory owners | The adapter calls the existing production orchestrator and Simple runner; immutable stages use existing artifacts/outbox/lease APIs. The manual receipt proves read-only published memory and pause before provider. |
| Correction/invalidation, including no claims remaining | Consumer lifecycle tests plus the integrated workspace test preserve affected article/preview identities, suppress obsolete current copy and expose `CLAIMS_WITHDRAWN`. |
| Duplicate/out-of-order/no-change/crash resume | Focused controls prove no-op behavior, frozen input reuse, successful model/source stage reuse after compiler failure and a named fail-closed blocker for an unrecorded writer return. |
| Durable UI identity and current blocker | Final regressions select the newest blocked return regardless of input row order and prevent another report with the same version from supplying the current input; legacy Goal 17 lineage remains readable. |
| One current qualified controlled article and eight native previews | `goal18_controls/result.json` and `snapshot.json` agree on current article/preview identities; `receipt.json` separately records 2 historical controlled drafts / 16 compiled packages, 0 fresh calls and 0 public writes. |
| Actual rendered UI | The desktop, preview and mobile captures above were inspected. The final projection-only changes do not change that rendered layout or the accepted control's content. |
| Scoped remote delivery and exact-head CI | Implementation commit `4bd32e7f` plus generated CodeGraph commit `de069f9b`; exact-head run [39142221752](https://github.com/fatcat2109/capital-chronicle-contentops/actions/runs/39142221752) passed both jobs. Final audit fixes and final head/CI readback are recorded in PR #87 after push. |

The local UI build had emitted four ignored config `.js`/`.d.ts` files that affected the
filesystem-based graph scan. Those task-generated files were moved intact to the temporary
`goal18-generated-ui-config-backup-20261018` folder. CodeGraph is regenerated from the existing
generator with the clean source inventory; no duplicate index or generator policy change.

Control Tower scoped synchronization remains **PENDING its existing owner**, with the same
Main/ContentOps PR and immutable handoff inputs listed above. This is a discovery follow-up,
not permission to edit Main or the separate database/shared-registry owner.

### Exact remaining boundary

The implementation and controlled acceptance are complete. A fresh provider article remains
blocked by the existing operator pause marker and must not be bypassed. The next owner-controlled
operation is the existing `scripts/run_capital_chronicle_report_draft_v1.py` against the admitted
v2 receipt after that marker is cleared; it needs no new scheduler, store or publisher. Public
dispatch still requires real canonical Substack readback and the existing
`DurablePublicationCoordinator`.
