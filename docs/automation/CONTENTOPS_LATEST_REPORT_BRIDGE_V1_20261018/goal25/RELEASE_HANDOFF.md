# Goal25 — native roles and active Neo tool loop

Status: `IMPLEMENTED_AND_ISOLATED_NATIVE_PROOF / PAUSED_NOT_DEPLOYED`.
PR: [90](https://github.com/fatcat2109/capital-chronicle-contentops/pull/90).
Remote exact head and CI are recorded in `delivery.json` after push. This extends the existing
Goal20–24 checkpoint; prior evidence is unchanged. No self-merge, deployment, production
activation, new post or saved platform draft is part of this goal.

## What changed

- `NativeDesktopTurn` requests the assigned native model per role: Luna MAX filters X;
  Sol6.1 low chooses the story/angle/mode/audience question/evidence plan; Sol6.1 MAX writes
  canonical prose, SEO and article-bound native passages, with at most one same-writer repair.
  Actual invocation provenance is recorded separately from configured settings. Tokens/cost
  remain null because the native tools do not expose them.
- Filtering runs before the downstream <=32 ranking. It processes every X record in the
  frozen governed intake in bounded 24-record batches. Existing outbox rows hold immutable
  batch requests/returns and exact-record decisions. A completed batch interrupted before
  materialization resumes without a new semantic call. Exact unchanged records reuse their
  decisions across opportunities; corrections change only affected record hashes. Original
  correction/update identity survives intake and candidate dedupe. Deferred items are counted
  explicitly; they are not claimed rejected, processed into facts or silently published.
- Existing code still retrieves/parses/computes/seals evidence: <=3 admissions, <=6 shared
  source requests. Main public boundaries, claim/epistemic/rights validation, the exact
  institutional-edge packet and the eight-channel compiler remain the same owners.
- `NativeNeoExecutor` binds the existing outbox, coordinator, transport and readiness manager
  to the active Desktop conversation. Python emits requests; Desktop executes actual Neo MCP
  and submits a hash-bound observed return. No invented Python-to-MCP bridge or second
  publisher was added. Default missing executor is definite no-write. Unclaimed pending
  actions remain pending; a claimed write with no return becomes UNKNOWN and readback-only.
  Exact current identity is checked again at the action boundary, alongside pause/mode and
  payload/media hashes. Readiness proofs expire and get a new bounded probe epoch.
- The existing desk and same four target prompts/config expose the roles and native tool
  loop. Actual host objects and production pause were read back unchanged.

## Real native proof

See [native_proof.json](native_proof.json), [artifacts](artifacts/) and
[visual inspection](visual/inspection.json).

| Requirement | Observed result |
| --- | --- |
| Full bounded upstream scope | All **94** original X records in the complete retained 17 Oct 2026 02:00–05:02 UTC interval; **62 KEEP / 22 REJECT / 10 DEFER**, remaining unprocessed 0 |
| Downstream bound | <=32 candidate packet, actual admitted plan and shared source counts in receipt |
| Actual native roles | `/root/goal25_luna_filter`: gpt-6-luna/max; `/root/goal25_sol_light`: gpt-6.1-sol/low; `/root/goal25_sol_max_writer`: gpt-6.1-sol/max |
| Source | Dated FirstSquawk relay citing Financial Times about proposed Anthropic–Blackstone chip financing; report truth only, event UNCONFIRMED; **0/6** retrieval requests |
| Output | **1 qualified new article / 8 native packages**, conditional mechanism, countercase and specific missing terms/watch list; writer consumed exact packet hash |
| Review/handoff | Existing revision-bound KEEP review; same sole-coordinator plan prepared, **0 editorial-store dispatches** |
| Restart | Same outbox payloads and JSON artifact bytes, six semantic responses retained, no new source/model work |
| Media | Eight prior reviewed research cards retained/reused unchanged in the existing desk, no new render. New relay article has **0** media: no relevant verified existing asset; unrelated EIA imagery was not attached |
| Paused host | Four old App objects remain PAUSED with exact Goal24 config hashes; production pause hash unchanged |

The MAX writer hit an account usage limit after saving its complete response. The parent
submitted those exact saved bytes; it did not author a substitute. Deterministic validation
passed without a repair. One native invocation can emit several batch responses; six semantic
responses are not a claimed six paid/API calls. Token and dollar totals are unknown.

The retained interval is deliberately historical. No claim is made that the entire historical
sidecar archive, all 1,339 records in a seven-day diagnostic window, or today's empty 24-hour
intake was filtered by this proof. Routine filtering covers its full admissible frozen input.

## Actual Neo readback, no write

The isolated readback store imports exact existing intents/object identities through a
read-only production connection. It is test evidence, not a new production publication ledger.
`neo_native_returns.json` records actual MCP tool observations, return hashes and object IDs.
The native helper then resumes the existing coordinator's reconciliation.

| Existing destination/object | Actual result |
| --- | --- |
| Substack `213682262` | `RECONCILED_CONFIRMED`: exact canonical URL and supported public content |
| YouTube `UgkxRi-mk1C3VZgckZ7928rXhKiQucUEfMCS` | `RECONCILED_CONFIRMED`: exact Community URL/author/content |
| X `2094728314640617511` | `RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE`: public root exists; stored expected reply is not visible |
| X `2089681225246233006`, reply `2089688511884726540` | Actual root/reply IDs read; current text differs from package reconstructed by the retained artifact, so strict content PASS is withheld |

These objects belong to older already published work, not the new article. This is an actual
coordinator readback-loop proof, not a claim the new article was published or that every old
X thread is healthy. X root existence ends retry ambiguity without approving missing content.
Do not post/retry/edit to make this proof green. Media/hash and X thread-order mismatch paths,
missing executor, pause/mode, immutable return and claimed-write loss are controlled tests;
the actual publish-click path remains **UNEXERCISED**.

## Operation

Use the absolute `manual_binding.json` for this isolated editorial proof. `advance` emits an
exact pending stage; the assigned native role authors its JSON, `submit --stage <exact stage>`
seals it, then `advance` continues. A qualified result requires revision-bound review before
`handoff`; neither command dispatches. Preserve frozen requests on interruption.

For existing-object Neo readback, use `scripts/run_native_neo_executor.py --binding <absolute
neo_binding.json>` with `verify --surface ...` or `readback --dispatch-id ...`. On pending:

1. `begin --request-sha256 <request.request_sha256>` before the actual action.
2. In the active Desktop turn, execute the exact Neo request with fresh snapshot/identity and
   inspect public text, stable URLs/IDs, ordered replies and expected media.
3. `submit --request-sha256 ... --response <bound observed JSON>`.
4. Resume `readback`/`verify`, or the helper's readback-only `recover`.

The binding pins the actual native invocation, same store and operation. Tool-return fields
are documented in the module/CLI and exercised in `tests/test_native_neo_executor_v1.py`.
The helper rejects `allow_publish=true` and cannot make a platform post or save a draft.
Production composition can explicitly inject the same concrete executor; no executor is
silently made available to a background Python process.

## Verification and limits

Focused checks are in `verification.json`: native safety, >32 backlog/restart/correction,
coordinator, existing deterministic newsroom, operator/read model and UI. Real React component
render inspected desktop/all packages and mobile (430px viewport/430px scroll width).
Static stored preview is not deployment/server/runtime proof. Source cards retain their
previous rights/review/byte identity. No new evidence/rights grant was inferred.

The article is accepted for the isolated zero-write proof. Before any separate public release,
retain the historical source date in short social copies and polish repeated attribution,
`Watch: Watch...`, and the compiler's `Source-bound brief` Discord label. Neither SEO hygiene
nor local qualification proves ranking, audience response or 5–8/day production reliability.

Main wire schemas, accepted eight packages/15 propositions, canonical memory and public export
lineage remain unchanged. `continuity.json` verifies the prior owning store still has **6 KEEP /
2 HOLD**, all eight media hashes and exact Goal23 handoff bytes. The new isolated proof store
reconstructs the same research revisions as UNREVIEWED because prior review rows were not
copied; it is not a replacement of that accepted owning store. Its frozen model inputs and
proof remain intact. No Main/DB/builder message or receiver mutation occurred. Control
Tower/Main synchronization is **PENDING_OWNER_RECEIVER**; this durable discoverable checkpoint
is the handoff, not a synchronization-success claim. CodeGraph uses the existing generator.

Next release action is independent review of PR90 and its exact CI/source evidence, with the
four task configs and production pause still intact. Activation/deployment and any public
write remain separate decisions.
