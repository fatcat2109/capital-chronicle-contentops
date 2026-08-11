# `docs/` — Authority, Evidence, and Generated Context

Documentation has three distinct roles:

1. current authority/direction (`CURRENT_CONTEXT.md`, current overlays, next-task pointer);
2. immutable or historical evidence under `docs/automation/`;
3. generated descriptive context under `docs/codegraph/`.

Do not let generated indexes become product authority. Do not rewrite accepted evidence or old
plans merely to make them agree with newer direction; record supersession in current authority
surfaces when explicitly tasked.

`docs/codegraph/graph.json` and `docs/codegraph/INDEX.md` are deterministic generated outputs.
Regenerate them with `python scripts/generate_codex_context_index.py`; do not hand-edit them.
`docs/codegraph/V2_CONTEXT.md` is the compact curated V2 routing map and is validated alongside
the generated graph.

Exclude archives, runtime outputs, vendor trees, generated media, and broad historical evidence
noise from the codegraph. Never commit secrets, signed URLs, browser/session material, or raw
provider responses.
