# ContentOps V2 Locale Activation Hardening V1 — Evidence

Authority date: 2026-08-18

Task: `TASK_CONTENTOPS_V2_LOCALE_ACTIVATION_HARDENING_V1`

Classification:

`PASS_IMPLEMENTATION_V2_LOCALE_ACTIVATION_PACKAGES_READY_FOR_JIM_LISTENING_REVIEW`

The accepted US Retail Short was localized into Simplified Chinese, Hindi, Vietnamese, and
Korean from one governed English transcript and one accepted picture lock. The four packages
contain localized narration, actual-audio-timed SRT/VTT, transcript-derived metadata, a listening
sample, and a picture-identical per-locale mux. The YouTube-neutral manifest carries the canonical
English audio plus all four locale sidecars. No upload or account-eligibility claim was made.

The accepted picture is `58.4s / 1,752 frames / H.264 High / 1080x1920`. Its encoded video-stream
SHA-256 is `ea56cd17e8973c29c93160285462bc808dca2d9560957c897e06e18f74c30bf5`;
all four localized muxes have the same stream hash and frame count. Muxing did not use
`-shortest`, and Remotion was not invoked.

The source is tagged `yuvj420p / pc / bt470bg` with no explicit transfer/primaries metadata.
That is legal full-range H.264 and does not objectively prove wrong pixel levels. The governed
verdict is therefore to preserve the already accepted picture stream, not perform a speculative
transcode. No shared normalized derivative was required.

Hindi uses local `kokoro-onnx / kokoro-v1.0 / hf_alpha`. The local Chinese candidate failed its
real G2P preflight, so the authorized bounded fallback uses ElevenLabs
`eleven_multilingual_v2`; Vietnamese uses `eleven_flash_v2_5`; Korean uses
`eleven_multilingual_v2`. All use the non-cloned premade stock voice
`EXAVITQu4vr4xnSDxMaL`. The account remained on the existing free tier. Across preflight,
bounded corrections, and final proof, the observed quota counter moved from 5,703 to 8,076
characters; no purchase, quota extension, or external cash charge occurred. Provider responses
did not expose per-request dollar cost, which remains recorded as `null` rather than invented.

The real E2E receipt is ignored runtime evidence at:

`.task-runtime/v2-locale-activation-hardening-v1/proof_20260818/locale_activation_e2e_receipt.json`

Its SHA-bound receipt hash is
`d03b47cf652a06847aac0fbcbc72df43e2b2c8fff7c6c469c3cc6819bdce98fa`.
Exact artifact/package hashes and absolute listening/full-audio/package paths are in
`final_evidence_v1.json`.

Builder validation does not claim Jim's subjective language, voice, or listening acceptance.
The next task remains unauthorized until GitHub/package audit and that listening gate pass.
