# Maintainer Findings

## What should stay reusable

- Keep locale support registry-driven. New locales should add a profile plus governed editorial
  payload; they should not create a new renderer or orchestrator.
- Keep picture, audio, captions, metadata, and transport as separate package artifacts. This
  made it possible to prove unchanged picture bytes and prevents provider choices from leaking
  into editorial identity.
- Keep caption timing bound to actual synthesized segment durations. Text-length estimates are
  not sufficient across Spanish, Portuguese, and Japanese.
- Keep the factual-anchor contract attached to viewer-facing surfaces, including compact labels.
  The first actual-media pass found that a visually plausible abbreviation could still broaden
  an official measure beyond its governed scope.

## Bottlenecks observed

1. Full Remotion renders dominate local wall time. One shared clean picture plus locale-specific
   burned-caption pictures is the correct current split; do not render four identical clean
   pictures.
2. Terminology repair can change narration length enough to breach the 58-second gate. Run the
   factual-label alignment before final sample selection and reserve at least one second of tail.
3. Japanese needs a real Japanese G2P path. Generic espeak output was rejected during preflight;
   the proof therefore pins Misaki Japanese 0.8.4 and records it in receipts.
4. Windows Remotion public-asset traversal is more reliable with an explicit staged public
   directory than with a directory junction. The renderer should continue receiving a governed
   `--public-dir` rather than discovering arbitrary local assets.
5. Short-only synthesis receipts describe that invocation and may omit an already-built
   longform payload. The package builder correctly hashes the actual longform files directly;
   a future ergonomic improvement could emit separate immutable per-format receipts.

## Recommended next improvements

- Add deterministic caption line-width/reading-speed diagnostics as advisory evidence before
  expensive burned-caption renders; retain actual-media review as authority.
- Persist render wall-time and peak-memory telemetry automatically in the render receipt.
- Add a first-class per-format audio receipt so cache-update runs never obscure the earlier full
  build record.
- Keep platform constraints in a maintained contract document and validate package geometry
  against the chosen future surface only at transport time. Platform requirements change more
  frequently than content identity.
- Before onboarding another CJK locale, require a language-native G2P preflight and a human
  pronunciation gate; do not infer support from Unicode rendering alone.
