# V6 25-Task / Roadmap Ledger

This ledger maps the V6 roadmap to current repo evidence. It is a roadmap/progress aid, not runtime authority over GitHub. Status values are conservative: fixture/manual evidence is not live/provider/API evidence.

## Status Vocabulary

- `complete`: implemented and accepted for its stated local/product scope.
- `complete_fixture_only`: complete using fixture/manual/operator-supplied evidence only.
- `complete_pre_live_no_send`: complete up to pre-live/dry-run/governance boundary with no live send.
- `partially_complete`: meaningful repo evidence exists, but lane is not complete.
- `pending`: no accepted implementation evidence found for the lane in this refresh.
- `deferred`: intentionally later/not active.
- `blocked_until_explicit_live_scope`: cannot proceed without exact live/provider/platform authorization.

## Ledger

| # | Task / Lane | Status | Current repo evidence and caveats |
|---:|---|---|---|
| 01 | V6 master plan authority | complete | Expanded in `current_v6_master_plan.md`; GitHub remote remains runtime authority. |
| 02 | Unified redacted credential capability matrix | complete | Redacted capability/readiness artifacts exist; no raw secret values are authority. |
| 03 | Platform universe and adapter taxonomy | partially_complete | Registry/docs and canonical V5 Command Center cover Substack, LinkedIn, X, Discord, Telegram, Facebook Page, Threads, Instagram, TikTok, and generic manual fallback. Fast Ship live adapters now exist for Discord, Telegram, Facebook Page, Threads, and Instagram; Facebook Page and Threads have live smoke evidence, Instagram remains media-input gated. |
| 04 | Canonical Substack article workflow | complete_fixture_only | Canonical article and Substack manual export/evidence packets exist locally. |
| 05 | AI research grounding lane | complete | Research/canonical article packet builders exist for local deterministic workflow. |
| 06 | SEO and editorial refinement lane | partially_complete | SEO/editorial packet docs exist; continue verifying per future task scope. |
| 07 | Platform-native variant generator | complete_fixture_only | Deterministic adapter output now drives full-platform variant rows in the V5 Command Center with stable payload hashes and manual dispatch gates. Live platform behavior remains gated. |
| 08 | Discord webhook/community drop lane | complete_pre_live_no_send | Discord dry-run/outbox/pre-live artifacts exist and are surfaced in the V5 Command Center bridge panel as redacted local-only status; no live send is claimed here. |
| 09 | Telegram remote operator lane | complete_fixture_only | Telegram checkpoint/manual lane evidence is surfaced in the V5 Command Center bridge panel as redacted local-only status; no bot/API send, token read, browser/CDP, or scheduler is claimed. |
| 10 | Approval/outbox/audit integration | complete_fixture_only | Payload hash, approval, outbox, bridge, manual/deferred distribution, audit, and final action-strip artifacts exist across lanes; V5 Command Center now displays deterministic manual audit rows, operator-supplied approve/hold/reject decision packets bound to adapter-built payload hashes, local outbox readiness reconciliation rows, Discord/Telegram local-only bridge rows, Facebook Page/Threads/Instagram/TikTok/Generic Manual local-only handoff rows, and a consolidated final operator action strip. Approval/readiness/bridge/manual-deferred/action-strip status is local/manual evidence only and does not authorize dispatch. |
| 11 | Public URL capture and reconciliation | complete_fixture_only | Substack and LinkedIn URL/audit imports are operator-supplied/manual only. |
| 12 | Community feedback intake | complete_fixture_only | Operator-supplied feedback intake packet exists locally; no live community activity, scrape, fetch, API, browser, or provider call is claimed. |
| 13 | LLM feedback summarizer | deferred | Current backlog summary uses deterministic tag grouping only; no LLM/provider call is claimed. |
| 14 | Backlog/next-idea generator | complete_fixture_only | Deterministic backlog candidates are generated from operator-supplied fixture feedback; recommendations remain review-only. |
| 15 | Media asset export lane | complete_fixture_only | V5 Command Center now splits media by source class from deterministic adapter output: news/current-event topics show grounded image candidate metadata with stable metadata hashes, while Capital Chronicle internal/report posts show built-in chart/card candidates with media hashes. No Google scraping, image download, URL fetch, rights verification, or rendered export is claimed. |
| 16 | V6 UI command surface | complete_fixture_only | Final V6 command center is integrated into canonical `ui/contentops_v5/` with local deterministic adapter model, inspector selectors, nav route, disabled live-action controls, full platform universe, source-aware media lanes, manual audit lane, and final operator action strip. |
| 17 | Operator review dashboard | partially_complete | V5 Approval Queue/Evidence Vault show fixture/manual evidence; no live controls authorized. |
| 18 | Credential setup workbench alignment | blocked_until_explicit_live_scope | Credential/env value reads are forbidden unless a future exact scope allows safe handling. |
| 19 | Platform registry alignment | partially_complete | Registry contract now marks Meta-family official API lanes live-capable under Fast Ship Mode when credential rows are present; future UI/reporting tasks should surface per-platform evidence and blocked reasons. |
| 20 | Adapter safety policies | partially_complete | Focused tests cover Meta adapter validation, dry-run, live request construction, failure shaping, env fallbacks, and unsupported edit outcomes. Platform actions remain governed by Fast Ship evidence and redacted status docs. |
| 21 | Browser/CDP supervised adapter boundary | complete_pre_live_no_send | X TASK 0087AD proved standard ContentOps profile CDP post/capture/reply with registry audit; reusable profile guard, pre-live post packet, GO-phrase gate, exact authorization/scope/execution packets, and registry reconciliation are complete as local supervised packet evidence. `TASK_CONTENTOPS_V6_X_CDP_REGISTRY_TO_OPERATOR_WORKFLOW_BATCH_V0` finishes the remaining registry idempotency/readback lane: exact execution rows append idempotently by natural key, registry rows audit locally without public fetch, operator_browser_lab has a read-only audit command, and V5 Command Center shows Registry Readback. Browser/CDP remains supervised and cannot read session/secret stores; no public URL fetch is claimed. |
| 22 | Manual fallback playbooks | complete_fixture_only | Substack/LinkedIn runbooks exist, and Facebook Page/Threads/Instagram/TikTok/Generic Manual manual/deferred distribution rows are hardened in the canonical V5 Command Center as local-only handoff/status evidence. |
| 23 | Evidence packet standardization | complete_fixture_only | Final release packet, acceptance record, red-team report, and browser-QA boundary are generated under `docs/automation/V6_FINAL_RELEASE/`; no live/API/provider evidence is claimed. |
| 24 | End-to-end dry-run acceptance | complete_fixture_only | Local V6 loop evidence covers idea → research packet → canonical article → Discord drop → variants → hash approval → blocked dispatch/audit/manual fallback → feedback → next idea. |
| 25 | Final product readiness review | complete_fixture_only | `PASS_FINAL_LOCAL_RELEASE_REVIEW`; release evidence writer is idempotent; Python release-readiness regression passed; canonical `ui/contentops_v5/` production build and Vitest suite passed after local dependency restore. |

## Accepted Lane Highlights

- Status docs/protocol exist in `docs/status/`.
- Canonical dashboard is `ui/contentops_v5/`.
- Substack manual publication evidence is complete as fixture/manual local evidence.
- LinkedIn manual publication evidence is complete as fixture/manual local evidence and accepted at `83c53fd3a39b377d9f74fa70cd8b6a5357689ecb` after this status repair.
- Discord pre-live docs may exist, but this ledger does not claim live send.
- Facebook Page and Threads live/API smoke evidence is committed for Fast Ship; Instagram Business is adapter-ready but smoke-blocked by missing public media URL/media ID; TikTok and generic manual fallback remain manual/deferred.
- X CDP pre-live post command, GO-phrase gate, exact execution outcome, registry reconciliation, and registry idempotency/readback audit are complete as local supervised/packet evidence; no repo-driven X click, API call, session read, or public URL fetch is claimed.
- Live/provider/platform execution is enabled under Fast Ship Mode for implemented lanes with evidence; unsupported or missing-input outcomes are recorded explicitly.

Recommended next lane: `TASK_CONTENTOPS_V6_UNIFIED_OPERATOR_REPORTING_CONSOLE_V0`. Implement unified operator execution logs, active queues visualizer, live-dispatch evidence summaries, and dashboard controls in the canonical V5 command center.

## How to Update This Ledger

1. Update this file only on roadmap/lane completion or execution-plan refresh.
2. Use conservative statuses and distinguish local/fixture/manual evidence from live/API/provider evidence.
3. Never hardcode a future next task as permanent truth.
4. Keep recommendations soft and timestamp/context dependent.
5. If a lane claims live/public/API verification, cite committed evidence and tests; otherwise mark it manual/fixture/pre-live.
