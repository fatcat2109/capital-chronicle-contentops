# ContentOps Four-Trigger Data Resolution Adapter V1

Status: `IMPLEMENTED / TESTED / SHADOW_ONLY / NO_RUNTIME_EFFECT`

## Scope and authority boundary

Goal 15 adds the ContentOps consumer adapter for the shared Main-owned evidence-first contracts.
PR #81 remains open and is retained as the design target; the adapter binds to its exact head and
to the Main operating-model document without copying Main schemas or creating a second authority.

| Binding | Exact evidence |
| --- | --- |
| ContentOps base | `origin/master` at `3bcd41d9ec49d3ec217fe3865247a178ab827a7b` |
| Implementation commit | `c9e0db655e4df9e171b1147f84b64ac5c0168b38` |
| PR #81 design target | `dd03470ae06a2fce4f1c1358005f3854de904738`, `docs/automation/CONTENTOPS_FOUR_TRIGGER_DATA_RESOLUTION_AND_EDITORIAL_OPERATING_MODEL_V1.md`, 7,871 bytes, SHA-256 `2b33888f2f87111bee6f560bdfd9a6fb99caf6ddcb1477115327ec076a2686db` |
| Main operating model | `docs/strategy/ACTIVE_CONTEXT/CAPITAL_CHRONICLE_FOUR_TRIGGER_ANALYSIS_AND_DATA_OPERATING_MODEL_V1.md`, 15,569 bytes, SHA-256 `b1fc4c192b1865890a3f0ad2833b4f9b7cfb654eb7dee2306fdb48abbe2ee35a` |

Main contract names are consumed exactly:

- `CapitalChronicleTriggerRequestV1`
- `CapitalChronicleDataNeedPlanV1`
- `CapitalChronicleDataResolutionReceiptV1`
- `CapitalChronicleAnalysisRunReceiptV1`
- `CapitalChronicleServingCoverageProjectionV1`

The adapter always emits `consumer_route=CONTENTOPS_EDITORIAL`, `no_write=true`, and explicit
authority flags. It never creates a scheduler, store, publisher, broker action, private portfolio
reader, credential/session reader, or public-write path.

## BEFORE / AFTER

**BEFORE:** ContentOps had the accepted Simple Gemini, sidecar/published-memory, sourceability,
selector/writer/validator, canonical Substack, eight-derivative and readback owners, but no
deterministic consumer seam for the shared four-trigger request/plan/resolution contracts.

**AFTER:** `live_contentops/four_trigger_data_resolution_adapter_v1.py` now creates and hashes
requests/plans, deduplicates idempotency keys, resolves database-first in the locked order, records
BrowserOS read-only fallback receipts, preserves stale/rights/PIT/contradiction/missingness, binds
analysis and public-safe coverage projections, prepares a Simple Gemini handoff, and attaches the
four epistemic layers to all eight existing derivative intents.

## Existing owners reused

The adapter names and consumes these existing owners:

- `live_contentops.newsroom_assignment_scheduler_v1.load_rolling_x_headline_sidecars`;
- `live_contentops.published_corpus_read_model_v1.load_canonical_published_memory_read_only`;
- `live_contentops.v1_simple_gemini_newsroom_v1` for sourceability/dedupe, selector, writer and validator;
- `live_contentops._eight_platform_substack_first_pipeline_impl_v1.build_native_derivative_payloads`;
- `live_contentops.publication_coordinator_v1.DurablePublicationCoordinator` for canonical publication/readback.

Routine windows remain `17:00`, `21:00`, `23:00`, and following `01:00`; the adapter creates no fifth
window. Chrome CDP `9222` remains ingestion-only and Edge CDP `9223` remains publication/media/readback.
`UNKNOWN_WRITE` remains the existing stop -> read back -> reconcile contract.

## Changed paths and hashes

| Path | Bytes | SHA-256 |
| --- | ---: | --- |
| `live_contentops/four_trigger_data_resolution_adapter_v1.py` | 55,691 | `e0ee21442b275e8baf6baeab26ee62816732cc25daaed9b72a5df4d5527ae1ba` |
| `schemas/contentops_four_trigger_data_resolution_adapter_v1.schema.json` | 1,436 | `5b3c05c812918a36cb3d3947ac88d59f7d1a4ffbdf3fd68caef2637750779e16` |
| `tests/fixtures/four_trigger_data_resolution_cases_v1.json` | 8,780 | `a03f7c2b6097f5faa70e32e618cb491904640f392794063909496f5d75ff3b96` |
| `tests/fixtures/four_trigger_data_resolution_receipts_v1.json` | 33,215 | `e214bf78c0090d7a466d3995e1d5ad3d24e6c96148cb3499fa158ac0d4f88199` |
| `tests/test_four_trigger_data_resolution_adapter_v1.py` | 24,265 | `0255f47735a319970fd25efab08a22f216b845f23d8a1de2edf4d69e7e3a67ad` |
| `docs/codegraph/graph.json` | 5,746,291 | `e9b2a6a37bf30dd649a18e5ac993562377ef2b0e1d392a3f01b068ecc1d33690` |

The schema file identifies the ContentOps adapter and the five Main-owned contract names; it does
not redefine their field authority.

## Evidence and test counts

- Focused adapter suite: `27 passed`.
- Adapter plus BrowserOS, newsroom, derivative, publication, continuous-intelligence and Simple
  epistemic regression suite: `262 passed in 130.76s`.
- Ruff check, Ruff format check, Python compilation and `git diff --check`: PASS.
- CodeGraph generator: `CODEGRAPH_CURRENT`; refreshed inventory is 7,581 nodes and 14,303 edges.
- Fixture receipt counts (shadow fixtures only): `research-only=5`, `draft-only=0`,
  `publishable=0`, `DATA_BLOCKED=2` (one contradiction and one unavailable/missing path).
- BrowserOS fallback fixture records a visible evidence SHA-256, source identity, retrieval/observed/
  known-at clocks, public-read-only rights, read-only tool policy, fallback reason and missingness.
- Idempotent terminal checkpoint replay returns the same receipt hash without another source/recovery
  call. Eight derivative intents retain all four epistemic layers with `public_write_performed=false`.

## Exact gaps and blockers

1. PR #81 is still OPEN; current host runtime proof for BrowserOS, CDP identity/readiness and any
   natural scheduled request is not established by this repository slice.
2. The Main contract producers and semantic query/read-model availability remain Main-owned. Fixture
   rows and shadow receipts do not promote `CAPITAL_CHRONICLE_ANALYSIS`, proxy context, portfolio
   context, forecast, runtime, broker or public authority.
3. No live Simple Gemini invocation, publication, derivative dispatch, BrowserOS session, scheduler
   enablement or external write was performed.

## One exact next command

After PR #81 is merged and the owner selects a read-only shadow request, run:

```powershell
python -m pytest -q tests/test_four_trigger_data_resolution_adapter_v1.py tests/test_browser_rendered_source_recovery_v1.py
```

That command is the next bounded validation step; it does not enable runtime or public write.
