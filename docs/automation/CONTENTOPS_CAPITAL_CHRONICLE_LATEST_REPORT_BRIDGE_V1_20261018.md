# Goal 17 â€” latest Main report into ContentOps editorial input

Owning plan: [latest-report bridge](CONTENTOPS_CAPITAL_CHRONICLE_LATEST_REPORT_BRIDGE_V1.md).
Scope: ContentOps consumer only; implementation checkpoint, not a product-status owner.

## Current result

**Exact local Main output -> substantive editorial input is proven.** The replacement
P1 XNGUSD report passed the actual-clock importer with Main's two exact machine schemas:
7 admitted claims, 1 durable editorial input, 7 article-section mappings and 8 planned
input intents. Drafts, writer/model calls, compiled derivatives and public writes are 0.

[Actual local integration](CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/actual_local_integration.json),
[the substantive XNGUSD input](CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/XNGUSD_editorial_input.json)
and [the CLI readback](CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/cli_actual_readback.json)
record the exact boundaries. The report includes the EIA October 15 storage release,
CC's conditional balance interpretation, 5/21/63-session scenarios, hold and invalidation
conditions. It does not establish a current CFD price, a market surprise or an order.

Main producer source/schema/output are still local and uncommitted at this readback.
The producer base is `a4863f1638ef6d1523c2140721f9bd9b384f7e73`; exact local source SHA-256
is recorded in `tests/fixtures/main_goal17_report/producer_v1/producer_binding.json`.
**Immutable Main commit/remote binding remains pending.** Local integration is not a
merged/deployed/operating result.

The obsolete initial scaffold remains a separate negative control and actual rejection
receipt. It is not counted as a second admitted event.

## Reused and changed

- Main remains sole wire/schema/hash and analytical owner. ContentOps validates exact
  UTF-8 bytes, duplicate JSON keys, nonfinite values, seals, scope, clocks, claim hashes,
  supporting evidence, rights, query lineage and private-context exclusion.
- The existing `ContentOpsDurableStore` artifact, work-item, outbox and lease APIs own
  last-seen/version/delivery state. No schema migration, separate journal or new store.
  Internal destinations `internal:cc-report-receipt` and
  `internal:cc-report-editorial-input` use distinct non-public lifecycle statuses.
- Duplicate, older, equal-version/different-bytes, correction/invalidation parent and
  crash-resume controls retain history. A received newer eligible version prevents an
  older pending input from being delivered. Same receipt IDs cannot bind different bytes.
- A substantive editorial brief carries exact claim text, evidence IDs, report hashes,
  horizon/proxy limits, what changed, uncertainty and watch conditions into the existing
  Simple `capital_chronicle_context`. A report candidate joins the supplied current intake and retains the exact supporting
  source locators. Published memory and existing selector/source/writer budgets retain
  their role. The existing writer prompt consumes the report context.
- Each claim maps to an article section and eight **planned input intents**. These are
  not compiled derivatives or a qualified article. No model/writer was invoked.
- Named research gaps use the existing DB-first resolver. `NeoNamedGapRecovery` calls
  the existing installed-Neo/MCP preflight and rendered-source recovery, capped at one
  named `rendered_context` observation. Acquisition does not prove historical PIT,
  redistribution rights or Main analytical truth. New evidence requires a new Main
  version; a browser row cannot repair rights or overwrite an imported claim.

## Evidence boundary and counts

[Actual scaffold rejection](CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/scaffold_rejection.json)
binds the initial exact Main envelope and two referenced report bodies copied under
`tests/fixtures/main_goal17_report/`. Its producer base is
`a4863f1638ef6d1523c2140721f9bd9b384f7e73`; the producer source and outputs were uncommitted.
The envelope raw SHA-256 is
`99f9f3764b9a7503c3e25849067f0bd0d42197704e5dba01c8ed5e06534e6b4f`.
The receipt uses the actual UTC clock, not the scaffold's future 18:00 timestamp.

| Replacement Main output, actual observed outcome | Count |
| --- | ---: |
| Exact report events received / admitted | 1 / 1 |
| Admitted claims / article-section mappings | 7 / 7 |
| Editorial inputs / planned derivative input intents | 1 / 8 |
| Drafts / writer calls / compiled derivatives / public writes | 0 / 0 / 0 / 0 |
| Blocked replacement-report results | 0 |

The initial scaffold rejection is archived separately (1 received, 0 admitted, 1 blocked).
Synthetic mechanics controls intentionally skip the full Main schemas. Separate tests
consume exact Main schema/report/envelope bytes, exercise the default machine-schema
and producer-hash binding, and prepare an actual report-derived input through the
existing writer prompt without invoking its model.

The EIA source and rights hash declarations inherit Main's sealed provenance. ContentOps
verified report/evidence binding and schema/hash/rights/cutoff gates; it performed no new
independent browser capture or underlying-event confirmation. Main's source replay and
its BrowserOS acquisition remain distinct evidence owners.

Focused validation: the 39-control consumer + 27 adapter + 36 Simple bundle passed
(**102 total**). A subsequent same-receipt concurrency repair passed all **40 current
consumer controls**; unchanged adapter/Simple evidence remains applicable. Focused Ruff passed.
The repair gives each operation a unique lease owner, preventing concurrent receipt
re-entry from reacquiring another operation's lease.
Existing coordinator recovery skipped internal outbox inputs with zero transport calls
and zero publication backlog. The actual CLI exited successfully with `ADMITTED`.

## Finite remaining work

1. Bind the unchanged exact Main report/schema bytes to Main's final immutable producer
   commit and verify its remote branch. Do not replace real artifacts with synthetic ones.
2. Push the local integration update to existing [PR #87](https://github.com/fatcat2109/capital-chronicle-contentops/pull/87),
   refresh the scoped graph and read back the final remote head/CI.
3. Leave runtime, scheduling, model invocation, publisher, merge and deployment unchanged.

Exact-head CI run `39132137943` passed both jobs for the local-integration head
`fe4b0e7753883a1619becc6718d4f156ca7167d7`. It predates the final concurrency
repair; later head status must be read back separately.

Example read-only import after Main supplies the exact paths and binding:

```powershell
python -m live_contentops.capital_chronicle_latest_report_consumer_v1 `
  --envelope MAIN_ENVELOPE_JSON --reports MAIN_REPORT_JSON `
  --cutoff-utc ACTUAL_ADMITTED_UTC_CUTOFF `
  --envelope-schema MAIN_ENVELOPE_SCHEMA_JSON --report-schema MAIN_REPORT_SCHEMA_JSON `
  --producer-binding EXACT_PRODUCER_BINDING_JSON --output NEW_LOCAL_RECEIPT_JSON
```

No runtime, scheduler, provider/model, database-owner, broker, publication, merge or
deployment action occurred. The existing four windows, Simple budgets, publisher and
eight-derivative compiler retain their ownership.

## Discovery synchronization

The existing Control Tower was inspected as a dated locator. Its scoped synchronizer
requires final Main/ContentOps PR identities and immutable handoff blobs. Those are not
both available yet; **Control Tower synchronization is pending**. Do not overwrite its
shared dirty checkout or use a broad collector. This checkpoint is the discoverable
handoff for the existing Operator to run its scoped non-database synchronizer once
the exact PR revisions exist. CodeGraph outputs were refreshed and the documented check
returned `CODEGRAPH_CURRENT` at source commit `0c090e7dbb9c9beaf73fcbf4389fb7a087f21e1c`.
This is source-index freshness, not operating or interoperability proof.

## Exact next action

Read the final Main P1 producer commit and compare Git blob SHA-256 values against
`producer_v1/producer_binding.json`. If unchanged, append the immutable remote binding;
if changed, validate the new exact export and retain the compatibility delta in this
same slice. Then finish the scoped commit/push/PR readback. No new owner approval is
required for this already-authorized continuation.
