# V1 9Router Research Model Ladder Owner Alignment

Task: `TASK_CONTENTOPS_V1_9ROUTER_RESEARCH_MODEL_LADDER_OWNER_ALIGNMENT_V1`

Classification:

`PASS_V1_9ROUTER_RESEARCH_LADDER_READY_FOR_CHATGPT_AUDIT_AND_NEW_LIVE_OPPORTUNITY`

## Starting authority and durable state

- fetched `origin/master`: `97cd13c914f1a48029cdc8529ab9ffd31637ec1d`;
- clean task branch/worktree: `codex/v1-9router-research-model-ladder-owner-alignment-v1`;
- latest manual opportunity before work:
  `operator-requested-desktop-go-20260817T072454Z-caef98d39bc5`, durably `REJECTED`,
  zero public write, `UNKNOWN_WRITE=0`;
- pending manual triggers: `0`;
- the interrupted attempted rerun created no additional durable work item or public write;
- two historical `READY` outbox rows from 2026-08-09 remain legacy/non-active state and were not
  mutated or dispatched by this correction.

No `GO` was run by this task.

## Routing correction

The prior current V1 grounded-research role inherited the five-route V1 quality pool:

1. `new/claude-fable-5`;
2. `new/gpt-5.6-sol-xhigh`;
3. `new/claude-opus-5`;
4. `vx/gemini-3.1-pro-preview(high)`;
5. `cx/gpt-5.6-sol(xhigh)`.

The exact owner-locked grounded-research ladder is now:

1. `cx/gpt-5.6-terra(high)`;
2. `vx/gemini-3.1-pro-preview(high)`;
3. `vx/gemini-3.5-flash(high)`.

The canonical seam is
`live_contentops.nine_router_ordered_model_router_v2.V1_GROUNDED_RESEARCH_MODEL_LADDER`, consumed
automatically by role `v1_grounded_researcher`. Temporary build-acceptance incident settings cannot
replace this owner-locked ladder. Article-writing, coordinator, final editorial-worker, schedule,
V2, publication, and Capital Chronicle authority were not changed.

The pre-existing research retry semantics are preserved:

- maximum total provider attempts: `6`;
- maximum fallback transitions: `4`;
- infrastructure same-model retries: `0`;
- one bounded structured-output repair globally;
- declared per-route attempt ceilings: `[2, 2, 2]`, with a second attempt reachable only through
  the existing single structured-repair path;
- no budget reset on model change or reconstruction.

Each router receipt now makes the safe audit fields explicit: provider/gateway `9router`, requested
route, one-based ladder position, global/model attempt, model retry number, fallback source/reason,
terminal selected route, output hash, and existing governed-input/prompt hashes. No credential,
header, cookie/session value, or sensitive base URL is recorded.

## Live zero-write capability proof

One harmless exact-nonce request was sent directly through the canonical 9Router adapter to each
route, with `max_tokens=32`, temperature `0`, and no research fact or article request.

| Position | Requested route | Result | Returned model | Latency | Response SHA-256 |
|---:|---|---|---|---:|---|
| 1 | `cx/gpt-5.6-terra(high)` | PASS | `gpt-5.6-terra` | 4.8861s | `be5af74916205dbfed66e48b19449cb7d1d5eeabcbcd289049e0d5d8835f0da8` |
| 2 | `vx/gemini-3.1-pro-preview(high)` | PASS | `gemini-3.1-pro-preview` | 5.6098s | `be5af74916205dbfed66e48b19449cb7d1d5eeabcbcd289049e0d5d8835f0da8` |
| 3 | `vx/gemini-3.5-flash(high)` | PASS | `gemini-3.5-flash` | 4.6786s | `be5af74916205dbfed66e48b19449cb7d1d5eeabcbcd289049e0d5d8835f0da8` |

All three responses exactly matched nonce
`CC_V1_9ROUTER_RESEARCH_LADDER_NONCE_20260817`. Full safe receipt:
`live_route_capability_proof_v1.json`.

## Deterministic validation

- primary success: no fallback;
- primary eligible provider failure: fallback to Gemini 3.1 Pro;
- primary plus Gemini 3.1 Pro eligible provider failure: fallback to Gemini 3.5 Flash;
- all three provider failures: truthful authorized-pool-exhausted terminal;
- factual/evidence rejection: terminal at the current route with no model shopping;
- no route outside the exact three-route research ladder is called;
- focused validation in clean pytest processes: router/research/provider `121 passed`,
  operator/newsroom `50 passed`, cost governor `10 passed`, CodeGraph contract `11 passed`
  (`192 passed` total);
- CodeGraph regeneration/check: `CODEGRAPH_CURRENT`.

One combined multi-file pytest process exposed pre-existing order-dependent process-state pollution
in a cost-governor test; the same complete focused groups all pass in clean processes, which matches
their production process boundaries. No runtime policy was weakened to hide that test-order caveat.

## Preserved boundaries

- Desktop coordinator: exact `gpt-5.6-sol / HIGH`;
- final article worker: exactly one fresh isolated `gpt-5.6-sol / XHIGH` only after governed
  evidence warrants an article;
- native V1 Scheduled Tasks: exactly four, all `PAUSED`, same names/recurrences/project,
  `gpt-5.6-sol / high`;
- article generation calls: `0`;
- XHIGH editorial-worker spawns: `0`;
- public writes/readbacks: `0`;
- `UNKNOWN_WRITE=0`;
- Capital Chronicle mutations: `0`;
- V2 product/runtime mutations: `0`.

## Exact next action

`CHATGPT_INDEPENDENTLY_AUDITS_REMOTE_RESEARCH_LADDER`
`→ FAST_FORWARD_ACCEPTED_BRANCH_TO_CURRENT_MASTER`
`→ SYNC_CANONICAL_CHECKOUT`
`→ VERIFY_THREE_9ROUTER_ROUTES_AND_NINE_SURFACE_READINESS`
`→ RUN_EXACTLY_ONE_NEW_HIGH_COORDINATOR_LIVE_GO`
`→ CHATGPT_AUDITS_REAL_XHIGH_ARTICLE_AND_ALL_NINE_PUBLIC_SURFACES`

The four Scheduled Tasks remain paused until that real publication canary receives Jim/ChatGPT
PASS.
