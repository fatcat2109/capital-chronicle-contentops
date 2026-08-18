# ContentOps V2 Locale Audio Timeline Alignment Bounded Correction V1 — Evidence

Authority date: 2026-08-18

Task: `TASK_CONTENTOPS_V2_LOCALE_AUDIO_TIMELINE_ALIGNMENT_BOUNDED_CORRECTION_V1`

Classification ceiling:

`PASS_V2_LOCALE_AUDIO_TIMELINE_ALIGNMENT_CORRECTION_READY_FOR_OWNER_REVIEW`

The Task-2 Vietnamese narration defect was a timeline-placement defect. Task 2 packed all
localized phrases from 0.18 seconds forward and padded the rest of the accepted picture. Measured
meaningful Vietnamese speech ended at 43.02 seconds, leaving a 15.38-second unexplained tail.

This bounded correction binds each localized source segment to the matching accepted English
narrative window, records each actual synthesized phrase duration and placement, and derives
captions from those corrected placements. Every one of the 18 SHA-bound Vietnamese Task-2 phrase
WAVs was reused unchanged. There was no translation rewrite, TTS request, speed change, Remotion
render, picture transcode, or public/platform operation.

Corrected Vietnamese meaningful speech runs from 0.19 through 57.68 seconds, leaving 0.72 seconds
of final headroom. The accepted picture remains 58.4 seconds and 1,752 frames. The localized mux's
encoded video-stream SHA-256 remains
`ea56cd17e8973c29c93160285462bc808dca2d9560957c897e06e18f74c30bf5`.

The exact corrected audio SHA-256 is
`38da2efe42f91940bd3b1ca4555a0540aae0d6789ba170812e0406cdd71ec0ea`.
The corrected package ID is
`locale_pkg_893b18432e8b25e38d3c6e8a3c34bdd91ef5043c747c06e5c7b766a599f26cb8`.

Simplified Chinese, Hindi, and Korean were not regenerated or resynthesized. Deterministic actual
timing QA passes their existing Task-2 artifacts with meaningful final tails of 2.83, 1.49, and
0.56 seconds respectively.

The runtime owner-review bundle is ignored evidence under:

`.task-runtime/v2-locale-audio-timeline-alignment-correction-v1/proof_20260818/`

Exact artifact paths, hashes, source-window placements, unchanged-locale identities, and bounded
authority counters are in `final_evidence_v1.json` and the runtime
`locale_audio_timeline_correction_receipt.json`.

Builder validation does not claim Jim's subjective Vietnamese language, pacing, or voice
acceptance. Task 3 was not started.
