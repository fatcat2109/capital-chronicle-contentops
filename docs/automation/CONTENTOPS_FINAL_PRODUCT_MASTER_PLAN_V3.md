# Capital Chronicle ContentOps — Final Product Master Plan V3

Authority date: 2026-08-29
Status: `CURRENT_ROOT_EXECUTION_MASTER_PLAN / V1_ACCEPTED / ACTIVATION`

North Star: `docs/automation/CONTENTOPS_FINAL_PRODUCT_NORTH_STAR_V3.md`
Current V1 activation authority: `docs/automation/CONTENTOPS_V1_POST_ACCEPTANCE_ACTIVATION_AUTHORITY_V1.md`
Authority map: `docs/automation/CONTENTOPS_CURRENT_AUTHORITY_AND_SUPERSESSION_MAP_V1.md`

## 0. Locked objective

Operate one coherent autonomous V1 growth newsroom at 5–8 useful published articles per production day, then continue one isolated V2 retention-native video lane without rebuilding accepted systems, weakening truth, or confusing missing current-host proof with missing implementation.

Current owner state:

- `V1_FINAL_PRODUCT_ACCEPTED = TRUE`;
- routine V1 public-write/readback authority is granted for the accepted V1 path;
- V2 public-write authority remains zero unless separately granted.

The repository merge commit `db0befb8ad44f1080c67fcb801e5470ce7852369` records the V1 grant.

Final V1 operating target:

`5–8 PUBLISHED ARTICLES per newsroom production day`

Historical zero-write throughput benchmark:

`4 QUALIFIED ZERO-PUBLIC-WRITE ARTICLES / 32 DERIVATIVE INTENTS per newsroom production day`

That benchmark remains telemetry/economics evidence only; it is not a renewed launch or acceptance gate.

A live day below target without an exact hard external blocker is `DEGRADED_DAILY_OUTPUT_DEFICIT`. Candidate-level abstention remains valid; filler and weaker evidence are forbidden.

## 1. Current V1 architecture

Routine V1 editorial ownership is `SIMPLE_GEMINI_RUNTIME`, not Desktop Automations.

Accepted per-opportunity editorial economics:

- <=32 current candidates after deterministic dedupe/sourceability ordering;
- one `vx/gemini-3.5-flash(high)` selector;
- one primary + <=2 useful fallbacks;
- shared <=6 deterministic source/provenance GETs;
- exact report-truth/event-truth epistemic state;
- one Flash writer;
- deterministic material-claim/source/epistemic validation;
- <=1 Flash revision without source expansion;
- <=3 logical Flash calls total;
- zero Codex runtime model calls;
- one qualified article plus exactly eight native derivative packages.

Official confirmation is not universal prerequisite. Exact reputable reports, approved newsroom-owned social reports, record-scoped canonical-X relay records, and explicit approved rumor records may support only the narrow propositions their evidence proves. High-harm handling remains stricter.

## 2. Accepted foundation — reuse, do not rebuild

### V1

`CURRENTLY_PROVEN_AND_REUSE`:

- current headline intake, published-memory/dedupe, update-chain and production-day foundations;
- Simple Gemini selection/writer/revision path and PR #37 Editorial Growth Edge;
- sourceability ordering, first-party/reputable-secondary retrieval donors, publisher pinning, exact epistemic-state adapter;
- canonical-X relay/explicit-rumor zero-GET branch under record-scoped provenance;
- native exactly-eight derivative compiler and X/Threads quality correction;
- four-window Simple scheduler mechanics and persistent exactly-one-process zero-write host proof;
- merged PR #38 post-acceptance authority/static-safety closure plus emergency-stop/process coverage for Simple;
- merged PR #39 single routine production-owner composition: current Final Daily App -> `SIMPLE_GEMINI_RUNTIME`, with Native Desktop/legacy rolling-X compatibility-only and non-routing;
- Simple-to-durable publication bridge through the existing coordinator contract: Substack/readback first and exactly-eight native derivative rematerialization only after a real canonical URL, with zero bridge model calls/GETs;
- durable V1 store, destination registry, canonical Substack-first publication coordinator, destination transports, strict readback/reconciliation, UNKNOWN-write recovery;
- real historical Italy one-Substack-plus-eight-derivatives canary with all nine reconciled and `UNKNOWN_WRITE=0`;
- V5 live read model/UI foundation.

Do not rebuild any of the above merely because current-host state must be revalidated.

### V2

Current V2 master keeps its existing free-form rendering/package/publication-control foundation. V2 is isolated from V1 runtime/store/browser/publication authority and has no public-write grant.

## 3. Historical proof that requires only current revalidation

`HISTORICALLY_PROVEN_CURRENT_REVALIDATION_ONLY`:

- live readiness/account/session state for Substack, Telegram, Discord, X, LinkedIn, Facebook Page, Instagram Business, Threads, and YouTube Community;
- publication profile/account identity on Edge CDP 9223;
- exact host state around the canonical production store and unresolved recovery/UNKNOWN-write backlog.

Historical success proves capability; it does not prove today's login/session/token/readiness state.

## 4. True current V1 implementation gap

The Simple-to-coordinator integration is implemented through the existing publication plan,
canonical-first coordinator, and native `finalize_intent` compiler seam. The remaining gap is:

1. **Published-vs-qualified accounting.** Editorial qualification remains useful telemetry, but live daily-output health/counting must be based on strictly reconciled published canonical articles. Publication failure, deferral, or ambiguity cannot count as a successful published article or prematurely satisfy the live deficit calculation.

Merged PR #38 already closes emergency-stop/process coverage. Merged PR #39 already closes single-owner composition. Do not reissue either as implementation work unless fresh code demonstrates regression.

No V1 transport, durable-store, native-packager, readback, or UNKNOWN-write recovery rebuild is authorized or needed.

## 5. Current host proof required before first new live write

After bridge/accounting implementation, read-only activation preflight must prove:

- production DB integrity/schema is healthy;
- no unresolved `UNKNOWN_WRITE`, ambiguous `DISPATCH_ATTEMPT_STARTED`, or recovery backlog blocks a new write;
- exactly one routine production owner/process;
- Edge `contentops-social-main` CDP 9223 is the publication/media/readback profile;
- exact current public account/destination identities are correct;
- all nine required destinations are freshly readiness-proven under existing contracts;
- no secret/session material is exposed during proof.

Chrome `CapitalChronicleBot` CDP 9222 remains ingestion-only.

## 6. Current activation roadmap

Use small bounded slices, not one giant activation task.

### Closed slice — repository authority/static safety + single owner

Merged PR #38 closed post-acceptance authority/static-safety, CodeGraph/static routing, and emergency-stop/process coverage for Simple. Merged PR #39 closed the current routine-owner composition. These are evidence, not current work.

### Slice A — Simple publication bridge

- build the smallest adapter from the accepted Simple qualified article/article manifest/native-preview artifacts into the existing `DurablePublicationCoordinator` plan contract;
- preserve canonical Substack-first publication/readback;
- obtain and validate the real canonical `/p/...` URL before derivative materialization;
- deterministically rematerialize exactly eight derivatives through the existing native compiler, preserving article identity, epistemic state, platform limits, and native quality invariants;
- no live write required for implementation validation.

### Slice B — published/reconciled production-day accounting

- preserve qualified-count telemetry for editorial economics/dedupe;
- add/reuse a canonical read projection that counts only strictly reconciled canonical Substack publications for live production-day health;
- make live deficit pacing/counting use reconciled published count rather than qualified count;
- do not create a second publication store or duplicate reconciliation authority;
- no live write required for implementation validation.

If repository-native planning proves Slice A and Slice B are inseparable without duplicating code or creating unsafe intermediate semantics, they may be implemented in one PR but must remain separately testable and evidenced. Otherwise keep them as separate small PRs.

### Slice C — current-host read-only activation preflight

- verify store/recovery/UNKNOWN state;
- verify current process ownership and scheduler state;
- verify Edge profile and exact account/destination readiness;
- no public write.

### Slice D — one live end-to-end V1 canary

Under the already-granted routine authority, publish exactly one fresh governed article through:

`Simple -> canonical Substack -> strict canonical readback -> exactly eight derivative destinations -> strict destination-local readback/reconciliation`.

Stop immediately on wrong identity, unresolved UNKNOWN write, public-object ambiguity, destructive mutation, or loss of epistemic state.

### Slice E — routine enablement

Only after Slice D is strictly reconciled, enable the four live windows toward 5–8 useful published articles/day. Do not add a fifth routine task and do not manufacture filler.

## 7. Definition of operationally ready V1

The owner product-acceptance decision is already true. Operational activation is ready when:

1. the Simple->publication bridge is current and tested;
2. live daily-output accounting counts strictly reconciled published canonical articles, not merely qualified zero-write articles;
3. current-host read-only preflight passes, including proof that merged single-owner/emergency-stop contracts still hold on the active host;
4. one fresh live article plus exactly eight derivatives strictly reconcile with `UNKNOWN_WRITE=0`;
5. the four routine windows may then run live toward the accepted 5–8/day target.

Do not create another V1 acceptance gate after these activation conditions are satisfied.

## 8. V2-after-V1

V2 remains isolated. Continue only current-compatible donor reconciliation, actual-media validation, unattended/recovery revalidation, and integrated qualification/observation/bounded-learning work. Never mutate/reset V1 runtime/store/browser/publication authority and never infer V2 public-write permission from V1 acceptance.

## 9. Hard stops

Stop on secret/session exposure, fabricated factual/Core Analyzer truth, wrong-account/out-of-scope public write, destructive production-state mutation, unresolved `UNKNOWN_WRITE`, ambiguous public-object identity, irreconcilable ref conflict, duplicate production owner, or accidental V2 authority expansion.

Substack is canonical. The eight V1 derivative destinations remain Telegram, Discord, X, LinkedIn, Facebook Page, Instagram Business, Threads, and YouTube Community.

Protected historical `v1.0` remains immutable at `6983bfb3ef300414b744f3f8f97ca81ff699348b`.
