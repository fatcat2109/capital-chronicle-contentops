# V1 real daily yield recovery — implementation and replay evidence

Task: `TASK_CONTENTOPS_V1_REAL_DAILY_YIELD_RECOVERY_AND_SAME_OPPORTUNITY_CANDIDATE_WALK_V1`

Starting master: `70987dfe83e1c623a19b86e58ede20be6d584e09`

## Diagnosis

Read-only reconstruction found four completed Aug. 15 Jim-local scheduled opportunities before
implementation. The 01:00, 04:00, and 12:00 windows each exhausted all 12 ranked candidates at
evidence acquisition. The 14:00 window stopped after rank 1 became evidence-viable and its writer
output failed reader value; 11 ranked candidates remained unattempted.

The 14:00 article was not rejected merely because it missed a 90-word target by eight words. It
was one 82-word paragraph made primarily of three source-title/attribution restatements. Hard
factual/safety review passed and mandatory semantic-review calls were zero, but the copy lacked a
distinct reader payoff. The corrected gate retains that rejection as `not_attribution_chain_copy`
while making paragraph, heading, and preferred word targets advisory.

## Correction

- Resume the immutable ranked pool after candidate-local evidence, builder, writer, or reader-value
  failure.
- Stop after the first publication-qualified candidate or after truthful bounded exhaustion.
- Preserve global router/cost/safety stops and one-publication maximum per opportunity.
- Keep ordinary reporting at one writer call per attempted evidence-viable candidate and zero
  mandatory semantic-review calls.
- Persist compact per-candidate ranks, titles, evidence/writer results, exact terminal reasons, the
  selected candidate, and the opportunity terminal reason in the existing cycle evidence.

## Exact replay

The exact frozen 14:00 viability and writer artifacts were replayed with an isolated cost ledger
and `publication_enabled=False`. Rank 1 remained rejected for genuine attribution-chain copy. The
corrected opportunity then walked ranks 2–12; every later candidate was truthfully evidence-blocked.
Final result: `ALL_BOUNDED_CANDIDATES_EXHAUSTED`, attempted `12/12`, public writes `0`, unknown
writes `0`, mandatory semantic-review calls `0`.

The exact frozen 01:00, 04:00, and 12:00 opportunities were also replayed. Each remained a truthful
`ALL_RANKED_CLUSTERS_EVIDENCE_BLOCKED` with `12/12` candidates attempted and zero writes.

Machine-readable reconstruction, every rank/title/blocker, before/after reader checks, and replay
telemetry: `aug15_reconstruction_and_replay_v1.json`.

## Safety

No production database mutation, synthetic trigger, browser publication action, V2 mutation, or
secret/session inspection occurred during diagnosis or replay.
