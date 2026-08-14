# V2 short + longform low-cost audio vertical slice evidence

Task: `TASK_CONTENTOPS_V2_SHORT_LONGFORM_LOW_COST_AUDIO_VERTICAL_SLICE_V1`

Builder ceiling: `PASS_IMPLEMENTATION_MEDIA_READY_FOR_JIM_CHATGPT_REVIEW`

Owner acceptance: pending Jim + ChatGPT actual-media/audio review.

## Identity

- branch: `task/v2-short-longform-low-cost-audio-vertical-slice-v1`
- authority base: `task/v2-audio-economics-longform-contract-v1@3831b9defb0d591c5bc01e2790bc34eb5054e664`
- issuance master: `70987dfe83e1c623a19b86e58ede20be6d584e09`
- runtime root: `A:\Capital Chronicle\Runtime\ContentOps\v2_short_longform_low_cost_audio_20260815`
- creative source SHA-256: `c6fc97a2485ffe6e3f5a40e12521ef28291877553e3b7058620c68099c8e673e`

## Story and evidence

The fresh story is **The Treasury market's giant offset**: August 11, 2026 CFTC Traders in Financial Futures data show very large asset-manager net longs opposite very large leveraged-fund net shorts in two-, five-, and ten-year Treasury futures. The independently authored longform explains synthetic-duration demand, the cash-futures basis/repo mechanism, benefits, leverage transmission, the proxy-versus-identity boundary, counter-case, and confirm/challenge conditions.

The governed CFTC text source SHA-256 is `e3e4bff2592777fbd9a125e723bdb087b5110b47b95c16e1b376dcb029b44f96`. Exact row hashes, values, dates, and source URLs are in `contracts/evidence_packet.json` below the runtime root. Primary supporting authorities are CFTC, the Federal Reserve's 2024 and 2026 basis/exposure notes, the May 2026 Financial Stability Report, and U.S. Treasury remarks on Treasury-market resilience.

## Actual media

| Artifact | Resolution | Duration | SHA-256 | Audio |
|---|---:|---:|---|---|
| short clean master | 2160×3840 | 56.739s | `f0a72ae1b4f91da5162850705cfe744587c6c18f5d23d337d51dd43574baac81` | −16.1 LUFS / −1.5 dBTP |
| short derivative | 1080×1920 | 56.739s | `b838a9f339729fc97e5feae75d8689a7f6dbb4a5fbc38c3063445396d98158ae` | copied from master |
| longform clean master | 1920×1080 | 559.300s | `82068792fd66d943d3089932c2a1f563f7ff2fcb0be2ba3b7623f476610ab4fa` | −16.0 LUFS / −1.2 dBTP |

All masters are H.264/AAC, 30 fps, YUV420p limited-range BT.709 SDR. The longform is a direct 1080p source render. A nine-minute 4K longform was deferred as disproportionate for this first owner-review proof; the vector-native source and scale-selectable Remotion path remain 4K-capable.

Clean masters have no burned subtitles. Semantic sidecar SRTs, proxies, contact sheets, keyframes, selective-rerender proof, ffprobe results, loudness receipts, and the final handoff are persisted under the runtime root.

## Build audio and economics

- production build backend: local Kokoro-82M, voice `af_heart`, Apache-2.0 model license;
- 26 immutable semantic segments, 615.8 generated seconds, 9,882 input characters;
- exact segment identity hashes text + backend + model + voice + settings;
- restart proof: 26 reused, zero regenerated;
- API credits: 0; API dollar cost: 0; electricity/hardware cost not measured;
- cost label: `ZERO_MARGINAL_API_CREDIT_COST_NOT_ZERO_TOTAL_COST`;
- Parler: `PARLER_DEFERRED_ENVIRONMENT_UNAVAILABLE`, with no install project attempted;
- Chatterbox: one local default/no-reference/no-cloning probe, 13.68s output in 101.1177s on CPU, MIT, zero API credits;
- ElevenLabs: zero calls and zero credits; premium-final seam disabled pending explicit owner authority;
- Windows SAPI: not used.

Kokoro and Chatterbox audition WAVs remain in `auditions/`. Builder metrics do not accept either as the permanent publication voice.

## Recovery, review, and safety

- durable SQLite stage ledger reaches `OWNER_REVIEW` across the required fourteen stages;
- identical checkpoints and immutable audio entries reuse safely;
- a selective longform scene render left both master hashes unchanged;
- native visual families include primary document, numeric hero, diverging chart, timing, repo/basis mechanism, synthetic-duration flow, stress transmission, and confirm/challenge matrix;
- proxy review repaired two semantic visual mismatches before master render;
- deterministic mastering repaired low loudness and missing BT.709 metadata without time stretching;
- nine focused tests pass; TypeScript passes; CodeGraph must be current at commit;
- public writes 0, uploads 0, browser-profile uses 0, V1 mutations 0, ElevenLabs calls 0, mode bakeoffs 0, V2-02 starts 0.

Remaining owner-review caveats: Kokoro voice identity/prosody is not publication-accepted; several analytical scenes deliberately settle into calm late-scene holds that should be judged in the actual nine-minute video; the 4K longform pass remains deferred.
