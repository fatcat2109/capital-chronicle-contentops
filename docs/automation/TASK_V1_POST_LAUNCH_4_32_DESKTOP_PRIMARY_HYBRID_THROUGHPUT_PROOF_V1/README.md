# V1 post-launch 4/32 Desktop-primary hybrid throughput proof

Terminal result: `DEGRADED_DAILY_OUTPUT_DEFICIT / FAIL_4_32_FLOOR_NOT_MET`.

The bounded newsroom day completed all four routine opportunities with 0 qualified articles and
0 derivative intents. The requested 4/32 success classification is forbidden. No filler article
was manufactured and no public write occurred.

The proof bound the canonical durable continuity and three confirmed canonical publications in
read-only mode. The published Italy canary matched exactly once and was excluded from duplicate
production. Across the four current-input frontiers, the pipeline attempted 40 distinct stories
covering 46 current headline identities without repetition. It performed 117 source requests,
avoided 82 additional story-scoped reads through reuse, and made two delta acquisitions.

Frontiers 1-3 exhausted their bounded evidence-request budgets without reaching an article
boundary. Frontier 4 reached one governed article boundary. Exactly one fresh isolated
`gpt-5.6-sol / XHIGH` worker returned an article and the same worker performed the sole permitted
revision. The revised article passed deterministic editorial validation, but the required semantic
gate failed or was unavailable. The candidate terminalized as
`EDITORIAL_WORKER_REVISION_BUDGET_EXHAUSTED`; the remaining same-opportunity candidates were then
walked until the frontier evidence budget exhausted. SDK fallback, direct SDK use, and arbitration
were all zero because the native path was neither unavailable before invocation nor racing.

The four V1 Automations remain `PAUSED`; no fifth V1 Automation exists. `UNKNOWN_WRITE`, public
writes, publication-provider writes, and production-store resets are all zero.

Primary evidence:

- `final_throughput_proof_receipt_v1.json` — compact terminal statistics, routing, timing, token,
  cost-exposure, safety, and failure classification.
- `multi_frontier_floor_rehearsal_summary_v1.json` — canonical harness summary.
- `candidate_blocker_ledger_v1.json` — exact candidate title/identity and terminal blocker for all
  40 attempted stories.
- `newsroom_production_day_v1.json` — canonical terminal production-day record.
- `current_durable_state_readonly_v1.json` — read-only continuity and published-memory binding.
- `frontier_*/` — prepared states, routing/evidence records, XHIGH requests/returns, revision
  contract, and canonical zero-write rehearsals.

There are no qualified article or eight-intent artifact paths to report because no article crossed
the full qualification gate. This absence is part of the failure evidence, not an omitted output.
