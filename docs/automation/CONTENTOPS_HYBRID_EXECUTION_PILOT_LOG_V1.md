# ContentOps Hybrid Execution Pilot Log V1

Authority date: 2026-08-19
Status: `PILOT_EVIDENCE_ONLY`

This log measures execution-lane utility. It does not alter product authority or sequence.

| # | Task | Lane | Codex used | Validation | Result | Notes |
|---|---|---|---|---|---|---|
| 1 | Establish ContentOps Web/GitHub/Actions execution path | `WEB_STATIC -> WEB_CI` | No | `ci-fast` run `32248818022`; 11 CodeGraph tests; compile; diff hygiene | PASS | Proved Actions feedback loop on target repo with read-only token scope. |
| 2 | Reconcile hybrid execution authority candidate | `WEB_STATIC -> WEB_CI` | No | `ci-fast` run `32250173271`; 11 CodeGraph tests; compile; authority assertions; full branch diff hygiene | PASS | Root candidate now routes by evidence capability while preserving product/truth/public-write boundaries. |
| 3 | Reconcile accepted P0 lineage, current pointers, and CodeGraph source epoch | `WEB_STATIC -> WEB_CI` | No | Internal PR #2 merged only into integration branch; draft PR #3; exact-head CI isolated stale CodeGraph; branch-only refresh commit `20e717f32cfa712a274dc1007de1de8b818cb074`; final deterministic CI triggered by this evidence checkpoint | IN_PROGRESS | Unified accepted P0 source/evidence with hybrid execution without master mutation; final green head still required before closing this row. |

Pilot counting rule: count only real eligible engineering work. Do not invent tasks to reach a quota. A task that correctly escalates to Codex is useful pilot evidence rather than a failure of the method.
