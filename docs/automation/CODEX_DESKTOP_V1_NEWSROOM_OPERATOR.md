# Codex Desktop V1 Newsroom Operator

Authority date: 2026-08-21
Status: `CURRENT_V1_CODEX_EXECUTION_CONTRACT`

## 1. Critical truth boundary

This document defines the intended native Codex execution contract. It does **not** prove that Codex Automations currently exist on the host.

Repository configuration != host Automation truth.

Until actual supported Codex inventory proves otherwise, use:

`UNPROVEN_HOST_AUTOMATION_STATE`

Do not claim `READY`, `PAUSED`, `ENABLED`, or unattended execution merely because this file lists intended tasks.

`live_contentops/codex_desktop_newsroom_operator_v1.py` is continuity/routing support. It is not a scheduler, Desktop bridge, model bridge, or automatic host-task creator.

FDA-G currently has no proven direct native Codex invocation path.

## 2. Owner output contract

BUILD/PROOF:

`4 QUALIFIED ZERO-PUBLIC-WRITE ARTICLES minimum per newsroom production day`

FINAL V1:

`5–8 PUBLISHED ARTICLES per newsroom production day`

Candidate-level abstention remains valid. A whole production day below the active floor is degraded unless an exact hard external blocker is proven.

No filler. No truth/evidence/numeric/rights/permission weakening.

## 3. Production-day windows

Intended routine schedule:

| Group | Intended Automation | Bangkok recurrence |
|---|---|---|
| London | `V1 Newsroom — London 1700` | Monday–Friday 17:00 |
| New York | `V1 Newsroom — New York 2100` | Monday–Friday 21:00 |
| New York | `V1 Newsroom — New York 2300` | Monday–Friday 23:00 |
| New York | `V1 Newsroom — New York 0100` | Tuesday–Saturday 01:00 |

Timezone: `Asia/Bangkok`.

The 01:00 opportunity belongs to the prior newsroom production day. Production accounting must use deterministic `newsroom_production_day_id` semantics, not a naive local calendar date.

Do not create a fifth routine task merely to satisfy the floor.

## 4. Model roles

Routine coordinator:

`gpt-5.6-sol / HIGH`

Final editorial worker:

one fresh isolated `gpt-5.6-sol / XHIGH` worker for each warranted final canonical article.

Grounded research/evidence model policy remains current repo authority and grants zero factual/numeric/permission/public-write authority to model output.

HIGH owns runtime/state recovery, candidate preparation/ranking, evidence/research, readiness, deterministic validation, publication coordination, readback/reconciliation, observation scheduling, and terminal reporting.

HIGH must not silently author the final canonical article.

## 5. Daily deficit recovery contract

Old `one opportunity = at most one article` behavior is superseded where it prevents the active daily floor.

At each actual Codex Automation wake:

1. resolve current newsroom production day;
2. read qualified/published counts and remaining deficit;
3. recover/reconcile existing state and require `UNKNOWN_WRITE=0`;
4. load current candidate universe using durable cutoff/evaluated/update-chain memory;
5. walk strong candidates and applicable editorial modes;
6. for each candidate that reaches the article boundary, create one fresh isolated XHIGH worker;
7. persist each qualified article/package result;
8. continue only until current cumulative expected progress is restored, bounded candidate/evidence universe is exhausted, bounded cost/retry limits are reached, or a hard external blocker occurs;
9. persist deficit before/after and terminal reasons.

Do not loop forever or repeatedly research unchanged terminal candidates.

## 6. Editorial spectrum

Canonical modes:

- `BREAKING_BRIEF`
- `FOLLOW_UP_UPDATE`
- `STANDARD_NEWS_ANALYSIS`
- `CAPITAL_CHRONICLE_VIEW`
- `WHAT_THE_MARKET_IS_MISSING`
- `EVERGREEN_EXPLAINER`
- `DATA_OR_DOCUMENT_LENS`
- `WEEK_AHEAD_OR_WATCH`

Quiet-day lower-rung modes are required before treating the usable universe as exhausted.

## 7. Evidence/authority rules

Evidence burden follows claim ambition.

One exact current authentic official primary source may support a narrow attributed breaking fact. Broader causal, market, valuation, forecast, scenario, probability, regime, or proprietary numeric claims require stronger authority/evidence.

Context/discovery and governed internal Core Analyzer material are not publication permission.

Each XHIGH worker receives only bounded accepted evidence/authority/context and an exact governed-input hash. It receives zero factual, numeric, CC, permission, gate, or public-write authority.

No legacy final-writer fallback.

## 8. Intended reusable Automation prompt

Use current repository authority; do not embed stale branch SHAs.

```text
Read AGENTS.md, the current authority/supersession map, root V3 North Star/Master Plan, the current V1 pointer, and docs/automation/CODEX_DESKTOP_V1_NEWSROOM_OPERATOR.md. Operate as the native V1 coordinator on gpt-5.6-sol / HIGH. Resolve the current newsroom production day and active build/final output contract. Recover/reconcile current state, require UNKNOWN_WRITE=0, load fresh current intake/cutoff/update-chain memory, evaluate the candidate universe and full useful editorial spectrum, acquire claim-appropriate evidence, and pursue bounded deficit recovery rather than treating one candidate abstention as whole-day success. For every candidate that genuinely reaches the final-article boundary, create exactly one fresh isolated gpt-5.6-sol / XHIGH editorial worker with only the bounded governed packet and exact input hash; grant it zero factual/numeric/CC/permission/public-write authority. HIGH resumes deterministic validation and zero-write or authorized publication lifecycle after each return. Do not manufacture filler, weaken evidence, create a fifth routine task, invent host Automation state, or perform public writes without exact owner authority.
```

## 9. Actual Automation setup/inventory rule

Before claiming routine execution is available, prove on the installed Codex product/host:

- Automations supported yes/no;
- exact ContentOps Automations found;
- names/schedules/timezone;
- project/repo/worktree target;
- model/reasoning effort;
- prompt/thread identity;
- active/paused/absent state;
- unattended behavior where supported;
- ability of HIGH coordinator to create fresh isolated XHIGH workers.

If supported programmatic Automation management is unavailable, stop with exact owner UI setup instructions. Do not fake success in repo docs.

## 10. Material-event wake

FDA-G material-event detection/priority does not prove immediate Codex wake.

Until actual supported execution is demonstrated, classify:

`MATERIAL_EVENT_CODEX_WAKE_NOT_IMPLEMENTED`

Do not add a credential/access-token/API Codex bridge without a separate explicit owner grant.

## 11. Build/publication safety

Current build bridge proof remains `SHADOW_ONLY / ZERO PUBLIC WRITE` unless a separate exact canary grant is active.

Do not publish, create externally visible drafts, dispatch derivatives, inspect raw secrets/session data, mutate public account identity, reset production store, or blind-retry ambiguous writes.

## 12. Final acceptance of routine Codex execution

Routine Codex execution is accepted only when actual host evidence proves the Automation objects and at least one real zero-write Automation invocation reaches current FDA-G state and returns a truthful terminal result.

Automation invocation PASS and article qualification PASS are separate claims.
