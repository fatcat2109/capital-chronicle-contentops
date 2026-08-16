# Zero-Rerender Global Language Sidecar Correction V1 — Final Evidence

Authority date: 2026-08-16

## Result

`PASS_ZERO_RERENDER_GLOBAL_LANGUAGE_SIDECAR_CORRECTION_READY_FOR_MERGE_AUDIT`

Starting branch HEAD: `ac0c089dff94a7d988bccd34e0c85ad8795249a7`.

The correction changes production policy to:

`AUDIO_SIDECAR_FIRST / PICTURE_RENDER_ONCE / NO_LOCALE_PICTURE_RENDER_BY_DEFAULT /
NO_XHIGH_PER_LOCALE / GLOBAL_LANGUAGE_REACH / BURNED_CAPTION_OPTIONAL_ONLY`.

Existing Spanish, Brazilian Portuguese and Japanese burned-caption media was not deleted or
regenerated. It remains historical proof and is not a canonical package requirement.

## Global locale registry

`CORE_ALWAYS_ON`:

`en, es, pt-BR, zh-Hans, hi, id, ar, vi, ja, ko, fr, de`

`EXPANSION_CONFIGURED`:

`zh-Hant, bn, ta, te, mr, ur, fil, tr, ru, th, it`

Hindi is the core India lane; Bengali, Tamil, Telugu and Marathi are distinct configured
expansion locales. `zh-Hant` may share Mandarin audio with `zh-Hans` only when linguistically
appropriate; script-specific captions and metadata stay separate. Cantonese is not represented
as Mandarin.

These entries are capability declarations, not voice acceptance claims.

## Translation backend

- Candidate: official `Qwen/Qwen3-4B`.
- License: Apache-2.0.
- Runtime contract: local `transformers`, `local_files_only=True`, no network fallback.
- Role: multilingual translation only; never factual authority.
- Result: `ADAPTER_IMPLEMENTED / FAIL_CLOSED_VALIDATION_TESTED /
  MODEL_NOT_MATERIALIZED_IN_REPOSITORY`.
- NLLB-200 distilled is explicitly excluded from the canonical commercial route because the
  discovered license is not commercially suitable.

The adapter validates explicit semantic facts on actual target text: numbers, percentages,
dates, named entities, units, sign/direction, chronology, and uncertainty markers. Any missing
governed target form rejects the locale segment. It performs no silent factual repair.

Official Qwen references:

- <https://huggingface.co/Qwen/Qwen3-4B>
- <https://huggingface.co/Qwen/Qwen3-4B/blob/main/LICENSE>

## TTS routing

The first route is a preference, never acceptance:

| Locale group | Preferred route | Fallback/escalation |
|---|---|---|
| en, es, pt-BR, ja | existing local Kokoro proof | Eleven Multilingual v2 |
| zh-Hans, hi, fr | local Kokoro candidate | Eleven Multilingual v2 |
| id, ar, ko, de | Eleven Multilingual v2 | owner quality decision |
| vi | Eleven Flash v2.5 | Eleven v3 only for material quality gain |
| zh-Hant | share accepted Mandarin when appropriate | Eleven Multilingual v2 |
| ta, fil, tr, ru, it | Eleven Multilingual v2 | owner quality decision |
| bn, te, mr, ur, th | Eleven v3 coverage | no lower model claim |

Fresh official ElevenLabs documentation reports Multilingual v2 at 29 languages and stable
longform, Flash v2.5 at 32 languages including Vietnamese and lower API character cost, and v3
at 70+ languages. Flash numeric normalization remains a governed pre-TTS responsibility.

Official reference: <https://elevenlabs.io/docs/overview/models>

No provider call, paid synthesis, secret access, or real-person voice cloning occurred.
Authentic authority speech remains authentic or may later receive a clearly distinct interpreter
treatment; the real person is never synthesized speaking translated words in their voice.

## One-time voice registry

Existing 20–30 second proof samples are retained for the still-review-gated locales:

- `audio/es/voice_sample.wav` — `85cf6b1669e93a69085b98c815024099c6c724238cceb2ba529807eb701605ce`
- `audio/pt-BR/voice_sample.wav` — `cb8b73867dc067d9b686f76b0edf6bd60607d95681b133d2300c55b9de5085ae`
- `audio/ja/voice_sample.wav` — `174aef4b12ac2cb93bedc41acc9517a4ae7a52dc9030eed8052a854d69055d6e`

Paths are relative to
`.task-runtime/v2-native-multiformat-multilingual-package-factory-v1/`.

English is locked to the owner-preferred accepted Kokoro baseline `af_heart`, speed `1.06`,
language `en-us`, as recorded by the accepted owner-polish evidence. The registry leaves its
sample path and hash null because that authority records accepted narration stems/final media,
not an immutable standalone `af_heart` voice-sample artifact. The earlier `am_michael` proof
sample is not English voice-registry authority.

No new core-locale sample was generated because no new provider/stock voice was owner-selected
or authorized for paid use. Their registry entries remain explicitly pending; no full 14-minute
dub was synthesized.

## Zero-rerender proof

Runtime report:

`.task-runtime/v2-zero-rerender-global-language-sidecar-correction-v1/zero_rerender_proof.json`

Executed operations:

- Remotion video renders: `0`
- 4K renders: `0`
- localized picture renders: `0`
- FFmpeg `-c:v copy` muxes: `1`
- caption sidecar writes: `3` (`JSON`, `SRT`, `VTT`)
- metadata sidecar writes: `1`
- MAX calls: `0`
- ULTRA calls: `0`
- public writes: `0`
- V1 mutations: `0`
- scheduler changes: `0`

Canonical Short picture SHA-256 remained
`e83878eb5f3efab30aed8385fc6c6d5ede7105b4ada0ce04f87c02033baa0430`.

Input and stream-copy output H.264 elementary/payload SHA-256 are identical:

`05b083870d3c8ea164eef971144aed48b916043b8b7a553310efcd26f1161775`

Caption proof passed ten cues with
`ACTUAL_PLACED_AUDIO_SEGMENT_DURATIONS`. Caption and metadata generation both record
`picture_render_required: false`.

## Package correction

Eight EN/ES/pt-BR/JA demonstration package manifests were rebuilt in the correction runtime.
For a given editorial format, every locale manifest hashes the same `canonical_picture`.
Burned-caption artifacts are `null`. Supplying one without later exact authority fails closed.

- Short canonical picture SHA-256 in all four packages:
  `e83878eb5f3efab30aed8385fc6c6d5ede7105b4ada0ce04f87c02033baa0430`.
- Longform canonical picture SHA-256 in all four packages:
  `9685471ef572aa324f55871502f65df7e351caf3b1d56590b30b765cdf069d96`.

YouTube delivery is one video identity plus creator-supplied alternate audio, timed captions and
localized metadata. Alternate-audio upload remains a YouTube Studio/eligibility-gated product
capability; no verified public Data API uploader is claimed. Other future platform-specific
localized MP4s must use the same H.264 picture with stream-copy muxing and no burned captions by
default.

## Remaining caveats

- The Qwen3-4B weights and local Transformers runtime are not materialized in this repository;
  actual translation quality/throughput remains a later local-runtime acceptance gate.
- New core-locale voices remain unselected and unaccepted. Provider authority and Jim listening
  review are required before sample generation or production routing.
- ElevenLabs is a capability route only; this task made no provider calls and recorded no cost.
- RTL caption presentation and platform-native behavior still require actual-media/platform QA
  when Arabic or Urdu is first activated.
- Publication adapters remain the next task after merge/acceptance. No upload is authorized here.
