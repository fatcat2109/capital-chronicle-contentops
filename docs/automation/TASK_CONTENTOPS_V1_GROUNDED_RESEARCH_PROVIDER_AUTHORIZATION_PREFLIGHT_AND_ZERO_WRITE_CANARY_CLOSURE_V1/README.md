# Grounded Research Provider Authorization Preflight and Zero-Write Canary Closure

Classification: `BLOCKED_GROUNDED_RESEARCH_PROVIDER_AUTHORIZATION`

Exact next blocker: `TERRA_ROUTE_AUTHORIZATION_OR_OWNER_POLICY_DECISION_REQUIRED`

The CodeGraph final-head discrepancy is corrected without product-code changes. The bounded three-route provider preflight then found Terra temporarily rate-limited rather than unauthorized, while both Gemini routes were healthy and identity-verified. Under the existing router contract, Terra's `http_429_rate_limited` result was fallback-eligible, so one fresh zero-write canary was authorized without skipping Terra or changing policy.

The canary's first grounded-research invocation subsequently received `http_401_unauthorized` from Terra. The canonical router correctly treated that result as terminal and non-retryable: it did not advance to Gemini, did not walk another candidate, and did not create an article worker. No retry or policy change was attempted.

## Repository and CodeGraph

- Fresh `origin/master`: `8f6e4422d09fc9794c38ccc036ff1d1d9650034c`
- Starting branch HEAD: `b4f8624f540e21dc60e17a83a3eeb8a9db3a0e0d`
- Branch: `codex/v1-rolling-x-effective-capability-registry-alignment-canary-retry-v1`
- CodeGraph source HEAD before: `5e16cdd399eddb64c606fdc30b6521e1fd73b79d`
- CodeGraph source HEAD after regeneration: `b4f8624f540e21dc60e17a83a3eeb8a9db3a0e0d`
- CodeGraph source-tree digest: `d73f4af4f97b03540fc6c09edcdeebbcc90179654a5c02b21a5fded78618dfeb`
- CodeGraph inventory: 7,091 nodes and 13,321 edges
- `python scripts/generate_codex_context_index.py --check`: `CODEGRAPH_CURRENT`

Only `docs/codegraph/INDEX.md`, `docs/codegraph/V2_CONTEXT.md`, and `docs/codegraph/graph.json` changed for CodeGraph. Generator semantics and product source were not altered.

## Three-route preflight

The canonical `nine_router_preflight_v2.run_preflight` and provider adapter probed exactly once each, with credential presence only:

| Requested route | Health | Failure/status | Observed identity | Identity verified |
|---|---|---|---|---|
| `cx/gpt-5.6-terra(high)` | `TEMPORARILY_UNAVAILABLE` | `http_429_rate_limited` / `4xx` | unavailable | no |
| `vx/gemini-3.1-pro-preview(high)` | `HEALTHY` | none / `2xx` | `gemini-3.1-pro-preview` | yes |
| `vx/gemini-3.5-flash(high)` | `HEALTHY` | none / `2xx` | `gemini-3.5-flash` | yes |

The preflight made three provider calls and zero public research retrieval, article-writer, publication, browser, platform, or scheduler calls. `NINE_ROUTER_API_KEY` and `NINE_ROUTER_BASE_URL` were both reported only as `present_redacted`.

## Fresh zero-write canary

- Fresh cutoff: `2026-08-17T16:22:17.402782Z`
- Current rolling input: 310 headlines
- Prepared frontier: 12
- Deferred: 12
- Prepared state: `REBUILT_FROM_CANONICAL_FRONTIER_INPUTS`
- Attempted candidates: 1
- Unattempted after terminal provider stop: 11
- Grounded-research logical invocations: 1
- Grounded-research provider attempts: 1
- Models attempted: Terra only
- Public research retrieval requests: 3
- Retrieved candidates accepted before synthesis: 1
- Terminal result: `http_401_unauthorized / LLM_TERMINAL_NON_RETRYABLE_FAILURE`
- Registry mismatch: 0
- Source-family mismatch: 0
- Unsupported canonical story type: 0
- Native XHIGH workers: 0
- Legacy article writers: 0
- Mandatory semantic reviews: 0
- Article and package artifacts: none

The existing friction classifier recorded two `DATA_NOT_AVAILABLE`, one `FACTUAL_OR_RISK_BLOCK`, and three `SYSTEM_OR_BINDING_BLOCK` consequence rows for the absent evidence packet/capabilities. These are preserved verbatim in `blocker_taxonomy.json`; the actual terminal root cause is the separate provider-authorization blocker. The fixed registry-drift blockers remained zero.

## Safety and validation

The production-store SHA-256 remained `91DB00518B174CB80E298F7063C08AD1734537FEBCBC52FECC79216263F10909`. Durable editorial cutoff remained `2026-08-17T08:50:15.794759Z`, and continuity hash remained `ed1005c4de83e4490aeb69e719dcdd9f6ad61e29287089aa4230cb2d915175a4`.

Public writes, `UNKNOWN_WRITE`, publication-coordinator calls, outbox/publication intent, publication-browser navigation, Capital Chronicle mutation, V2 mutation, and Scheduled Task mutation were all zero. All four existing V1 tasks remain exactly present and `PAUSED` with unchanged hashes.

Focused validation passed 257 tests covering provider adapter/preflight, failure classification, the owner-locked research ladder, grounded research, effective registry and targeted evidence, same-opportunity walking, prepared frontier/continuity, HIGH-to-XHIGH routing, Institutional Edge, and zero-write packaging.

Operator/provider action is required to restore Terra authorization or for Jim to explicitly change owner policy. This task does not recommend weakening 401 semantics, skipping Terra, or starting at Gemini.
