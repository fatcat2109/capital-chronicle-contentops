# Desktop-Primary Hybrid Codex V1 Newsroom Operator

Authority date: 2026-08-26
Status: `CURRENT_V1_CODEX_EXECUTION_CONTRACT / NATIVE_LLM_FIRST_SELECTED_STORY_PREPARE`

This document is the exact runtime contract that the four existing V1 Codex Desktop Automations
must read from current repository bytes. It owns execution detail only. Root `AGENTS.md`, current
V3 North Star/Master Plan, the authority/supersession map, and Jim's latest instruction remain
higher authority.

## 1. Current native execution order

Desktop standalone fresh-run Automations remain the primary routine V1 heavy-editorial brain.
The current native zero-write order is now:

```text
FDA-G / durable current intake + continuity
-> zero-model prepared candidate frontier
-> fresh Desktop gpt-5.6-sol / HIGH coordinator selects ONE useful story + canonical mode
-> deterministic hydration/evidence acquisition for ONLY that selected story
-> exact hash-bound native worker handoff with accepted evidence/context
-> one fresh isolated gpt-5.6-sol / HIGH final worker
-> deterministic validation
-> at most one same-worker HIGH revision from concrete validation deltas
-> exactly eight undispatched derivative intents when qualified
-> zero public write unless separately authorized later
```

This is `LLM-FIRST / VALIDATE-AFTER` at the editorial-decision boundary: HIGH story/angle selection
happens before evidence-ready/sourceability/capability perfection can veto the story. It does **not**
mean the final worker should waste quota broadly rediscovering evidence that deterministic selected-
story hydration can already provide. The accepted evidence packet is context, never factual or
publication authority by itself; final deterministic claim/source/CC/rights/identity gates remain
hard after the worker returns.

Do not restore the historical routine order:

```text
multi-candidate evidence-ready pool -> capability/sourceability perfection -> writer
```

and do not restore the historical 35-call / 10.2M-token discovery default.

## 2. Two-step native PREPARE handshake

Use only the public production runtime methods. Never call private supervisor methods.

### Step A — selection probe

Call:

```text
FinalDailyAppProductionRuntime.prepare_native_desktop_scheduled_opportunity(
  automation_id=<exact existing V1 Automation id>,
  now=<current governed time if explicitly supplied>
)
```

When a zero-model prepared frontier exists, the expected result is:

`classification = HIGH_SELECTION_REQUIRED`

with an exact `coordinator_selection_request` and persisted selection artifact.

At this point the runtime must have performed:

- zero newsroom-cycle invocations for the article path;
- zero evidence-acquisition requests;
- zero semantic-assignment provider calls;
- zero story-type semantic calls;
- zero public/provider writes;
- zero factual/numeric/evidence/CC/publication authority grants.

The coordinator request contains at most eight current prepared candidates, current bounded
continuity context where available, the exact canonical opportunity id, allowed canonical product
modes, and an exact `selection_request_logical_hash`.

The Desktop coordinator itself chooses exactly one useful non-filler current candidate and one of
the eight canonical article modes. It must return:

```text
schema_version = contentops.native_llm_first_selection_return.v1
canonical_opportunity_id = <exact probe value>
selection_request_logical_hash = <exact probe value>
selected_cluster_id = <one candidate from the probe>
article_mode = <one canonical product mode>
selection_rationale = <concise useful-reader rationale>
model = gpt-5.6-sol
reasoning_effort = HIGH
public_write_attempted = false
```

Selection grants no factual, evidence, numeric, Capital Chronicle, permission, rights, or
publication authority.

If Step A returns a governed no-candidate/blocker terminal result instead of
`HIGH_SELECTION_REQUIRED`, do not invent a selection and do not create a worker.

### Step B — selected-story deterministic hydration

Pass the exact selection back through the same public method:

```text
FinalDailyAppProductionRuntime.prepare_native_desktop_scheduled_opportunity(
  automation_id=<same exact id>,
  coordinator_selection=<exact Step-A return>,
  now=<current governed time if explicitly supplied>
)
```

The runtime verifies the persisted selection artifact/hash/expiry and then invokes the **existing
canonical PREPARE** on only the selected story:

- full `prepared_candidate_state` is removed from that canonical invocation so unused candidates
  cannot reopen a pre-writer multi-candidate evidence walk;
- `assignment_override` contains exactly the selected cluster/headline set;
- selected canonical article mode is preserved and marked LLM-first-selected;
- deterministic prepared `story_type_by_cluster` is reused, avoiding a hidden story-type model call;
- existing official/public evidence loaders, exact retrieval, story-scoped cache, request budgets,
  CC authority resolver, and handoff builder remain the sole evidence path;
- no second crawler/cache/store/scheduler/newsroom/publisher is created.

If selected-story hydration cannot establish the minimum trustworthy evidence required for the
selected article scope, record the exact candidate blocker. Candidate failure may continue to a
new governed candidate only through the bounded canonical opportunity semantics; never weaken hard
evidence gates and never manufacture filler.

If Step B reaches the article boundary it returns the existing exact hash-bound native worker
handoff (`HIGH_REQUIRED` / equivalent existing handoff classification). Only then create one fresh
isolated HIGH worker.

## 3. Worker contract

Final worker:

`gpt-5.6-sol / HIGH`, fresh and isolated.

Current ContentOps reasoning ceiling is permanently HIGH for coordinator, worker, revision, and
official SDK fallback. No XHIGH, ULTRA_HIGH, MAX, or effort above HIGH.

The worker receives only the bounded selected-story packet and exact governed-input hash. It has
zero factual, numeric, Capital Chronicle, permission, rights, gate, or public-write authority.

Use the accepted deterministic evidence packet first. Do not spend broad web/search turns merely
to rediscover already accepted source bytes. Read-only web expansion is permitted only when the
exact selected-story packet is genuinely insufficient for the warranted article scope and the
canonical bounded research/evidence policy allows it. Any newly cited material still requires
deterministic source-byte verification before qualification.

The worker must not invent or alter URLs, source handles, source IDs, evidence IDs, quotations,
numbers, or facts. Source-backed public copy uses only the exact supplied source markers/identity
contract. Never infer that a source omits a fact merely because a partial projection does not show
it.

At most one same-worker HIGH revision is allowed, and only for concrete deterministic validation
deltas. Representation-only title/dek/SEO/structured-data/alias defects are local normalization or
warnings where meaning is unchanged; do not spend another model turn on them.

## 4. COMPLETE

Use:

```text
FinalDailyAppProductionRuntime.complete_native_desktop_scheduled_opportunity(
  automation_id=<same exact id>,
  canonical_opportunity_id=<exact Step-A/Step-B opportunity id>,
  worker_return=<exact worker return>,
  coordinator_review_receipt=<exact hash-bound HIGH review receipt>,
  now=<current governed time if explicitly supplied>
)
```

COMPLETE reacquires the same durable work item and reuses the exact persisted intake/story/evidence/
viability bindings. It must not rerank or refetch the full candidate frontier merely because the
model conversation is fresh.

A semantic revision may return one same-worker revision request. A candidate-local hard failure may
continue according to the existing bounded candidate continuation contract. No legacy writer
fallback or provider shopping after a terminal semantic failure.

## 5. Four routine Automations only

Exactly four native V1 routine objects exist:

- `v1-newsroom-london-1700` — Monday-Friday 17:00 Bangkok
- `v1-newsroom-new-york-2100` — Monday-Friday 21:00 Bangkok
- `v1-newsroom-new-york-2300` — Monday-Friday 23:00 Bangkok
- `v1-newsroom-new-york-0100` — Tuesday-Saturday 01:00 Bangkok, belonging to the prior production day

Do not create a fifth routine Automation.

The four objects remain paused until current zero-write enablement/calendar-time proof is explicitly
advanced by the operator. Prompt/config normalization is not enablement. Enablement is not public-
write permission.

## 6. Output and throughput semantics

The build/proof throughput benchmark remains:

`4 QUALIFIED ZERO-PUBLIC-WRITE ARTICLES / 32 DERIVATIVE INTENTS per newsroom production day`.

It is telemetry/daily-output health evidence, not a prerequisite for one useful article and never a
per-window stop condition.

Final V1 target remains:

`5–8 useful PUBLISHED ARTICLES per newsroom production day`, without filler.

Candidate-level abstention is valid. Whole-day output below the active floor without an exact hard
external blocker is `DEGRADED_DAILY_OUTPUT_DEFICIT`.

Later existing windows may perform bounded catch-up work. Do not create extra routine windows to
chase the counter.

## 7. Hard gates preserved

Fail closed for:

- fabricated or unsupported material fact;
- materially unsupported causality;
- fake/unbound quotation;
- unsupported factual number;
- materially misleading stale event state;
- proprietary probability/forecast/scenario/regime/valuation/decision claim without exact Capital
  Chronicle publication authority;
- invalid or materially insufficient source/evidence binding;
- rights/permission failure;
- wrong destination/account or unauthorized public write;
- secret/session exposure;
- unresolved `UNKNOWN_WRITE`.

`UNKNOWN_WRITE = STOP RETRY -> READ BACK -> RECONCILE`.

In ZERO-WRITE/SHADOW_ONLY, destination readiness HOLD is publication diagnostics, not a story-
selection, hydration, or worker-admission veto. Zero media is valid.

## 8. Native primary vs SDK fallback

Native Desktop is the primary routine heavy-editorial owner. The official ChatGPT-authenticated
Codex App Server/SDK path is a bounded missed/failed-primary fallback, immediate direct path when
needed, and benchmark path. It is not a racing second scheduler.

Do not use the PR #29 direct SDK canary's approximately 993k accounted tokens / nine web-search
events as proof of native-primary steady-state economics. Native primary now selects first and then
reuses deterministic selected-story evidence before the final worker. Measure actual native
coordinator/worker/revision tokens, evidence/network reads, and web expansion in the host canary.

Accepted Desktop primary wins its canonical run identity. SDK fallback may start only after an exact
missed/failed/expired primary condition. Late Desktop completion after accepted fallback must be
suppressed; neither path may create duplicate articles or public objects.

## 9. Browser, publication, and safety boundaries

FDA-G remains continuous intake/state/runtime authority. The native selection seam is not a new
scheduler or state store.

Browser roles remain:

- Chrome `CapitalChronicleBot` CDP 9222 — ingestion only.
- Edge `contentops-social-main` CDP 9223 — publication/media/readback and explicitly authorized
  observation only.

No pyautogui, SendKeys, focus stealing, brittle UI selectors, private session/browser DB inspection,
cookie/token extraction, or unsupported internals.

No model, prompt, config, Automation, branch, or runtime composition grants public-write authority
by implication.

## 10. Current proof boundary

Accepted/reuse:

- canonical durable V1 runtime/store/supervisor/publication/readback foundations;
- PR #19 quota-efficient provider-resilient evidence discovery;
- PR #20 canonical single-article worker-return path;
- PR #29 HIGH-only direct LLM-first/validate-after single-article zero-write runtime proof;
- four existing paused native Automation objects and their prior supported host readback.

Current PR implementation may prove the **native selection-first -> selected-story hydration ->
existing worker handoff** mechanics through GitHub CI. That is not host/runtime acceptance.

Before enabling routine Automations, one narrow zero-write host canary must prove the new two-step
native PREPARE handshake on current real intake/store, actual HIGH coordinator/worker behavior,
exact economics, one qualified article plus eight undispatched derivative intents when a useful
candidate exists, public/provider writes `0`, and `UNKNOWN_WRITE=0`.

Do not merge implementation status into `V1_FINAL_PRODUCT_ACCEPTED`. Calendar-time unattended/
cold-start/fallback/late-result/duplicate-suppression proof and fresh V5 acceptance remain separate
later boundaries.
