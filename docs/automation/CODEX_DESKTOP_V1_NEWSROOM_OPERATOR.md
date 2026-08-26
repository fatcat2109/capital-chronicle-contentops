# Desktop-Primary Hybrid Codex V1 Newsroom Operator

Authority date: 2026-08-26
Status: `CURRENT_V1_CODEX_EXECUTION_CONTRACT / NATIVE_LLM_FIRST_VALIDATE_AFTER_PREPARE_COMPLETE`

This document is the exact runtime contract that the four existing V1 Codex Desktop Automations
must read from current repository bytes. It owns execution detail only. Root `AGENTS.md`, current
V3 North Star/Master Plan, the authority/supersession map, and Jim's latest instruction remain
higher authority.

## 1. Current native execution order

Desktop standalone fresh-run Automations remain the primary routine V1 heavy-editorial brain.
The current native zero-write order is:

```text
FDA-G / durable current intake + continuity
-> zero-model prepared candidate frontier
-> one Desktop gpt-5.6-sol / HIGH coordinator chooses ONE primary useful story
   + OPTIONAL genuinely useful fallbacks from the same frontier, in preferred order
-> exact HIGH-admitted shortlist is hash-bound; the full frontier cannot reopen
-> one fresh isolated gpt-5.6-sol / HIGH worker for the primary
   -> worker performs read-only research and writes the article
   -> worker returns article + exact cited URLs + material claim/source bindings
-> deterministic validate-after retrieves ONLY the cited URLs and verifies source bytes,
   timestamp provenance, material claims, numbers, quotes, causality and required CC authority
-> if concrete deterministic deltas remain: at most ONE same-worker HIGH revision
-> if that candidate still hard-fails: one fresh HIGH worker may continue to the next candidate
   already admitted by the SAME coordinator turn
-> only a deterministically verified worker article re-enters canonical viability/article/package
-> exactly eight undispatched derivative intents when qualified
-> zero public write unless separately authorized later
```

This is literal `LLM-FIRST / VALIDATE-AFTER`. Ordinary pre-writer evidence-ready/sourceability/
capability perfection does not veto the writer. The worker may research with read-only web access;
its assertions and timestamps grant no factual authority. Deterministic source retrieval and hard
truth/CC/rights/identity gates run after generation and remain authoritative.

Do not restore either historical failure mode:

```text
full candidate pool -> evidence/sourceability perfection -> writer
```

or:

```text
HIGH chooses primary -> deterministic evidence gate blocks before worker -> no article attempt
```

Candidate failure also must not starve the whole opportunity when the same HIGH turn admitted a
genuinely useful fallback. Never widen beyond that HIGH-admitted plan without a new governed
opportunity and new HIGH selection.

## 2. Step A — zero-work HIGH selection probe

Use only the public production runtime API:

```text
FinalDailyAppProductionRuntime.prepare_native_desktop_scheduled_opportunity(
  automation_id=<exact existing V1 Automation id>,
  now=<governed time when explicitly supplied>
)
```

When a zero-model prepared frontier exists, expected result:

`classification = HIGH_SELECTION_REQUIRED`

with an exact `coordinator_selection_request` and persisted immutable selection artifact.

Before the coordinator returns, require:

- newsroom-cycle invocations for the article path = `0`;
- evidence-acquisition requests = `0`;
- semantic-assignment provider calls = `0`;
- story-type semantic calls = `0`;
- public/provider writes = `0`;
- factual/numeric/evidence/CC/publication authority grants = `0`.

The request contains at most eight current prepared candidates, bounded publication/update-chain
memory, canonical opportunity identity, canonical product modes, and an exact request logical hash.

The single HIGH coordinator chooses exactly one primary useful non-filler candidate and zero or more
optional fallbacks that are independently worth writing if an earlier candidate fails. Do not fill
the fallback list mechanically.

Return the exact selection contract:

```text
schema_version = contentops.native_llm_first_selection_return.v1
canonical_opportunity_id = <exact probe value>
selection_request_logical_hash = <exact probe value>
selected_cluster_id = <primary candidate from the probe>
article_mode = <canonical product mode>
selection_rationale = <concise reader-value rationale>
fallback_candidates = [
  {
    cluster_id = <candidate from same probe>,
    article_mode = <canonical product mode>,
    selection_rationale = <concise reader-value rationale>
  }, ...
]
model = gpt-5.6-sol
reasoning_effort = HIGH
public_write_attempted = false
```

Selection grants no factual, numeric, evidence, Capital Chronicle, permission, rights, or
publication authority.

## 3. Step B — exact worker handoff BEFORE evidence admission

Pass the exact coordinator selection back through the same public PREPARE method.

The runtime must:

1. validate the persisted request/hash/expiry and immutable opportunity-bound selection return;
2. construct one narrowed rolling input containing only HIGH-admitted headline IDs in the exact
   coordinator primary/fallback order;
3. bind the assignment override to that exact input hash;
4. bypass generic pre-assignment compaction when the assignment override is already exact-input
   bound, so compaction cannot reorder the HIGH primary/fallback plan;
5. persist the narrowed intake/assignment/story-routing/prevalidation checkpoint;
6. return an exact fresh isolated HIGH `editorial_worker_request` for candidate-plan index `0`;
7. perform **zero deterministic evidence retrieval, zero source-locator model calls and zero old
   evidence-capability admission before that worker**.

Expected ordering marker:

`HIGH_SELECTION_THEN_FRESH_HIGH_WORKER_THEN_DETERMINISTIC_VALIDATE_AFTER`

Expected worker handoff is hash-bound to the selected candidate governed context and uses:

- model `gpt-5.6-sol`;
- reasoning effort `HIGH`;
- fresh = `true`;
- isolated = `true`;
- resume_existing = `false`;
- public-write authority = zero.

The historical constant string `SPAWN_ONE_FRESH_ISOLATED_XHIGH_EDITORIAL_WORKER` may remain inside
legacy schema compatibility code. It is not current execution authority. Current native execution
must never request effort above HIGH.

## 4. External HIGH worker return

The worker researches and writes before deterministic source validation. It receives only the exact
bounded governed context for its candidate. Read-only web research is allowed. No public/provider
publication write is allowed.

The native return envelope is:

```text
schema_version = contentops.native_llm_first_external_worker_return.v1
governed_input_hash = <exact worker-request hash>
model = gpt-5.6-sol
reasoning_effort = HIGH
fresh = true
isolated = true
resume_existing = false
public_write_attempted = false
usage = <supported exposed usage only; optional>
duration_ms = <supported exposed duration only; optional>
output = {
  article = <strict PR29 article transport>,
  cited_sources = [
    {
      source_id,
      url,
      publisher,
      published_at_utc = <locator hint only; never authority>
    }
  ],
  material_claim_bindings = [
    {
      claim_id,
      claim_text = <verbatim public-copy claim>,
      claim_kind = FACT | NUMBER | QUOTE | CAUSALITY,
      source_id,
      support_excerpt = <short exact source excerpt>,
      attribution_required
    }
  ]
}
```

Use one to three exact allowed HTTPS pages when possible. Every material fact, number, quotation or
causal assertion must bind to an exact cited source. The worker must not invent URLs, timestamps,
quotes, source IDs or facts.

## 5. COMPLETE — deterministic validate-after

Resume through:

```text
FinalDailyAppProductionRuntime.complete_native_desktop_scheduled_opportunity(
  automation_id=<same exact id>,
  canonical_opportunity_id=<same opportunity id>,
  worker_return=<exact native external worker return>,
  coordinator_review_receipt=<deterministic NOT_REQUIRED marker or exact current supported receipt>,
  now=<governed time when explicitly supplied>
)
```

For the current native LLM-first path, COMPLETE does **not** need another coordinator model turn.
The `coordinator_review_receipt` parameter remains for public API compatibility; a deterministic
`model_turn_performed=false / decision=NOT_REQUIRED` marker is valid when the current implementation
only requires a mapping and does not consume semantic review authority.

COMPLETE first validates the external worker identity/hash, then reuses PR #29's accepted
post-generation validator to:

- GET only the worker-cited exact URLs through the bounded deterministic public retrieval path;
- derive authoritative publication time from publisher HTML metadata, HTTP headers, or exact
  URL-bound intake metadata—not the worker timestamp;
- require exact retrieved support for every declared material claim;
- reject invented/unreachable/unbound URLs, unsupported material claims and stale/invalid source
  time;
- cache accepted verified bytes so canonical evidence replay does not refetch them;
- feed only verified article/evidence into the existing canonical viability/article/package path.

No old pre-selection semantic checkpoints may be rebound to a different narrowed input universe.
The exact native assignment override owns shortlist identity; deterministic validation owns factual
support.

### One bounded same-worker revision

If deterministic validation returns concrete deltas on the first worker return, COMPLETE may persist:

`SAME_HIGH_WORKER_LLM_FIRST_REVISION_REQUIRED`

with an exact same-worker revision request. Resume the **same isolated HIGH worker** once:

- fresh = `false`;
- isolated = `true`;
- resume_existing = `true`;
- resume_same_isolated_worker = `true`;
- fresh_worker_creation = `false`;
- same governed-input hash;
- exact deterministic validation deltas only.

Maximum bounded revision count = `1`. No replacement worker for revision and no effort above HIGH.

### Candidate continuation

If the same candidate still fails after its one revision, COMPLETE may issue a new fresh HIGH worker
request only for the next candidate already admitted by the original HIGH coordinator plan. The next
candidate keeps its original plan order and canonical mode. No new coordinator turn and no full
frontier reopening.

If all admitted candidates exhaust after post-generation validation, terminalize truthfully. Do not
manufacture filler or weaken evidence.

## 6. Four routine Automations only

Exactly four native V1 routine objects exist:

- `v1-newsroom-london-1700` — Monday-Friday 17:00 Bangkok
- `v1-newsroom-new-york-2100` — Monday-Friday 21:00 Bangkok
- `v1-newsroom-new-york-2300` — Monday-Friday 23:00 Bangkok
- `v1-newsroom-new-york-0100` — Tuesday-Saturday 01:00 Bangkok, belonging to the prior production day

Do not create a fifth routine Automation.

The four objects remain paused until current zero-write enablement/calendar-time proof is advanced
by the operator. Prompt/config normalization is not enablement and never implies public-write
permission.

## 7. Output and throughput semantics

Build/proof health benchmark:

`4 QUALIFIED ZERO-PUBLIC-WRITE ARTICLES / 32 DERIVATIVE INTENTS per newsroom production day`.

Final V1 target:

`5–8 useful PUBLISHED ARTICLES per newsroom production day`, without filler.

Candidate-level abstention is valid. Whole-day output below the active floor without an exact hard
external blocker is `DEGRADED_DAILY_OUTPUT_DEFICIT`. Later existing windows may perform bounded
catch-up work; do not create extra routine windows merely to chase the counter.

## 8. Hard gates preserved

Fail closed for:

- fabricated or unsupported material fact;
- materially unsupported causality;
- fake/unbound quotation;
- unsupported factual number;
- materially misleading stale event state;
- proprietary probability/forecast/scenario/regime/valuation/decision claim without exact Capital
  Chronicle authority;
- invalid post-generation source/material-claim binding;
- rights/permission failure;
- wrong destination/account or unauthorized public write;
- secret/session exposure;
- unresolved `UNKNOWN_WRITE`.

`UNKNOWN_WRITE = STOP RETRY -> READ BACK -> RECONCILE`.

Zero media is valid. In ZERO-WRITE/SHADOW_ONLY, destination readiness is publication diagnostics,
not a writer-admission veto.

## 9. Native primary vs SDK fallback

Native Desktop is the primary routine heavy-editorial owner. PR #29's official
ChatGPT-authenticated Codex App Server/SDK path remains accepted fallback/benchmark capability. It
must not race the native primary as a second scheduler.

Do not use PR #29's approximately 993k accounted tokens / nine web-search events as proof of native
steady-state economics. Measure actual native coordinator/worker/revision turns, supported token
usage, deterministic source GETs, web expansion, candidate attempts and cache reuse.

Accepted native primary wins its canonical run identity. SDK fallback may start only after an exact
missed/failed/expired primary condition. Late duplicate completion must be suppressed.

## 10. Browser, publication and safety boundaries

FDA-G remains continuous intake/state/runtime authority. The native LLM-first seam is not a new
scheduler, store, crawler, evidence authority or publisher.

Browser roles remain:

- Chrome `CapitalChronicleBot` CDP 9222 — ingestion only.
- Edge `contentops-social-main` CDP 9223 — publication/media/readback and explicitly authorized
  observation only.

No pyautogui, SendKeys, focus stealing, brittle selectors, private session/browser DB inspection,
cookie/token extraction or unsupported internals.

No model, prompt, config, Automation, branch or runtime composition grants public-write authority by
implication.

## 11. Current proof boundary

Accepted/reuse:

- canonical durable V1 runtime/store/supervisor/publication/readback foundations;
- PR #19 provider-resilient discovery;
- PR #20 canonical article/package path;
- PR #29 HIGH-only direct LLM-first/validate-after single-article zero-write runtime proof;
- existing four paused native Automation objects and prior supported host readback.

PR #30 static code/CI may prove the native split-phase mechanics, exact shortlist ordering, external
worker handoff, post-generation validator reuse, one same-worker revision cap, bounded fallback and
zero-write invariants. It cannot prove the current Windows Codex Desktop host or article quality.

Before merge, one isolated zero-write host canary on the exact accepted PR head must prove:

1. Step A selection before evidence work;
2. Step B returns a fresh HIGH worker request with evidence/source-locator calls still `0`;
3. actual worker runs before deterministic cited-source retrieval;
4. COMPLETE verifies only worker-cited source material, preserving deterministic timestamp/claim
   authority;
5. max one same-worker HIGH revision, then only HIGH-admitted fallback continuation if needed;
6. one useful qualified article + exactly eight undispatched derivatives when a viable story exists;
7. public/provider writes `0`, `UNKNOWN_WRITE=0`;
8. supported native economics and actual prose/source bindings are inspected.

Do not merge PR #30, enable routine Automations, or expand public-write authority before that proof is
independently audited.
