# `scripts/` — Operator and Repository Tooling

This scope owns thin operator launch helpers and offline repository tooling. It must not become a
second product runtime, scheduler, publisher, durable store, or provider gateway.

- `Start-ContentOpsDailyApp.ps1` delegates to
  `live_contentops.daily_app_launcher_v1`; keep it decision-free and idempotent.
- `generate_codex_context_index.py` deterministically creates `docs/codegraph/graph.json`,
  `INDEX.md`, and `V2_CONTEXT.md`, and validates the curated `V1_CONTEXT.md`.

Never add secret/session inspection, live database mutation, browser automation, or public writes
to context tooling. Preserve explicit exclusions for Runtime, raw headline data, historical
evidence noise, caches, media, vendors, and build output. Validate generator changes with
`tests/test_codex_context_index.py`, a real generate, then `--check`. Search graph inference types
`entrypoint_to_implementation` and `agents_directory_scope`.
