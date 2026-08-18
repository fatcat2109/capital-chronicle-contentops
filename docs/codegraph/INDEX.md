# ContentOps CodeGraph Entry Index — Stale Guard

Status: `STALE_GENERATED_CONTEXT / DISCOVERY_ONLY`

The last generated CodeGraph snapshot in this repository was built from source HEAD:

`5701f1039a7f229f636d54bdf0a2133bb2bdcf23`

It predates the current authority epoch and must not route a task or override current GitHub source/evidence.

This file is intentionally a manual stale guard, not a regenerated graph. No generated graph bytes were fabricated during the 2026-08-19 documentation-only authority rewrite.

## Current read path

1. `AGENTS.md`
2. `docs/codegraph/INDEX.md` (this stale guard)
3. `docs/automation/CONTENTOPS_CURRENT_AUTHORITY_AND_SUPERSESSION_MAP_V1.md`
4. `docs/automation/CONTENTOPS_FINAL_PRODUCT_NORTH_STAR_V3.md`
5. `docs/automation/CONTENTOPS_FINAL_PRODUCT_MASTER_PLAN_V3.md`
6. `docs/codegraph/V1_CONTEXT.md` or `docs/codegraph/V2_CONTEXT.md` as discovery aids only until regenerated
7. current lane pointer
8. nearest scoped `AGENTS.md`
9. exact code/tests/evidence

## Existing discovery artifacts

The existing pre-rewrite graph artifacts remain useful for call-path/orientation only:

- `docs/codegraph/graph.json`
- `docs/codegraph/V1_CONTEXT.md`
- `docs/codegraph/V2_CONTEXT.md`

Their generated/currentness claims must be interpreted against their recorded source HEAD, not against the current date or file modification time.

## First future repo operation

Before implementation, synchronize to freshly fetched remote `master`, then run the repository's canonical CodeGraph generation/check workflow:

```text
python scripts/generate_codex_context_index.py
python scripts/generate_codex_context_index.py --check
```

Verify the regenerated graph/index/V1/V2 contexts all bind to the exact current source epoch before using graph results as implementation-impact evidence.

If regeneration/check fails, use exact current source/tests/evidence plus literal search as necessary and report the graph failure; do not silently treat this stale snapshot as current.
