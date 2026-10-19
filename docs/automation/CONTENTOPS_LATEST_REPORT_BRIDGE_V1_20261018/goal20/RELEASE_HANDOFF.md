# Goal 20 â€” original evidence and evolving public report feed

Status: `IMPLEMENTED_LOCAL_PROOF_MAIN_IMMUTABLE_HANDOFF_PENDING`.
Owning checkpoint: [existing bridge handoff](../../CONTENTOPS_CAPITAL_CHRONICLE_LATEST_REPORT_BRIDGE_V1_20261018.md).
Base: merged PR87, master `45f9b0ebf209930e904085cf56bd4470a99c6501`.

## Delivered, with exact proof boundaries

| Required result | Current evidence |
| --- | --- |
| Independent useful evidence | Three retained propositions: EIA small-scale solar, EIA grid peaks, and BLS CPI. Exact source/policy bytes or separately identified BrowserOS rendered bytes, text spans, source identity, publication/capture/admission clocks and permission hashes are verified by `RetainedSourceResearch`. |
| Verified source permissions | A caller-supplied hostname, rights string or permission flags cannot authorize Main export. Two supported agency-authored text policies are verified from retained captures; photographs, trademarks and third-party works are excluded. Accepted Main public claims inherit only their exact durable Main contract. |
| Main context return | [Main readback](main_consumer_readback.json): existing Main adapter accepted 5 context-only projections: **3 independent, 2 Main-origin recirculations**. Zero model calls, DB writes or Main edits. Recirculation earns zero independent credit. |
| Incremental headline recovery | Existing outbox/cursor owner now keeps future records as hash-bound bookmarks, continues later useful records, recovers delayed arrivals after restart, and preserves local malformed/unknown-rights gaps. Permission-index revisions reopen bounded scanning. |
| Evolving public Main feed | `capital_chronicle_public_manifest_v1.py` reads the Main-owned `CapitalChroniclePublicReportExportManifestV1`: exact bytes/logical hashes, bounded parent chain, stable configured root, strict public paths, new versions, per-asset lineage, withdrawal and restart. v1.0/v1.1 pinned Git compatibility remains. |
| Producer/consumer proof | Three focused public-manifest tests exercise exact Main-produced **local compatibility control** bytes, incremental discovery without pointer edits, poisoned paths/bytes, parent/fork rejection, URN source identity, draft and withdrawal. The producer was still uncommitted at this proof; this is **not the requested immutable Main Goal20 handoff**. |
| Existing single newsroom | [Connected receipt](acceptance/receipt.json): **5 controlled drafts, 40 native previews, 4 source-backed media artifacts, 10 injected callbacks, 0 fresh provider calls, 0 public writes**. Three independent stories and two Main assets compete in the same existing Simple selection/writer/validator/compiler. The grid article uses two independently captured documents with separate source markers. Repeat opportunities add zero callbacks. |
| Substantive media | Existing source-backed renderer produces three actual source cards; its new bounded chart compiler renders six source-reported grid values with per-point quotes, periods, units and retained source/rights hashes. No forecast, trading result or private account field enters copy/media. |
| Daily App workspace | Existing report workspace shows source originality/inventory, conversion, controlled/provider distinction, dated freshness, source links, actual image previews, current pause, version/withdrawal and 8 native previews. [Workspace](acceptance/workspace.json), [desktop](visual/desktop.jpg), [mobile](visual/mobile.jpg), [native previews](visual/native-previews.jpg). All four rendered media were inspected directly. Mobile width 430 had scroll width 430; all four images loaded. |
| Focused validation | [108-test changed-owner set](focused_tests.txt), [12 focused seam tests](changed_seam_tests.txt), 5 UI tests, UI build, Ruff and compilation passed locally. These are scoped engineering proof. Exact remote CI is recorded in the PR after push. |

## Acquisition and authority limits

EIA documents were acquired through `BoundedOfficialPrimaryEvidenceLoader`; its existing locator
remains the discovery owner. BLS HTTP returned 403. The existing
`BrowserOSNeoRenderedSourceRecovery` recovered only the registered BLS release `pre` subtree;
its policy was captured separately. Rendered Markdown and canonical text have distinct hashes
and never masquerade as raw HTTP bytes. No login, click, storage/session read, model call or
public action was performed by acquisition.

`revision_at_utc` in this retained research adapter is the capture/admission clock. A publisher
revision clock was not independently established and is explicitly labelled. Historical official
observations do not become current market state. The chart compares source-reported peaks on
different dates; it establishes no causal attribution, forecast or market-price inference.

The existing reputable-attributed-report and canonical-X epistemic routes remain available in
Simple. Official confirmation is not a universal factual requirement. Unknown redistribution or
model-input rights still prohibit exporting that source body to Main; no X rights were invented.
The existing bulk CDP capture was neither replaced nor changed.

## Main manifest dependency â€” still open

Main owns the wire, schemas and export production. Its current `goal20/README.md` and local
`analysis_report_outbox_v1.py` supplied the matching contract. The local control fixture is
labelled `UNCOMMITTED_WORKTREE_BYTES`; it contains only public projection/envelope/schema
artifacts. This checkpoint does not claim that Main pushed a producer commit, supplied its
immutable compatibility example, or emitted new current-data report events.

Fresh exact local producer example readback found **9 schema errors** in its USOIL v2 v1.0
envelope: `SOURCE_FACT`, `CAUSAL_HYPOTHESIS`, `HORIZON_OUTLOOK` and explicit null horizons are
not accepted by the emitted v1.0 schema. All five handoff file hashes match Main's manifest;
this is a producer envelope/schema mismatch, not file corruption. The consumer correctly returns
`ENVELOPE_MAIN_SCHEMA_VALIDATION_FAILED`. [Exact dependency receipt](main_owner_example_readback.json).
Main must emit a schema-valid immutable example under its existing contract. ContentOps does not
rewrite Main claims, relax the schema, or manufacture a parent report to admit this example.

Required remaining handoff: Main's immutable producer revision + schema-valid example bytes/hashes + stable
export-root id and configured public root. Then consume that exact handoff, verify current
producer/consumer compatibility and record actual new manifest events. Until then Goal20 remains
active; `goal20_new_main_manifest_events=0` is intentional and truthful.

## Four existing windows and release

The existing Simple scheduler invokes `MainReportFeed.opportunity` once per existing slot. No
second scheduler, writer, store or publication owner was introduced. The four existing routine
windows remain 17:00, 21:00, 23:00 and following 01:00 Bangkok under the existing production day.

One reviewed configuration file, referenced by existing `CONTENTOPS_MAIN_REPORT_FEED_POINTER`,
may select the public manifest binding below after the Main handoff is accepted. `research_root`
points only to explicitly retained newsroom evidence. Configuration and runtime were not changed.

```json
{
  "schema_version": "contentops.main_public_export_binding.v1",
  "producer_repository": "https://github.com/fatcat2109/Headline-Raw-data-json",
  "export_root_id": "capital-chronicle-public-analysis-reports-v1",
  "public_export_root": "A:\\Capital Chronicle\\Runtime\\MainPublicReports",
  "research_root": "<reviewed retained research directory>"
}
```

The bounded next command after Main supplies that exact binding is:

```powershell
python scripts/run_capital_chronicle_intelligence_loop_v1.py --pointer <verified-main-public-binding.json> --store <new-isolated-proof.sqlite3> --output-dir <new-proof-output> --opportunity-id goal20-main-immutable-handoff --scan-only --research-root docs/automation/CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/goal20/retained_research
```

The manual command is draft/scan only and refuses the canonical production-store path. Existing
LLM pause remains in force. No deployment, self-merge, schedule start, provider spend, public post,
V2 expansion or transport migration occurred. The task-local hidden preview server was stopped;
its listener was verified absent. Main, Cockpit, MT5 and user terminal sessions were not changed.

Control Tower synchronization remains pending its separate owner. This existing owning checkpoint
and scoped PR are the discoverable handoff; no global refresh or shared database status credit is
claimed. CodeGraph is refreshed once after the implementation commit, with its source identity
recorded in the generated files.

## Real canonical sidecar scan

The bounded [manual scan receipt](manual/receipt.json) inspected 500 canonical sidecar rows; all 500 retained missing-permission gaps. The independent verified acquisition and exact Main facts continued: 5 permitted projections, comprising 3 independent and 2 recirculated. Existing seven-article published memory was read with SQLite query-only and remained unchanged. This scan invoked no model and started no schedule.

## Delivery

Implementation commit `9b57a3a4760012a0f5e9a25c88a62987e4f624d6`; CodeGraph source identity matches that commit. Scoped draft PR: [#88](https://github.com/fatcat2109/capital-chronicle-contentops/pull/88). Remote source head was verified after push. Exact-head CI and Main immutable-handoff readback remain in progress.
