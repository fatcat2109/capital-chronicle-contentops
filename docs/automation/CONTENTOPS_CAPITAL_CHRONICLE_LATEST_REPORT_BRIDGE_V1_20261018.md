# Goal 17 â€” latest Main report into ContentOps editorial input

Owning plan: [latest-report bridge](CONTENTOPS_CAPITAL_CHRONICLE_LATEST_REPORT_BRIDGE_V1.md).
Scope: ContentOps consumer only; implementation checkpoint, not a product-status owner.

## Current result

The consumer is implemented locally. Exact Main integration is **pending the replacement
P1 export**. The initial Main scaffold export was read as exact bytes and rejected; it
is not an admitted report, completed analysis, draft, or publication.

Main's live Builder is replacing that scaffold. Its source now declares
`asset-analysis-report-v1.0.0`, one `report_sha256` per envelope, all-claim-field hashing,
`supporting_evidence`, and explicit public-domain rights evidence. This consumer follows
that revision and rejects the obsolete scaffold shape. A local source declaration is
not an immutable producer commit or an exported machine schema.

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

| Actual observed outcome | Count |
| --- | ---: |
| Exact report events received | 1 |
| Admitted/consumed report events | 0 |
| Editorial inputs from real admitted claims | 0 |
| Drafts / writer calls / public writes | 0 / 0 / 0 |
| Blocked results | 1 |

Synthetic controls establish mechanics only. They explicitly disable absent Main
machine-schema enforcement; they are not evidence of upstream interoperability or
actual editorial work. The default importer requires both exact Main machine schemas
and a producer binding with their SHA-256 values and contract revision.

Focused validation: 35 consumer controls, 27 existing adapter regressions and
36 existing Simple newsroom regressions passed (98 total); focused Ruff passed.
The existing coordinator recovery also skipped both internal report outbox messages
with zero transport calls and zero publication backlog. Existing writer-prompt consumption is a deterministic
input test, not an actual Gemini invocation or final-copy validation.

## Finite remaining work

1. Read P1's finished report/envelope and exported Main schemas at its exact producer
   revision. Bind those bytes and hashes; do not invent a second schema.
2. Validate with the real clock and an admitted cutoff. If eligible, persist the actual
   report in a disposable existing store, prepare the substantive editorial input and
   record actual counts. If unavailable/blocked, retain the exact upstream blocker.
3. The scoped branch is pushed and [draft PR #87](https://github.com/fatcat2109/capital-chronicle-contentops/pull/87) is open.
   Remote head readback: `2da1587954d89397bb045149fd156d27e5ad7220`;
   base master remains `4ee9d64f451161a2dedc367f62f51569d7e56975`.
   Exact-head CI run `39131241598`: branch CodeGraph and deterministic validation both
   **PASS** for head `2da1587954d89397bb045149fd156d27e5ad7220`.
   This dated readback is not a claim about later commits or Main integration.

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

After Main P1 exports its replacement report and two machine schemas at an immutable
producer revision, copy the exact permitted bytes into a new fixture directory, bind
producer/schema hashes, and run the existing importer with the actual clock. Then
persist and prepare one admitted report input through `LatestReportDeliveryTracker`
and replace the pending integration counts with the actual readback. If any exact
rights/PIT/cutoff/claim gate fails, retain that blocker; do not edit Main output or
waive the gate. No further owner approval is required for this authorized continuation.
