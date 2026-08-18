# Capital Chronicle ContentOps — Root Repository Contract

Authority date: 2026-08-19

Status: `CURRENT_ROOT_AUTHORITY`

Repository: `fatcat2109/capital-chronicle-contentops`

## 1. Mandatory current read path

For any current ContentOps implementation, audit, task framing, or owner decision, read in this order:

1. `AGENTS.md`
2. `docs/codegraph/INDEX.md`
3. `docs/automation/CONTENTOPS_CURRENT_AUTHORITY_AND_SUPERSESSION_MAP_V1.md`
4. `docs/automation/CONTENTOPS_FINAL_PRODUCT_NORTH_STAR_V3.md`
5. `docs/automation/CONTENTOPS_FINAL_PRODUCT_MASTER_PLAN_V3.md`
6. `docs/codegraph/V1_CONTEXT.md` or `docs/codegraph/V2_CONTEXT.md` as appropriate
7. the current lane pointer
8. the nearest scoped `AGENTS.md`
9. exact implementation, tests, and evidence

Do not start from an old plan, handoff, task evidence folder, generated status file, sidecar/lab repository, or chat SHA.

`docs/codegraph/INDEX.md` is a discovery router, not an override. Compare its recorded source HEAD with freshly fetched remote `master`. If they differ, treat generated CodeGraph bytes as stale discovery aids only. Exact GitHub refs, commits, diffs, source, tests, and evidence outrank stale generated context.

## 2. GitHub and evidence authority

Before repo-state claims or task execution:

- fetch current remote `master` and relevant branch HEADs;
- read current bytes rather than trusting a pasted evidence packet;
- use commit ancestry/diffs to establish what is actually merged;
- preserve unrelated work;
- never claim PASS, final HEAD, remote parity, visual quality, media quality, or public-write success without the required evidence.

Authority order:

1. fetched GitHub refs, commits, diffs, and exact bytes;
2. committed code, tests, and accepted evidence;
3. this current authority spine and current lane pointers;
4. runtime/worker evidence;
5. historical docs, project sources, and chat.

Product authority order is Jim's latest explicit direction, then this root authority, then current owner overlays/pointers, then older plans/history.

Capital Chronicle/Core Analyzer analytical authority is external upstream product authority. ContentOps may consume only the exact upstream artifacts whose contract explicitly permits the intended ContentOps use; ContentOps repository detail can never widen that upstream permission.

## 3. Main execution framework

Current repository execution framework is `MAIN_CODEX` only.

- The primary Codex conversation/session owns repo reading, CodeGraph discovery, planning, implementation, self-debugging, focused validation, evidence collection, intentional staging, commit, and push.
- Separate owner-authorized `GPT-5.6 Sol / XHIGH` editorial or creative sessions/workers may be invoked only where current lane authority assigns consequential viewer-facing judgment.
- Authorized low-cost 9Router models remain available only for already-approved bounded filtering, research, classification, or similar non-authority roles.
- No alternate IDE/framework routing, fallback framework, or framework-specific model contract is current authority.
- Models never receive factual, numeric, Capital Chronicle/Core Analyzer, permission, credential, destination-identity, or public-write authority.

## 4. One final product architecture

Capital Chronicle and ContentOps are one company/product system with separate authority boundaries:

`Capital Chronicle/Core Analyzer intelligence and decision authority -> explicit publication-safe handoff + contextual discovery -> ContentOps intelligence fusion -> V1 publishing + V2 video/media -> observation -> bounded ContentOps learning -> audience/business utility`.

Capital Chronicle/Core Analyzer owns proprietary analytical and numeric truth, including calculations, scenarios, probabilities, forecasts, regimes, decision briefs, private decision/watch/abstain outputs, paper expressions, realized outcomes, and analytical error attribution.

ContentOps owns discovery, grounded external research, evidence/freshness/permission gates, faithful transformation of explicitly approved upstream publication material, writing, SEO, media, distribution, readback, observation, and bounded content learning.

ContentOps must never manufacture missing Capital Chronicle/Core Analyzer numbers, calculations, forecasts, probabilities, scenarios, regimes, decisions, positions, or proprietary conclusions. ContentOps audience learning may request or prioritize future analysis, but it may not mutate Core Analyzer truth, models, forecasts, decision records, paper records, or realized-outcome attribution.

## 5. Capital Chronicle / Core Analyzer data and publication boundary

The current read-only CC catalog/discovery foundation is reusable. Low database usage is not itself a product defect; the goal is useful relevance under the correct upstream authority class.

Maintain three distinct result classes:

1. **Context/discovery only** — arbitrary DuckDB rows, historical/entity/event/document matches, Step-1/headline catalyst context, sidecar/lab outputs, candidate snapshots, and other read-only discovery material. These may improve investigation and editorial questions but grant zero factual or numeric publication authority by themselves.
2. **Core Analyzer governed internal handoff** — point-in-time analyzer/database handoffs, validation packets, decision/forecast/scenario/paper/internal analytical outputs, candidate-only governed snapshots, and other upstream artifacts that may be internally authoritative for Capital Chronicle but do not explicitly grant ContentOps public reporting. These remain non-public in ContentOps unless a separate publication contract says otherwise.
3. **ContentOps publication-authorized CC packet** — an exact story-scoped upstream publication artifact, currently exemplified by `CapitalChroniclePublicationEvidencePacketV1.json`, or an explicit compatible successor, whose contract grants the intended consumer/use. Public numeric/analytical use requires explicit ContentOps consumer authorization, story-scoped permission, exact binding, required source health/freshness/lineage, no blocking conditions, and `llm_numeric_authority=false`.

The existence of a word such as `governed`, a validated Analyzer handoff, a point-in-time database, DQR metadata, or a model/run identity is **not** sufficient public authority.

The current code proves the intended separation:

- arbitrary catalog queries return context with `grants_factual_or_numeric_authority=false`;
- the Analyzer closed-loop handoff path remains publication-blocked/candidate context unless upstream publication permission exists;
- the story-scoped publication packet may authorize exact public claims without overriding unrelated/global DQR state;
- V2's existing governed video input requires a publication-authorized packet and exact numeric permission before consuming claims/time series.

Never turn arbitrary database rows, internal Analyzer outputs, candidate-only snapshots, stale surfaces, incompatible schemas, model assertions, or sidecar validation into publication authority.

## 6. Current root P0

The current root P0 is:

`CORE_ANALYZER_PUBLICATION_AUTHORITY_UTILIZATION + CC_CONTEXT_ACTIVATION + LATEST_WEB_SOURCE_REACHABILITY`.

The objective is not “query more databases.” It is:

1. consume the strongest relevant **publication-authorized** Capital Chronicle/Core Analyzer output when one exists and is exact for the story;
2. use bounded read-only CC context to improve investigation when useful, without authority promotion;
3. fix semantic activation so relevant context queries actually run when justified;
4. provide one lossless V1/V2 projection of publication-authorized chart/data material;
5. improve current accessible-source resolution;
6. expose telemetry that distinguishes authorized upstream use, context use, zero-use, blocked/degraded/candidate-only states, and exact reasons.

Database discovery/query counts are diagnostics, not product KPIs. Zero CC database queries can be the correct outcome when no relevant context is needed. No query-all behavior is authorized.

## 7. V1 — canonical newsroom/publication runtime

V1 remains the canonical Final Daily App/live newsroom-publication runtime.

Preserve:

- the canonical production orchestrator/pipeline and durable store;
- Substack-first canonical publication plus exactly eight V1 derivative destinations;
- exact destination identity and sufficient public-object identity;
- strict readback/reconciliation/recovery;
- `UNKNOWN_WRITE`: `STOP RETRY -> READ BACK -> RECONCILE`;
- current kill-switch/autonomy controls and idle/JIT browser policy;
- Chrome `CapitalChronicleBot` CDP 9222 for ingestion only;
- Edge `contentops-social-main` CDP 9223 for publication/media/readback and explicitly authorized observation only;
- LinkedIn official member API where current code/authority uses it;
- canonical V5 UI under `ui/contentops_v5/` and its current read model.

No-publication is valid. Zero images is valid. Filler is forbidden.

Final V1 acceptance still requires a fresh current real canary and subsequent unattended/cold-start proof; historical releases, zero-write fixtures, or self-reported worker PASS do not substitute for that evidence.

## 8. V2 — isolated retention-native media factory

V2 consumes qualified story/evidence authority but remains isolated from V1 runtime/store/browser/publication authority.

Preserve:

- `CONCRETE_FIRST_ABSTRACT_SECOND`;
- rights-safe real/contextual media and primary documents before decorative abstraction;
- publication-authorized/source-backed charts, maps, documents, and data as factual visual authority;
- generated media as illustrative only;
- real people represented with real rights-cleared documentary assets;
- Remotion as deterministic editing/render infrastructure, not a substitute for asset-rich editorial storytelling;
- owner/ChatGPT actual-media acceptance for consequential visual/audio quality.

A V2 chart/data adapter may project an upstream publication-authorized packet but may not regenerate, infer, repair, or upgrade the underlying numeric/analytical authority.

V2 currently has zero video public-write authority under this root authority. Any future provider upload or publication expansion requires exact owner scope, destination/account identity, readback/reconciliation, and a fresh safety gate.

Zero video production is valid when no qualified story exists.

## 9. Observation and learning

Observation may measure evidence/source health, publication-authorized CC use, contextual CC use, publication/readback, audience performance, search, conversion, video retention, reliability, and cost when the underlying observation is actually supported.

Learning may change ContentOps priority, timing recommendations, packaging, SEO, hook/asset choices, and bounded creative policy. It may never change facts, evidence permissions, Capital Chronicle/Core Analyzer analytical output, probabilities, scenarios, forecasts, numeric truth, decision/paper records, realized-outcome attribution, destination identity, safety gates, or public-write authority.

Unsupported observations are `UNAVAILABLE`/`UNKNOWN`, never fabricated zeroes. Degraded, proxy, candidate-only, stale, blocked, and missing states must remain visible rather than being smoothed into usable values.

## 10. Execution and change discipline

Prefer one heavy bounded end-to-end capability slice over ceremony or horizontal infrastructure.

Every implementation task must identify:

- user problem;
- capability/demo path;
- measurable utility delta;
- simplest viable approach;
- exact write/network/browser/publication scope;
- focused tests and one end-to-end smoke/demo;
- cost/runtime evidence where material;
- hard stop conditions;
- exact next blocker.

Stage explicit scoped paths only. Never use `git add .` or `git add -A`. Never force-push. Never push/merge `master` without explicit owner authorization.

## 11. Hard safety boundaries

Stop on:

- secret/session/token/cookie/private-key exposure;
- fabricated core facts or Capital Chronicle/Core Analyzer numeric/analytical truth;
- promotion of internal/candidate Analyzer material into public authority without an explicit publication-safe handoff;
- unauthorized or wrong-account public write;
- destructive production-store or upstream Capital Chronicle mutation;
- protected release/tag mutation;
- unresolved `UNKNOWN_WRITE` or public-object ambiguity;
- irreconcilable ref conflict;
- required credential/reauth/operator input unavailable for an explicitly authorized action.

Do not stop merely for historical noise, stale generated docs, unrelated dirty files, absent CI, pre-existing failures, or reversible mechanics.

The protected `v1.0` release commit remains `6983bfb3ef300414b744f3f8f97ca81ff699348b` and must not be rewritten or retargeted.

## 12. Visual/media acceptance

For UI, video, or audio acceptance, inspect the real rendered artifact. Tests and builder judgment prove mechanics, not viewer-facing quality.

A current authority/documentation change must not claim new visual or media acceptance unless the actual artifact was independently reviewed.
