# Capital Chronicle ContentOps V2 — Retention-Native Video Factory Task Graph V1

Authority date: 2026-08-12
Status: `CURRENT_CANONICAL_V2_TASK_GRAPH`

Detailed scope and acceptance live in `CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_MASTER_PLAN_V1.md`. The current V2-01 architecture override lives in `docs/status/CONTENTOPS_V2_GPT56_CREATIVE_CODE_AND_ASSET_DENSITY_OWNER_OVERRIDE_V1.md` and controls where the original V2-01 text conflicts.

## Current position

Canonical plan baseline was authored from master `831dfb181b23cb7b27d195bbbc1bb7b847a86590` and later updated directly on master. Always fetch current remote master before implementation.

Rejected creative references:

- `task/tier2-v2-creative-system-rebuild-v1` / `d231b54e026570442d9fd9269b61e55c3de31d21` — `REJECTED_CREATIVE_PRODUCT_REFERENCE_ONLY`
- `task/tier2-v2-retention-native-video-factory-vertical-slice-v1` / `b6f5002903fba65a668506e4ca38ae61b907ab18` — `FAIL_CREATIVE_MOTION_ARCHITECTURE / REJECTED_CREATIVE_PRODUCT_REFERENCE_ONLY`

The second branch improved story selection, asset/right/audio infrastructure and machine diagnostics but failed Jim's actual media review because motion/edit grammar remained repetitive, slow, template-like, and had text-overlap defects. Do not merge it.

Current next task:

`TASK_CONTENTOPS_TIER2_V2_GPT56_CREATIVE_CODE_ASSET_RICH_VIDEO_VERTICAL_SLICE_V1`

Exact main creative-code model:

`new/gpt-5.6-sol-xhigh` through 9Router.

## Execution graph

| # | Task | Product capability | Required visible result | Result required to advance | Operator/external dependency | Next |
|---|---|---|---|---|---|---|
| V2-01 | `TASK_CONTENTOPS_TIER2_V2_GPT56_CREATIVE_CODE_ASSET_RICH_VIDEO_VERTICAL_SLICE_V1` | exact GPT-5.6 creative editor + motion-code author + revision author; sandboxed per-shot Remotion code; asset-rich edit; collision/repetition diagnostics | 45–60s native short + 90–150s 16:9 proof, exact GPT-5.6 authorship receipts, large rights-safe candidate pool, rich selected visual states, current voice/music/SFX, captions-hidden motion proof | `PASS_RETENTION_NATIVE_VERTICAL_SLICE_VISUAL_AUDIO_ACCEPTED` | Existing 9Router/image/asset/voice credentials only; no public authority | V2-02 |
| V2-02 | `TASK_CONTENTOPS_TIER2_V2_PREMIUM_AUDIO_AND_ASSET_INTELLIGENCE_V1` | premium voice routing, sonic identity, rights-aware entity/document/location asset intelligence | blind voice bundle, reusable music/SFX library, 3 rights-cleared asset packs, rerendered proof | `PASS_PREMIUM_AUDIO_AND_ASSET_ENGINE_ACCEPTED` | Jim decision only if paid ElevenLabs/music becomes justified | V2-03 |
| V2-03 | `TASK_CONTENTOPS_TIER2_V2_DIVERSE_STORY_MODE_CORPUS_AND_MOTION_ACCEPTANCE_V1` | repeated creative quality across story modes | ≥3 shorts, ≥2 mid-form, 4 story modes + `VIDEO_NOT_SELECTED`, optional 8–15m hero only if earned | `PASS_REPEATED_PROFESSIONAL_CREATIVE_QUALITY` | governed story supply | V2-04 |
|  |  |  | **MILESTONE: PROFESSIONAL_CREATIVE_PROOF** |  |  |  |
| V2-04 | `TASK_CONTENTOPS_TIER2_V2_PACKAGING_DISCOVERY_AND_CHANNEL_SERIES_ENGINE_V1` | titles, thumbnails, covers, search intent, series, CTA/binge loop, promise audit | 3 title + 3 thumbnail strategies per hero; native short packaging; 4–6 series hypotheses | `PASS_CHANNEL_PACKAGING_AND_SERIES_SYSTEM` | read-only trend/search sources where useful | V2-05 |
| V2-05 | `TASK_CONTENTOPS_TIER2_V2_SHADOW_DAILY_VIDEO_PORTFOLIO_V1` | daily video opportunity portfolio and abstention | 7-day shadow/replay, selected/deferred/not-selected reasons, ≥3 high-quality packages if supply permits | `PASS_SHADOW_VIDEO_PORTFOLIO_FACTORY` | live/replay story universe | V2-06 |
|  |  |  | **MILESTONE: CHANNEL_PRODUCT_AND_SHADOW_FACTORY_PROOF** |  |  |  |
| V2-06 | `TASK_CONTENTOPS_TIER2_V2_YOUTUBE_PRIVATE_UPLOAD_PROCESSING_AND_READBACK_V1` | private/unlisted YouTube upload, processing, captions/thumbnail metadata, readback/recovery | one private hero + one private/unlisted Short with exact object/readback evidence | `PASS_YOUTUBE_PRIVATE_TRANSPORT_AND_READBACK` | fresh YouTube OAuth/scope/channel validation | V2-07 |
| V2-07 | `TASK_CONTENTOPS_TIER2_V2_SHORTS_AND_TIKTOK_CONTROLLED_DELIVERY_V1` | controlled YouTube Shorts + TikTok draft/private delivery | private Short + TikTok controlled object/readback or exact provider approval blocker | `PASS_CONTROLLED_SHORT_VIDEO_DELIVERY` | TikTok OAuth/app capability/approval state | V2-08 |
|  |  |  | **MILESTONE: PRIVATE_PLATFORM_DELIVERY_PROOF** |  |  |  |
| V2-08 | `TASK_CONTENTOPS_TIER2_V2_EXACT_AUTHORIZED_PUBLIC_GROWTH_PILOT_V1` | bounded real public cohort with strict readback | ~2 hero/mid-form + ~6 Shorts and bounded TikTok cohort if authorized; no-publication allowed | `PASS_SMALL_PUBLIC_VIDEO_COHORT` | **explicit Jim public-write authorization required** | V2-09 |
|  |  |  | **MILESTONE: CONTROLLED_PUBLIC_COHORT_PROOF** |  |  |  |
| V2-09 | `TASK_CONTENTOPS_TIER2_V2_RETENTION_ANALYTICS_AND_BEAT_ATTRIBUTION_V1` | platform performance → video/scene/beat/asset/audio attribution | retention curves, spike/dip reports, packaging/funnel observations, freshness/provenance | `PASS_BEAT_LEVEL_RETENTION_OBSERVABILITY` | real published cohort metrics | V2-10 |
| V2-10 | `TASK_CONTENTOPS_TIER2_V2_TREND_PACKAGING_AND_CREATIVE_LEARNING_V1` | bounded versioned learning from real audience evidence | ≥3 supported conclusions, one packaging learning, one retention edit learning, one `NO_POLICY_CHANGE` | `PASS_BOUNDED_VIDEO_GROWTH_LEARNING` | sufficient sample size | V2-11 |
|  |  |  | **MILESTONE: RETENTION_AND_LEARNING_PROOF** |  |  |  |
| V2-11 | `TASK_CONTENTOPS_TIER2_V2_AUTONOMOUS_CHANNEL_OPERATING_SYSTEM_V1` | full daily opportunity→production→publish→observe→learn loop + operator surface | 10–15 operating-day soak, Video Today state, recovery/cost/series health | `PASS_AUTONOMOUS_VIDEO_CHANNEL_LOOP` | exact platform authority from prior gates | V2-12 |
|  |  |  | **MILESTONE: AUTONOMOUS_OPERATING_PROOF** |  |  |  |
| V2-12 | `TASK_CONTENTOPS_TIER2_V2_FINAL_RELIABILITY_GROWTH_PROOF_AND_RELEASE_V1` | final repeated quality/reliability/growth proof and release | ≥6 accepted hero/mid/long, ≥20 shorts, ≥3 series, ≥3 story modes, retention-driven improvement, reliability proof | `PASS_CONTENTOPS_V2_VIDEO_FACTORY_OWNER_ACCEPTED` | Jim final acceptance/release authorization | FINAL |

## Non-negotiable V2-01 replacement rules

1. The failed `b6f50029...` implementation does not satisfy V2-01 and does not advance the graph.
2. `new/gpt-5.6-sol-xhigh` must be the exact primary creative editor, motion-code author, and creative revision author through 9Router.
3. Remotion is deterministic execution/rendering infrastructure, not the source of creative decisions.
4. Keep accepted image/asset/voice/audio provider choices unless a concrete blocker requires change.
5. Use the official Remotion Agent Skill baseline recorded in `CONTENTOPS_V2_REMOTION_AGENT_SKILL_BASELINE_V1.md`; community skills are reference only.
6. Increase asset candidate/selected-state richness substantially, while preserving editorial purpose and rights.
7. Add machine diagnostics for text collision and repetitive transition/easing/duration/direction/layout motifs.
8. A fallback creative model must be labeled `DEGRADED_CREATIVE_MODEL` and cannot self-pass professional quality.
9. Jim/ChatGPT must inspect actual MP4/audio before V2-01 passes.

## General advancement rules

1. V2-01 through V2-03 are media-quality gates. Unit tests cannot substitute for actual MP4/audio review.
2. No platform upload work before `PROFESSIONAL_CREATIVE_PROOF` and `CHANNEL_PRODUCT_AND_SHADOW_FACTORY_PROOF` pass.
3. No public video write before V2-08 receives explicit owner scope.
4. No learning-policy automation before real public cohort data exists.
5. Every task supports abstention/fail-closed outcomes; no filler is manufactured to satisfy this graph.
6. One implementation, one independent audit, maximum one bounded correction before architecture/scope is reconsidered.
7. V1 remains concurrent and authoritative for its own live runtime; V2 does not create a second newsroom/store/scheduler/publication authority.

## Milestone outputs

### `PROFESSIONAL_CREATIVE_PROOF`
Repeated owner-accepted retention-native visual/audio quality across multiple story modes.

### `CHANNEL_PRODUCT_AND_SHADOW_FACTORY_PROOF`
Packaging/series strategy plus disciplined daily video portfolio with no filler.

### `PRIVATE_PLATFORM_DELIVERY_PROOF`
Controlled YouTube/TikTok object creation, processing, identity, readback, and recovery.

### `CONTROLLED_PUBLIC_COHORT_PROOF`
Small exact-authorized live cohort with zero unresolved writes/rights/truth incidents.

### `RETENTION_AND_LEARNING_PROOF`
Real audience behavior maps to beats/packaging and supports bounded useful changes.

### `AUTONOMOUS_OPERATING_PROOF`
Durable low-burden daily channel loop survives real operations.

### `FINAL_V2_RELEASE`
Repeated professional quality, reliable operation, measured audience value, bounded learning, safe recovery, sustainable cost, and Jim owner acceptance.
