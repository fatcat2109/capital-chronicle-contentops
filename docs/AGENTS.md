# `docs/` — Authority, Evidence, and Generated Context

Documentation has three distinct roles:

1. current authority/direction (`CURRENT_CONTEXT.md`, current overlays, next-task pointer);
2. immutable or historical evidence under `docs/automation/`;
3. generated descriptive context under `docs/codegraph/`.

Do not let generated indexes become product authority. Do not rewrite accepted evidence or old
plans merely to make them agree with newer direction; record supersession in current authority
surfaces when explicitly tasked.

`docs/codegraph/graph.json`, `docs/codegraph/INDEX.md`, and `docs/codegraph/V2_CONTEXT.md` are
deterministic generated outputs. `docs/codegraph/V1_CONTEXT.md` is the curated current V1 map;
the generator validates its routed paths and includes it in freshness hashing. Regenerate with
`python scripts/generate_codex_context_index.py`; do not hand-edit generated outputs.

Exclude archives, runtime outputs, vendor trees, generated media, and broad historical evidence
noise from the codegraph. Never commit secrets, signed URLs, browser/session material, or raw
provider responses.

Current production navigation evidence is limited to the continuous-intelligence realignment,
preselection closeout, first real 5–8 production-day attempt, and current FDA-G routing linked
from `V1_CONTEXT.md`. Do not rewrite accepted packets; update current routing surfaces only when
the owner explicitly changes direction. Search the graph for `authority_doc` or
`authority_anchor_paths`.
