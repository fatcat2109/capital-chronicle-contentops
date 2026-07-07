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
| 03 | Platform universe and adapter taxonomy | partially_complete | Registry/docs and canonical V5 Command Center cover Substack, LinkedIn, X, Discord, Telegram, Facebook Page, Threads, Instagram, TikTok, and generic manual fallback. Fast Ship live adapters were verified under E2E live run `v6_pipeline_3c19fed2b5df` for Substack, LinkedIn, X, Discord, Telegram, Facebook Page, and Threads; scoped retry `v6_pipeline_a2d260907953` verified Instagram without reposting prior successes. |
| 04 | Canonical Substack article workflow | complete | Live Substack publishing is verified under Fast Ship Mode. Scoped visual repair run `v6_pipeline_d49f6e14a856` published `https://capitalchronicle.substack.com/p/crude-awakenings-how-spiking-oil-13c`, uploaded 2 in-body visual slots, and public readback found 2 public images with order/placement status PASS. |
| 05 | AI research grounding lane | complete | Research/canonical article packet builders exist for local deterministic workflow. |
| 06 | SEO and editorial refinement lane | partially_complete | Final run `v6_pipeline_3c44a9855cc6` passed article gates with 2,009 words, 8 sections, source trail, numeric evidence, SEO metadata, and 2 visual slots. Provider-native drafts still needed source-backed repair, so native provider reliability remains the next hardening lane. |
| 07 | Platform-native variant generator | complete_fixture_only | Deterministic adapter output now drives full-platform variant rows in the V5 Command Center with stable payload hashes and manual dispatch gates. Live platform behavior remains gated. |
| 08 | Discord webhook/community drop lane | complete_pre_live_no_send | Discord dry-run/outbox/pre-live artifacts exist and are surfaced in the V5 Command Center bridge panel as redacted local-only status; no live send is claimed here. |
| 09 | Telegram remote operator lane | complete_fixture_only | Telegram checkpoint/manual lane evidence is surfaced in the V5 Command Center bridge panel as redacted local-only status; no bot/API send, token read, browser/CDP, or scheduler is claimed. |
| 10 | Approval/outbox/audit integration | complete_fixture_only | Payload hash, approval, outbox, bridge, manual/deferred distribution, audit, and final action-strip artifacts exist across lanes; V5 Command Center now displays deterministic manual audit rows, operator-supplied approve/hold/reject decision packets bound to adapter-built payload hashes, local outbox readiness reconciliation rows, Discord/Telegram local-only bridge rows, Facebook Page/Threads/Instagram/TikTok/Generic Manual local-only handoff rows, and a consolidated final operator action strip. Approval/readiness/bridge/manual-deferred/action-strip status is local/manual evidence only and does not authorize dispatch. |
| 11 | Public URL capture and reconciliation | complete_fixture_only | Substack and LinkedIn URL/audit imports are operator-supplied/manual only. |
| 12 | Community feedback intake | complete_fixture_only | Operator-supplied feedback intake packet exists locally; no live community activity, scrape, fetch, API, browser, or provider call is claimed. |
| 13 | LLM feedback summarizer | deferred | Current backlog summary uses deterministic tag grouping only; no LLM/provider call is claimed. |
| 14 | Backlog/next-idea generator | complete_fixture_only | Deterministic backlog candidates are generated from operator-supplied fixture feedback; recommendations remain review-only. |
| 15 | Media asset export lane | complete | Media transport and media judgment are live-proven across implemented lanes. Scoped repair run `v6_pipeline_d49f6e14a856` rejected weak search media, selected current FRED/EIA WTI chart assets through 2026-06-29, uploaded Substack visuals in-body with public placement PASS, and required LinkedIn native media upload/preview proof before post success. Google search remains environment-blocked, with source-backed chart pack fallback retained. |
| 16 | V6 UI command surface | complete_fixture_only | Final V6 command center is integrated into canonical `ui/contentops_v5/` with local deterministic adapter model, inspector selectors, nav route, disabled live-action controls, full platform universe, source-aware media lanes, manual audit lane, and final operator action strip. |
| 17 | Operator review dashboard | partially_complete | V5 Approval Queue/Evidence Vault show fixture/manual evidence; no live controls authorized. |
| 18 | Credential setup workbench alignment | blocked_until_explicit_live_scope | Credential/env value reads are forbidden unless a future exact scope allows safe handling. |
| 19 | Platform registry alignment | partially_complete | Registry contract now marks Meta-family official API lanes live-capable under Fast Ship Mode when credential rows are present; future UI/reporting tasks should surface per-platform evidence and blocked reasons. |
| 20 | Adapter safety policies | partially_complete | Focused tests cover Meta adapter validation, dry-run, live request construction, failure shaping, env fallbacks, and unsupported edit outcomes. Platform actions remain governed by Fast Ship evidence and redacted status docs. |
| 21 | Browser/CDP supervised adapter boundary | complete_pre_live_no_send | X TASK 0087AD proved standard ContentOps profile CDP post/capture/reply with registry audit; reusable profile guard, pre-live post packet, GO-phrase gate, exact authorization/scope/execution packets, and registry reconciliation are complete as local supervised packet evidence. `TASK_CONTENTOPS_V6_X_CDP_REGISTRY_TO_OPERATOR_WORKFLOW_BATCH_V0` finishes the remaining registry idempotency/readback lane: exact execution rows append idempotently by natural key, registry rows audit locally without public fetch, operator_browser_lab has a read-only audit command, and V5 Command Center shows Registry Readback. Browser/CDP remains supervised and cannot read session/secret stores; no public URL fetch is claimed. |
| 22 | Manual fallback playbooks | complete_fixture_only | Substack/LinkedIn runbooks exist, and Facebook Page/Threads/Instagram/TikTok/Generic Manual manual/deferred distribution rows are hardened in the canonical V5 Command Center as local-only handoff/status evidence. |
| 23 | Evidence packet standardization | complete_fixture_only | Final release packet, acceptance record, red-team report, and browser-QA boundary are generated under `docs/automation/V6_FINAL_RELEASE/`; no live/API/provider evidence is claimed. |
| 24 | End-to-end dry-run acceptance | complete_fixture_only | Local V6 loop evidence covers idea → research packet → canonical article → Discord drop → variants → hash approval → blocked dispatch/audit/manual fallback → feedback → next idea. |
| 25 | Final product readiness review | complete | Final non-bypassed full all-platform run `v6_pipeline_3c44a9855cc6` reached true `DISPATCH_COMPLETE` with live provider and dispatch enabled. Manual QA then found LinkedIn native image and Substack placement regressions; scoped repair run `v6_pipeline_d49f6e14a856` reached `DISPATCH_COMPLETE` for Substack + LinkedIn with Substack public placement PASS and LinkedIn native media preview proof. Manual screenshot/crop review and LinkedIn permalink/readback hardening remain recommended before launch acceptance. |

## Accepted Lane Highlights

- Status docs/protocol exist in `docs/status/`.
- Canonical dashboard is `ui/contentops_v5/`.
- Substack manual publication evidence is complete as fixture/manual local evidence.
- LinkedIn manual publication evidence is complete as fixture/manual local evidence and accepted at `83c53fd3a39b377d9f74fa70cd8b6a5357689ecb` after this status repair.
- Discord, Telegram, Facebook Page, Threads, LinkedIn, X, and Substack have live success evidence under E2E rehearsal `v6_pipeline_3c19fed2b5df`; Instagram has live scoped retry success evidence under `v6_pipeline_a2d260907953`.
- X CDP pre-live post command, GO-phrase gate, exact execution outcome, registry reconciliation, and registry idempotency/readback audit are complete as local supervised/packet evidence; no repo-driven X click, API call, session read, or public URL fetch is claimed.
- Live/provider/platform execution is enabled under Fast Ship Mode for implemented lanes with evidence; unsupported, missing-input, and media-validation outcomes are recorded explicitly.

Completed lane: `TASK_CONTENTOPS_V6_MEDIA_JUDGMENT_AND_ARTICLE_VISUAL_STRUCTURE_GATE_V0`. Clickable links and real media dispatches remain integrated, but selected visuals now must pass a deterministic content audit before counting as launch-ready evidence. The audit rejects stale, weakly sourced, directionally mismatched, unverified, or generated fallback visuals; oil-topic runs can generate current WTI/FRED chart packs with machine-readable attribution; Substack variants now carry multiple in-body visual markers; and article quality gates require SEO metadata plus purposeful visual slots. Focused verification: `python -m py_compile ...` passed; `python -m pytest tests/test_media_content_audit_v6.py tests/test_google_image_search_v6.py tests/test_substack_browser_adapter_v6.py tests/test_ai_research_canonical_article_engine_v6.py -q` -> 19 passed; `python -m pytest tests/test_platform_native_variant_generator_live.py tests/test_live_production_pipeline_runner.py -q` -> 20 passed; `python -m pytest tests/test_instagram_adapter_v6.py tests/test_facebook_page_adapter_v6.py tests/test_telegram_live_adapter_v6.py -q` -> 28 passed.

Completed restore lane: `TASK_CONTENTOPS_V6_RESTORE_NON_BYPASSED_FULL_AUTOMATION_SUCCESS_AND_EDITORIAL_QUALITY_V0`. Clean restore worktree at remote HEAD `bb3a0ffe50c201011903f211d1caf62c6fdb556c` ran `python -m live_contentops.live_production_pipeline_runner_v6 --live-run --dispatch-live` with `CONTENTOPS_BYPASS_QUALITY_GATES=false`. Final run `v6_pipeline_3c44a9855cc6` reached true `DISPATCH_COMPLETE`. Article gates passed (2,009 words, 8 sections, 18 numeric references, SEO metadata, 2 visual slots); media audit passed with current FRED/EIA WTI assets; Substack public visual readback passed with 2 public images; all implemented platform lanes returned SUCCESS. Recommended next lane: `TASK_CONTENTOPS_V6_PROVIDER_NATIVE_DRAFT_RELIABILITY_AND_PLATFORM_VISUAL_QA_V0`.

Completed visual repair lane: `TASK_CONTENTOPS_V6_LINKEDIN_NATIVE_IMAGE_AND_SUBSTACK_IN_BODY_VISUAL_PLACEMENT_REPAIR_V0`. Manual QA found that prior `DISPATCH_COMPLETE` evidence was not product-acceptable because LinkedIn could pass as text-only and Substack images could be grouped near the end despite upload counts. The repair added required LinkedIn media upload/preview proof, Substack segment-by-segment visual insertion, visual-slot/marker-heading placement inference, and public visual order checks. Scoped live run `v6_pipeline_d49f6e14a856` reached `DISPATCH_COMPLETE` for Substack + LinkedIn with no bypass: Substack public readback PASS with 2 in-body images, LinkedIn native media `uploaded` and `media_preview_detected=true`. Focused verification: `python -m pytest tests/test_linkedin_browser_adapter_v6.py tests/test_substack_browser_adapter_v6.py tests/test_platform_native_variant_generator_live.py tests/test_live_production_pipeline_runner.py` -> 36 passed.

## How to Update This Ledger

1. Update this file only on roadmap/lane completion or execution-plan refresh.
2. Use conservative statuses and distinguish local/fixture/manual evidence from live/API/provider evidence.
3. Never hardcode a future next task as permanent truth.
4. Keep recommendations soft and timestamp/context dependent.
5. If a lane claims live/public/API verification, cite committed evidence and tests; otherwise mark it manual/fixture/pre-live.
