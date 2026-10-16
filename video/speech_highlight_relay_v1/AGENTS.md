# Speech Highlight Relay scope

This directory is an isolated retained replay lane. Its current pointer is
`docs/automation/CONTENTOPS_LIGHTWEIGHT_SPEECH_HIGHLIGHT_RELAY_CURRENT_EXECUTION_POINTER_V1.md`.

- Use only an explicit retained source packet and a frozen excerpt.
- Do not restore PR50 seeded discovery, hardcoded quote selection, provider calls, or
  publisher-derived rights clearance.
- Keep media and PDF inputs under local `.task-runtime/` output; commit hashes, probes and
  provenance only.
- Every local package remains `PUBLICATION_HOLD`, `ZERO_PUBLIC_WRITE`, and
  `production_eligible=false`.
- Do not add a scheduler, store, publisher, browser session, external upload, public draft or
  runtime mutation here.
- Render review must inspect actual frames. Audio listening, transcript timing, third-party
  continuity and legal clearance stay explicitly unverified until independently proven.
