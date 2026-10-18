# ContentOps Three-Trigger Editorial Flow V1

Status: `IMPLEMENTED / TESTED / SYNTHETIC_SHADOW_ONLY / NO_RUNTIME_EFFECT`

## BEFORE / AFTER

**BEFORE:** Goal 15 supplied deterministic Main-contract bindings, DB-first resolution,
BrowserOS read-only receipts, and a Simple Gemini handoff, but there was no materialized
operational flow for the three current ContentOps trigger kinds.

**AFTER:** `live_contentops/three_trigger_editorial_flow_v1.py` now materializes:

1. scheduled latest-intelligence/headline research;
2. scheduled daily public-safe portfolio context;
3. Jim manual Codex Desktop research/content requests.

Foundation coverage/serving remains a supporting data plane and is not an operational trigger.
The flow creates no fifth routine window, scheduler, store, publisher, broker action, private
portfolio reader, credential/session reader, runtime activation, or public write.

## Authority and contract bindings

| Binding | Exact evidence |
| --- | --- |
| ContentOps base | `origin/master@a82c8be5e238c07b783ebb1461efb31ea45892a4` |
| Goal 15 adapter | `live_contentops/four_trigger_data_resolution_adapter_v1.py`, 55,691 bytes, SHA-256 `e0ee21442b275e8baf6baeab26ee62816732cc25daaed9b72a5df4d5527ae1ba` |
| Goal 15 schema | `schemas/contentops_four_trigger_data_resolution_adapter_v1.schema.json`, 1,436 bytes, SHA-256 `5b3c05c812918a36cb3d3947ac88d59f7d1a4ffbdf3fd68caef2637750779e16` |
| PR #84 design context | head `b818bcc16e9c4677a5ea47c439f3e86f1af124cc`, operating-model path, 7,871 bytes, SHA-256 `2b33888f2f87111bee6f560bdfd9a6fb99caf6ddcb1477115327ec076a2686db`, state `OPEN` |

The flow consumes the five Main-owned contract names through Goal 15 and keeps
`consumer_route=CONTENTOPS_EDITORIAL`:

- `CapitalChronicleTriggerRequestV1`;
- `CapitalChronicleDataNeedPlanV1`;
- `CapitalChronicleDataResolutionReceiptV1`;
- `CapitalChronicleAnalysisRunReceiptV1`;
- `CapitalChronicleServingCoverageProjectionV1`.

## Existing owners reused

- retained sidecar and published-memory readers;
- Goal 15 DB-first resolver and BrowserOS read-only recovery seam;
- `SIMPLE_GEMINI_RUNTIME` / `run_v1_simple_gemini_newsroom`;
- existing sourceability/dedupe, selector, writer and validator;
- `DurablePublicationCoordinator` as the only publication/readback owner;
- existing eight-derivative compiler and `UNKNOWN_WRITE = STOP -> READ BACK -> RECONCILE`.

Routine windows remain exactly `17:00`, `21:00`, `23:00`, and following `01:00`. Chrome CDP
`9222` remains ingestion-only; Edge CDP `9223` remains publication/media/readback.

## Flow behavior

### Latest intelligence

The newest retained headline is converted into one bounded question asking separately what the
report says, what establishes the underlying event, and what remains uncertain. Resolution is
DB-first and preserves contradictions, report truth, event truth, analysis, scenario and exact/
proxy state. The Simple handoff is prepared but never invoked by this slice.

### Portfolio-safe context

Only `PUBLIC_SAFE_CONTEXT_ONLY` is accepted. Private positions, balances, broker, order, fill,
credential, cookie and session fields are rejected before resolution. The result is an editorial
context packet or explicit `ABSTAIN`, `DEFERRED` or `DATA_BLOCKED`; it is never a portfolio
decision, broker action or private-state projection.

### Jim manual request

Only requester `Jim` is accepted. The result is a reviewable research packet containing source
identity, observed/retrieved/known-at clocks, rights, freshness, PIT, epistemic state,
exact/proxy, contradictions, missingness and next action. It has no publication authority.

Checkpoint envelopes retain the request and plan hashes, so latest-intelligence resume can rebuild
the request/plan even when the current headline input is empty. Terminal idempotency reuse accepts
both a raw request receipt and a complete flow receipt.

## Changed paths

| Path | Bytes | SHA-256 |
| --- | ---: | --- |
| `live_contentops/three_trigger_editorial_flow_v1.py` | 34,091 | `ca7938a716e7d89891395d5710d111fd8211671a5430bad315f202b5f39fa692` |
| `schemas/contentops_three_trigger_editorial_flow_v1.schema.json` | 1,895 | `3253a8ed2d720c7b7506a5318a249732614d4bd728927d722e3aec826145a09a` |
| `tests/fixtures/three_trigger_editorial_flow_cases_v1.json` | 5,683 | `549bc0d99e101a91d0a7c1d565a480d9eda391efb80613d1d4557f788b7e844c` |
| `tests/fixtures/three_trigger_editorial_flow_receipts_v1.json` | 151,812 | `de8b59896db312fe781ac6eb93312f51905868d46b6a08adf81e575efc8f533a` |
| `tests/test_three_trigger_editorial_flow_v1.py` | 18,091 | `aebedc202ba7ad01fc5c5d0410b3442732c0f2184c9ca16532ffb9ce09da7d44` |

The CodeGraph files are refreshed after this handoff update and their exact remote blob hashes
are recorded after commit/remote readback.

- refreshed `docs/codegraph/INDEX.md`, `docs/codegraph/V2_CONTEXT.md`, and `docs/codegraph/graph.json`

## Evidence

- focused three-trigger suite: `20 passed`;
- combined Goal 16 + Goal 15 adapter + BrowserOS + existing pipeline/newsroom suite: `150 passed`;
- Ruff check, Python compilation and `git diff --check`: PASS;
- CodeGraph generated inventory: 7,592 nodes / 14,337 edges;
- fixture receipts: 9 cases, all synthetic shadow-only;
- disposition counts: `READY_FOR_EDITORIAL_RESEARCH=2`, `EDITORIAL_CONTEXT_READY=2`,
  `REVIEW_READY=1`, `DRAFT_ONLY=1`, `PUBLISHABLE=1`, `ABSTAIN=1`, `DATA_BLOCKED=1`;
- derivative shadow manifest: 8/8 intents, all four epistemic layers preserved,
  `public_write_performed=false`, `unknown_write=false`.

The `PUBLISHABLE=1` fixture is gated by an injected deterministic validation result and still
has no public-write or publication authority. Current-real, runtime, forecast, portfolio,
broker and publication proof counts remain zero.

## Exact blockers

1. PR #84 remains open; its design document is bound above but is not treated as merged authority.
2. No live BrowserOS/CDP identity, scheduler execution, natural production window, Simple Gemini
   runtime call, publication, readback or external write was performed.
3. Main producer availability and semantic query admissibility remain Main-owned; synthetic
   receipts do not promote any numeric, forecast, portfolio or public authority.

## One exact next command

After PR #84 is merged, run the bounded shadow validation:

```powershell
python -m pytest -q tests/test_three_trigger_editorial_flow_v1.py tests/test_four_trigger_data_resolution_adapter_v1.py
```
