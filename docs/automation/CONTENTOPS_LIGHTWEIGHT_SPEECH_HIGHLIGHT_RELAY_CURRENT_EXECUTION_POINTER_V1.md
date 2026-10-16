# ContentOps Lightweight Speech Highlight Relay — Current Execution Pointer V1

Authority date: 2026-10-17
Status: `CURRENT_RETAINED_REPLAY_REVALIDATION / PUBLICATION_HOLD`

## Boundary

This is a small, isolated relay slice. Main V2 remains `PAUSED_BY_OWNER`; this relay does not
resume V2 and does not add a second scheduler, store, publisher, browser role, provider route, or
public-write owner. The current implementation is the exact source at
`live_contentops/speech_highlight_relay_v1.py` and the explicit `speech-highlight-relay` CLI entry.

The slice selectively reconciles the useful local mechanics from historical PR50
(`85b70562da3c4b1502c15ac5993b526efc0f7477`) onto current master. PR50's seeded discovery,
hardcoded highlight path, provider fallback, and publisher-derived `REUSE_CLEAR` result are not
current authority and are not carried into this implementation.

## Retained replay input

The committed packet is
`video/speech_highlight_relay_v1/retained_replay_fed_20260729.json`. It binds the review to:

- retained media SHA-256 `4c2cd08ed327bec53300d8bc0bc170c16ba328a7af669b2240118fc956b7c1f9`;
- retained transcript PDF SHA-256 `be77d850144d99365ba8c92749ad21525e39eb3577d66d105ce0907a6656cb97`;
- source binding SHA-256 `9f3300d123d44cc5598baf23917e34cc796ac37782fcac574f7d6a551273cb61`;
- the frozen 4.485–27.900 second excerpt, duration 23.415 seconds.

The media and PDF remain local retained artifacts under `.task-runtime/` and are not committed.
The receipt below records their hashes and the package hashes. No fresh download was made.
The PDF is official text without embedded timing, so cue timing remains
`PROVISIONAL_DONOR_ALIGNMENT_REVIEW_REQUIRED`. Text matching is not audio verification.
The sanitized source probe is committed at
`video/speech_highlight_relay_v1/retained_source_probe_fed_20260729.json`.

## Rights and third-party boundary

The packet is `TRANSFORMATIVE_EDITORIAL_REVIEW_REQUIRED`, with
`legal_clearance_status=NOT_VERIFIED` and `production_eligible=false`. The historical donor
`REUSE_CLEAR` label is not promoted. The current policy page is retained as a URL only; no current
policy snapshot or legal clearance is claimed. The sampled visual review found the speaker and flag
in the selected excerpt. Full-frame continuity, reporter voice, and inseparable third-party audio
remain `UNKNOWN_REVIEW_REQUIRED`.

## Local proof receipt

Command:

```powershell
$env:PYTHONPATH=(Get-Location).Path
python -m live_contentops.speech_highlight_relay_v1 `
  --source-config video/speech_highlight_relay_v1/retained_replay_fed_20260729.json `
  --repo-root (Get-Location).Path `
  --output-dir .task-runtime/speech_highlight_relay_v1/package_current_replay_5
```

Observed result: `PASS_INTEGRITY_AND_FORMAT_PRIVATE_REVIEW_ONLY`, 23.415 seconds,
`PUBLICATION_HOLD`, `public_writes=0`, `unknown_writes=0`, `provider_calls=0`.

| artifact | SHA-256 | size |
| --- | --- | ---: |
| clean master | `9502cdfe5ac8d62b1140cd1e03f469a283ec39bce86e2f8d99875469c892b47a` | 5,401,957 |
| captioned derivative | `1b625cfa59cb10894197601fff7936515ada33739d3e16fafbc393232d0f11e8` | 5,486,030 |
| captions.srt | `d3af143351d8f77f83c7134b825e6dbca81fcd4e6fa82a75c6782e021a91c2fc` | 465 |
| captions.vtt | `0dcc25784546acf4880363b96214767078308b2b742fb93f7d5599779526d298` | 475 |
| captions.json | `2f21908bffcf11e28a23abb50789dd9bf2c4be64759fa3c63904a5fb454b0bc0` | 839 |

Both renders probe as 1080×1920 H.264 with 48 kHz stereo AAC and 23.415 seconds. The actual
rendered frames were inspected at 0, 5, 10, 16 and 22 seconds. Audio listening is
`NOT_VERIFIED` because this execution surface cannot receive audio input; the package deliberately
does not claim an audiovisual PASS. Local decode and spectral inspection found a present, non-silent
AAC stream (`mean_volume=-31.4 dB`, `max_volume=-13.0 dB`); that does not verify words, speaker,
timing or third-party audio.

## State and next gate

- Implemented: retained packet, fail-closed validation, local clip extraction, clean/captioned render,
  SRT/VTT/JSON sidecars, hashes, package verification, CLI and focused CI test hook.
- Tested: six focused boundary tests passed; local render and verifier passed.
- Integrated: CLI and `ci-fast` hook merged into current `master` via PR58 at
  `12666f7c9e40e8b3fce7044eef71c93120fa332d`.
- Merged: yes, PR58 exact head `42a67df84ad3b7176411f9cfd4b20501ffae7d77`; deployed: not verified.
- Render-reviewed: visual review complete; audio listening, timing, third-party continuity and legal
  clearance remain open.

The next command for a future local rerun is the command above. Any production or public-destination
use requires a separate owner decision after current rights, timing, third-party and audio review.
