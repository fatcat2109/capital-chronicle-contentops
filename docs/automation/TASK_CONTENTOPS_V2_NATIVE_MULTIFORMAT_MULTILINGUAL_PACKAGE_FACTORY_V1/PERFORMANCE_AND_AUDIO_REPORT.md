# Performance and Audio Report

## Local audio path

All demonstrated narration used local `kokoro-onnx 0.4.9` with the same governed model and
voice bundle. There were no cloud TTS calls, no paid inference calls, no SAPI use, and no
real-person voice cloning.

| Locale | Voice | G2P | Final Short speed | Spoken end | Final sample SHA-256 |
|---|---|---|---:|---:|---|
| en | `am_michael` | espeak-ng via Kokoro | 1.45 | 56.493s | `cb6f9107129416c6355680e6ec6c44ab5723ee2a2c1939571f83c1afe6300785` |
| es | `ef_dora` | espeak-ng via Kokoro | 1.45 | 56.856s | `85cf6b1669e93a69085b98c815024099c6c724238cceb2ba529807eb701605ce` |
| pt-BR | `pf_dora` | espeak-ng via Kokoro | 1.65 | 57.453s | `cb8b73867dc067d9b686f76b0edf6bd60607d95681b133d2300c55b9de5085ae` |
| ja | `jf_alpha` | Misaki Japanese 0.8.4 | 1.80 | 57.044s | `174aef4b12ac2cb93bedc41acc9517a4ae7a52dc9030eed8052a854d69055d6e` |

Representative samples run 20–27 seconds. These voice and speed choices are implementation
proofs only. `JIM_LISTENING_GATE_REQUIRED` remains mandatory.

## Measured local runtime

- Initial full localized synthesis/bus assembly: ES 231.06s, pt-BR 279.12s, JA 257.187s.
- Final cache-aware Short updates after terminology repair: ES 33.772s, pt-BR 39.548s,
  JA 40.725s.
- Full English audio/caption payload: 262.054s.
- Final four-picture Remotion pass ran concurrently on local CPU and completed in roughly
  17 minutes; the three burned-caption variants completed before the shared clean picture.
- Final seven audio muxes completed in about 6 seconds wall-clock when run concurrently.

These timings are workstation-specific and include local filesystem/cache effects. They are
evidence for this run, not a throughput SLA.

## Cost estimate

- TTS provider spend for this proof: `$0.00`.
- Marginal inference/API spend recorded by the deterministic audio layer: `$0.00`.
- Costs not claimed here: workstation electricity, Codex plan/quota consumption, human review,
  and any future platform/provider charges.

The TTS cache identity binds locale, voice, speed, synthesis revision, text, model SHA-256,
and voice-bundle SHA-256. Re-running unchanged segments is therefore content-keyed rather than
silently reusing language-only state.
