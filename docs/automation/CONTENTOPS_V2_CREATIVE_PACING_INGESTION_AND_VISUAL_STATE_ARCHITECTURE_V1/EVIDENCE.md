# Creative Pacing, Ingestion, and Visual-State Architecture V1 — Evidence

Authority date: 2026-08-15

Task: `TASK_CONTENTOPS_V2_CREATIVE_PACING_INGESTION_AND_VISUAL_STATE_ARCHITECTURE_V1`

Result: `PASS_IMPLEMENTATION_MEDIA_READY_FOR_JIM_CHATGPT_REVIEW`

Owner/substrate/public/mode/voice acceptance: not claimed

## Lineage and isolation

- Freshly fetched `origin/master`: `1a0029d0a01c77ae11b164904b0343489801dd25` (`fix(v1): recover yield with bounded candidate walk`).
- Exact V2 starting parent: `ae0abc575521392b043486415cefaa7179c14b48` (`feat(v2): repair treasury visual integrity and asset diversity`).
- Branch: `task/v2-creative-pacing-ingestion-visual-state-architecture-v1`.
- Runtime: `A:\Capital Chronicle\Runtime\ContentOps\v2_creative_pacing_ingestion_visual_state_20260815_r2`.
- Public writes/uploads/browser-profile uses/V1 mutations: `0/0/0/0`.
- No MAX/ULTRA comparison, V2-02 work, ElevenLabs call, publication action, or provider selection occurred.

## Generic architecture delivered

`live_contentops/v2_creative_pacing_v1.py` separates four concepts:

1. semantic beat — editorial/narrative information unit;
2. visual state — persistent viewer context that can carry several beats;
3. within-state action — reveal/emphasis without replacing the composition;
4. transition event — intentional context reset with an authored reason.

The reusable creative-role contract explicitly teaches `SEMANTIC BEAT != VISUAL STATE != WITHIN-STATE ACTION != TRANSITION EVENT`, progressive disclosure, ingestion dwell, cognitive switching cost, joint narration/visual editing before audio lock, and actual rendered-media inspection. It imposes no cadence or generic maximum state duration. The exact role policy is `new/gpt-5.6-sol-xhigh` only for `V2_CREATIVE_EDITOR`, `V2_MOTION_CODE_AUTHOR`, and `V2_CREATIVE_REVISION_AUTHOR`, with at most three same-model retries and no fallback.

Deterministic code binds authored state groups to exact beat timing, validates continuity/mapping, scans viewer copy, and produces descriptive diagnostics. It does not infer a director plan from seconds or enforce numerical creative thresholds.

## Actual media

| Artifact | Resolution | Duration | Loudness | SHA-256 |
|---|---:|---:|---:|---|
| `treasury-positioning-short-creative-pacing-ingestion-master.mp4` | 2160×3840 | 56.700s | -16.0 LUFS / -1.3 dBTP | `da4e2f7d23983b888055fe2bd05d835276e8e281573bc5146323ea3edb5d0fe6` |
| `treasury-positioning-short-creative-pacing-ingestion-1080x1920.mp4` | 1080×1920 | 56.700s | inherited mastered audio | `f122159fa1df0d088db606fe263d78bc6155541ff4b9af9327b38e123f516ea8` |
| `treasury-positioning-longform-creative-pacing-ingestion-master.mp4` | 1920×1080 | 559.300s | -16.1 LUFS / -1.3 dBTP | `d5c3102481ec89f11751128db5374c400f3430224463654d3ec05c7b67b166a5` |

Both masters are H.264/yuv420p, 30 fps, BT.709 SDR limited-range with AAC audio. Sidecars are `captions/treasury-positioning-short.srt` and `captions/treasury-positioning-longform.srt`; captions are not burned into the clean masters.

## Before/after pacing evidence

The before values are the independent owner-audit estimate for the accepted parent actual media. Fewer states are not treated as intrinsically better; the after media was inspected for comprehension, context persistence, useful resets, and final-third quality.

| Variant | Semantic beats | States before → after | Full-screen transitions before → after | Beats/state after | State duration after (min / median / mean / p90 / max) |
|---|---:|---:|---:|---:|---|
| Short | 24 | 24 → 9 | 23 → 8 | 2.667 | 2.051 / 6.350 / 6.286 / 7.680 / 8.900s |
| Longform | 125 | 125 → 64 | 124 → 63 | 1.953 | 3.243 / 4.905 / 8.737 / 16.542 / 27.888s |

Semantic boundary/montage beats occupied an estimated 10.901s short / 127.164s longform before. After, none remains a standalone boundary/montage visual state; useful qualifications are overlays, reveals, or persistent-state emphasis. Low-information standalone-card burden is `0s` in both outputs. Orange/title/boundary states are not generically banned; this controlled story simply did not need one after review.

Retained resets introduce a materially different source, analytical object, mechanism, monitoring context, or chapter. Removed resets were near-identical tenor updates, numerical changes inside one object, minor qualifiers, and synthesis sentences that worked better inside the existing view. Repeated near-identical-state churn diagnostics report no remaining candidates.

Progressive disclosure carries 23/24 short beats across eight states and 91/125 longform beats across 30 states. Examples:

- short `S04_PRIMARY_ROW_V01`: one full CFTC table persists through classification, source scope, and motive-limit emphasis;
- longform `L03_TWO_YEAR_V02`: one 27.888s 2Y object carries six beats from gross legs through governed nets, face-value boundary, and interpretation;
- longform basis/repo mechanisms now follow the source clock, reducing payoff distance before detailed tenor evidence;
- longform final third: 23 states, 8.018s mean, ten progressive states; actual complete-strip inspection passed.

The one allowed systemic correction absorbed the standalone orange 2Y qualifier/synthesis into the persistent maturity-data state. A subsequent frame proof caught a localized governed-row lookup bug inside that correction; state-level anchor binding was repaired and the affected longform master alone was rerendered. Final proof frames keep exact 2Y data through all five sampled actions.

## Ingestion dwell, narration, and pauses

High-information evidence states carry authored ingestion rationales rather than a universal duration gate. Short examples dwell 6.100s (full three-row CFTC table), 7.275s (multi-measure proxy comparison), and 6.350s (Financial Stability Report/stress path). Longform evidence holds range from compact 3–5s source introductions to 13.761s category reading, 18.046s basis/dataset boundary, and 18.592s leverage-page comparison. The 27.888s 2Y analytical state is accepted because six meaningful within-state actions advance utility.

| Variant | Narration words | Exact build-audio duration | Actual WPM | ≥250ms pauses at -40dB | Pause seconds | Median / longest |
|---|---:|---:|---:|---:|---:|---|
| Short | 127 | 56.575s | 134.7 | 20 | 11.257s | 0.547 / 0.815s |
| Longform | 1,357 | 559.150s | 145.6 | 167 | 87.939s | 0.514 / 0.886s |

These silence values are descriptive measurements on the mastered soundtracks, not cadence gates. No global TTS slowdown was applied. Existing segment-final pauses remain; dense mechanism/source passages use shorter clauses and persistent visuals.

## Truth, numeric authority, audio, assets, and safety

- CFTC raw source SHA-256: `e3e4bff2592777fbd9a125e723bdb087b5110b47b95c16e1b376dcb029b44f96`.
- Exact 2Y/5Y/10Y row hashes: `c70fb895f4fa8c3df8f38d3cf3aa0a41a39d52388d8f15289cc02fe7e1303da8`, `ec1e9bc0dd9a4c68764c19f95b02bdd4ad8c7f5176cebaa6337ef953b63b76da`, `4beffa46b41271563ccb4cd48bc5ef903184e793356a2fc9c3a967a1b7d6bf6e`.
- Numeric binding: `PASS_VIEWER_FACING_CFTC_VALUES_BOUND_TO_EXACT_GOVERNED_ROWS`; TypeScript contains no position literals and unused divergent `assetLong`/`assetShort` fields are removed.
- `STATIC_FULL_CONTEXT` survives for primary evidence: contain framing, fixed source-object scale/position, no zoom/pan/crop/Ken Burns/parallax.
- Audio: 25 unchanged semantic segments reused; one local Kokoro jargon-cleanup segment regenerated in 23.005s; combined audio rebuilt locally; API cost `$0`; no ElevenLabs and no publication-voice decision.
- Asset hunt/additions/network reads: `0`; the accepted 23-asset board was reused byte-for-byte. Serialized visual states actually reference 22 assets across nine rendered source-material families; `fed-eccles-building-1937.jpg` is honestly recorded as selected but not rendered.
- Internal-jargon scan: `PASS`, 406 viewer strings, zero findings.
- Source sandbox/import validation: `PASS`; viewer source imports only `react` and `remotion`.
- Generated real-person documentary media: `0`; public writes/uploads/V1 mutations: `0`.

## Validation and owner-review files

- `python -m pytest tests/test_treasury_visual_material_repair_v1.py -q`: `11 passed` (Windows emitted a post-success pytest temp-directory cleanup warning; exit code `0`).
- `npm run typecheck` in `video/asset_first_v1`: `PASS`.
- Cheap short and longform proxies rendered and were inspected before masters.
- Actual master contact sheets and dense full-duration strips were inspected after the single systemic correction.

Jim should send independent ChatGPT these exact runtime files:

1. `media/treasury-positioning-short-creative-pacing-ingestion-master.mp4`;
2. `media/treasury-positioning-longform-creative-pacing-ingestion-master.mp4`;
3. `captions/treasury-positioning-short.srt` and `captions/treasury-positioning-longform.srt`;
4. `review/short-master-dense-temporal-strip.jpg` and `review/longform-master-dense-temporal-strip.jpg`;
5. `review/short-progressive-disclosure-proof.jpg` and `review/longform-progressive-disclosure-proof.jpg`;
6. `contracts/visual_state_timeline.json`, `contracts/semantic_beat_to_visual_state_mapping.json`, and `contracts/full_screen_transition_timeline.json`;
7. `contracts/creative_pacing_owner_review.json`, `receipts/actual_master_pause_analysis.json`, `receipts/internal_jargon_scan.json`, `receipts/numeric_binding_receipt.json`, `receipts/frozen_audio_receipt.json`, and `receipts/zero_public_write.json`;
8. this evidence file and runtime `HANDOFF.json`.

Jim/independent ChatGPT must still decide whether the actual media clears the owner quality gate. This result does not authorize MAX/ULTRA, V2-02, publication, or any provider/voice decision.
