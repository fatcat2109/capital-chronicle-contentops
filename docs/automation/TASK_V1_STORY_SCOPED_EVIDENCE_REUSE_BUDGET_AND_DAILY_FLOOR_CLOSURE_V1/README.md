# V1 Story-Scoped Evidence Reuse, Budget, and Daily-Floor Closure

Authority date: 2026-08-21
Task: `TASK_V1_STORY_SCOPED_EVIDENCE_REUSE_BUDGET_AND_DAILY_FLOOR_CLOSURE_V1`
Starting SHA: `3f020469731a5763226b2c48f16f5290b50ebe35`
Parent product commit: `73b2be822ca0920a4f063ac3b561d6c322ab1754`
Classification: `DEGRADED_DAILY_OUTPUT_DEFICIT`

## Outcome

The verified duplicate-acquisition defect is closed without raising either request ceiling or weakening any evidence/publication gate.

For one immutable story/update chain at one evaluation cutoff and authority binding, the selector now acquires evidence once. Lower editorial modes deterministically re-evaluate the same documents, hashes, provenance, and grounded-research result. A new transport call is permitted only for an explicit capability/source/query delta and continues the same story ledger.

Reuse is rejected across a different story, update chain, material-update binding, cutoff, or assignment-authority binding. Reuse grants no factual, numeric, permission, or publication authority.

## Implementation

- `newsroom_assignment_scheduler_v1.py` binds a story-scoped acquisition ledger and reports per-mode `INITIAL_ACQUISITION`, `REUSED_STORY_SCOPED_EVIDENCE`, or `BOUNDED_DELTA_ACQUISITION` actions.
- `public_secondary_evidence_loader_v1.py` preserves the per-story allowance across calls and reuses a successful exact URL/query signature inside the same story scope without a network read.
- `official_primary_evidence_loader_v1.py` reuses exact official bytes only for an identical story/cutoff/family/binding signature.
- `grounded_news_research_v1.py` scopes successful research reuse to acquisition inputs rather than editorial mode and reports zero current calls/reads on reuse.
- `run_v1_current_multi_frontier_floor_rehearsal.py` emits story/mode request economics and can replay one exact committed frontier artifact.

No second evidence system, crawler, cache database, newsroom, scheduler, store, or publication path was created.

## Before/after request economics

The parent genuine four-frontier run attempted 14 stories and exposed 37 public plus 6 official requests in terminal receipts. All four frontiers ended `EVIDENCE_REQUEST_BUDGET_EXHAUSTED_BEFORE_PUBLISHABILITY_POOL_CLOSURE`. Parent accounting did not separately expose overwritten richer-mode acquisition, so those 43 reads are a lower-bound observation rather than a complete duplicate-read ledger.

The exact committed four-frontier artifact replay after the repair attempted 13 distinct stories:

- 55 public + 12 official = 67 actual reads;
- 82 same-story mode-downgrade reads avoided;
- 0 delta acquisitions;
- 0 global request-budget exhaustion;
- 0 evidence-qualified stories, XHIGH calls, articles, or derivative intents;
- 0 public/provider writes and `UNKNOWN_WRITE=0`.

One default-route provider failure and one retry caused by a misnamed process-local incident-expiry variable are preserved as diagnostics. Successful replay used the repository's short-lived `PRO_ONLY` incident seam; production routing defaults were not changed.

## Genuine current production-day rehearsal

The current-input run froze 897 headlines at one cutoff and completed exactly four zero-write frontiers:

- 17 distinct stories attempted;
- 71 public reads, 0 official reads, 71 total actual reads;
- 89 same-story downgrade reads avoided across 22 reuse-mode attempts;
- 0 repeated URL/query-signature network calls;
- 0 delta acquisitions;
- 6 truthful per-story allowance exhaustions and 0 global exhaustion;
- 0 evidence-qualified stories;
- 0 XHIGH calls because no story reached the article boundary;
- 0 qualified articles and 0/32 derivative intents;
- 0 public writes, 0 publication-provider writes, `UNKNOWN_WRITE=0`;
- 0 production-store resets and no fifth Automation.

The production-day result is therefore `DEGRADED_DAILY_OUTPUT_DEFICIT`, not `BLOCKED`: the 4/32 build floor was missed, but no hard system/external blocker prevented the bounded four-opportunity proof.

## Forensic second phase

The exact 17-row residual matrix is in `closure_evidence_summary_v1.json`. Its material categories are:

- exact first-party source-family/official-locator gaps for EIA storage, Philly Fed, State/DSCA, and USCC stories;
- a company-primary locator gap for Waymo;
- access-controlled or dead public candidates with no accepted authorized alternative;
- five true bounded per-story exhaustions after reuse;
- query/event-core or public-source availability misses;
- proprietary research/commentary claims that were not publicly bound.

No additional source-family fix was made. The currently registered official locator families do not authorize those first-party surfaces, and this task supplied no authority to add them generically. Access controls were not bypassed, model/X text was not promoted, and unsupported commentary remained excluded.

## Evidence and validation

The closure packet is `closure_evidence_summary_v1.json`. It binds the parent comparison, four committed replay summaries, genuine current summary, provider diagnostics, request reuse truth, safety counters, and the residual source/reachability matrix by portable SHA-256.

Focused and wider regression validation completed before the live proof:

- focused reuse/loader/research/runner suites: 91 passed;
- broader newsroom/evidence/publication regression: 215 passed;
- runner-specific follow-up: 46 passed, then 8 passed.

Final validation, regenerated CodeGraph/context checks, branch commit/push, and exact-head `ci-fast` are recorded in the task handoff after completion.

## Next exact product gate

Authorize only the exact first-party locator/source-family contracts demonstrated by the residual matrix, beginning with the sourceable official-release stories, then repeat the same four-frontier zero-write floor rehearsal. Do not raise budgets, relax gates, create a fifth Automation, or enable public writes while the 4/32 build floor remains unproven.
