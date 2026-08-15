# V1 grounded-research yield and budget-aware evidence recovery

Result: `PASS_V1_GROUNDED_RESEARCH_YIELD_RECOVERED`

## Authority and integration

- Starting remote master: `70987dfe83e1c623a19b86e58ede20be6d584e09`.
- Accepted parent: `codex/v1-real-daily-yield-recovery-v1` at `1a0029d0a01c77ae11b164904b0343489801dd25`, verified one commit ahead and zero behind the starting master.
- Integration: accepted parent fast-forwarded to remote `master`; exact remote readback was `1a0029d0a01c77ae11b164904b0343489801dd25`. The canonical checkout was safely fast-forwarded without disturbing unrelated dirty/untracked work. Production was not restarted because it already executed identical accepted bytes.
- New isolated branch: `codex/v1-grounded-research-yield-budget-aware-evidence-recovery-v1`, created from integrated master.
- Protected `v1.0`: annotated tag object `a021df7fd0264d9f160bdd605509da925f0bf131`, peeled immutable commit `6983bfb3ef300414b744f3f8f97ca81ff699348b`.

## Exact 17:00 historical reconstruction

Source opportunity: `editorial-window-e80bb6a6cbb69b2a206a3fff5c2105ac`, cutoff `2026-08-15T10:00:00.000529Z` (17:00 Jim-local), 839 current headlines, 12 frozen ranks, 12 attempted, zero writer calls, zero public writes.

The canonical ledger retained only six reserved logical IDs and aggregate cycle totals. The pre-correction research summary read the wrong router fields, recorded accepted planner summaries with provider count `0`, and dropped terminal non-accepted summaries. Therefore per-invocation provider-attempt/model/token allocation and the intended IDs of calls rejected before reservation are not safely recoverable. Those values are explicitly marked unavailable rather than inferred.

Cycle governor before correction and after correction remains:

- hard logical calls: 6;
- hard provider attempts: 12;
- hard accounted tokens: 250,000.

Historical final ledger state: 6 logical reservations, 12 provider attempts, 162,381 accounted tokens.

| Rank | Query-plan logical ID / reservation | Historical budget transition | Retrieval | Synthesis / binding | Exact safe conclusion |
|---:|---|---|---|---|---|
| 1 | `v1_research_plan_c4c3779c4211013b5a4f`; reserved | starts `L0/P0/T0`; ends rank with `L2`; per-rank P/T not persisted | 6 cumulative requests; accepted count not persisted, but synthesis proves at least one record existed | `v1_research_synthesis_c4c3779c4211013b5a4f` reserved; terminal summary dropped | generic synthesis/unbound masked the exact terminal class |
| 2 | `v1_research_plan_0f275a8a002b60431e5c`; reserved | starts `L2`; after rank `L4`; P/T allocation not separable | 11 cumulative cycle requests; accepted count not persisted, but synthesis proves at least one record existed | `v1_research_synthesis_0f275a8a002b60431e5c` reserved; terminal summary dropped | generic synthesis/unbound masked the exact terminal class |
| 3 | `v1_research_plan_bf2b7925ae32aab5428b`; reserved | `L4→L5`; provider/token delta not separable | 0 | not invoked | planner terminal detail was dropped; no evidence conclusion is justified |
| 4 | `v1_research_plan_5c6803b05d5cefeaec9c`; reserved | `L5→L6`; by end state was `L6/P12/T162381` | 0 | not invoked | planner terminal detail was dropped; no evidence conclusion is justified |
| 5–12 | intended ID not persisted; reservation denied | unchanged `L6/P12/T162381` | 0 each | not invoked | proven structural `llm_cycle_logical_call_budget_exhausted`, historically masked as query-planning unavailable |

The exact provider-attempt distribution among ranks 1–4 cannot be reconstructed from retained sanitized evidence. The ordered four-model pool shown in accepted planner summaries is policy order, not proof that every listed model received a network attempt. The aggregate proves that the provider-attempt ceiling was also reached by the end of rank 4, but does not safely assign that terminal event to a particular rank.

## Proven root causes

1. Every ordinary candidate paid for an LLM query plan before any public retrieval. Two model stages per source-bearing candidate made a six-logical-call cycle structurally incompatible with a twelve-rank diagnostic walk.
2. Once six logical reservations existed, ranks 5–12 were rejected before retrieval. This was infrastructure starvation, not genuine missing evidence.
3. Router summary field mismatches (`provider_attempt_count`/`token_usage` instead of `total_attempts`/`total_usage`) and discarded non-accepted summaries collapsed exact failures into generic planner/synthesis blockers.
4. Strict synthesis/source binding can legitimately reject model JSON. The prior route had no bounded structured repair reserved for the final viable model.

## Corrected flow

Before:

`candidate → LLM query plan → public retrieval → LLM synthesis → source binding → writer`

After, ordinary non-disputed story:

`candidate → deterministic neutral locator from proposition/entities/bound hosts → bounded existing public retriever → zero model calls when no documents → one bounded source synthesis when documents exist → unchanged source binding → writer`

Enhanced-risk stories retain the LLM plan and one bounded replan. The existing retriever, normalization, minimum trustworthy packet, hard evidence filter, CC authority, and publication gates remain authoritative. Query text and model assertions grant zero factual authority.

The global ceilings were not raised. A successful ordinary first candidate now consumes one research logical call; the zero-write smoke consumed one additional writer call. A global logical/provider/token or authorized-model-pool breaker now stops the candidate walk as `INFRASTRUCTURE_BUDGET_OR_PROVIDER_EXHAUSTED`; candidate-local evidence failures continue to the next rank.

## Exact frozen replay after correction

Canonical artifact: `exact_1700_zero_write_replay_final/grounded_research_vertical_slice_evidence_v1.json`.

The exhaustive diagnostic replay used durable per-candidate checkpoints/scopes so every frozen rank could be exercised without one diagnostic rank hiding later source outcomes. Normal production semantics still stop at the first viable candidate; this exact set would stop at rank 1 and remain inside the unchanged 6/12/250,000 cycle envelope.

| Rank | Result | Plan calls | Retrieval requests / accepted | Synthesis calls | Provider attempts / tokens | Exact terminal evidence |
|---:|---|---:|---:|---:|---:|---|
| 1 | PASS | 0 | 5 / 3 | 1 | 2 / 11,291 | minimum trustworthy packet |
| 2 | PASS | 2 | 6 / 1 | 1 | 3 / 12,866 | minimum trustworthy packet; one inaccessible listing did not negate the accessible FT record |
| 3 | BLOCKED | 0 | 3 / 0 | 0 | 0 / 0 | HTTP 403; no accepted record |
| 4 | BLOCKED | 1 | 4 / 1 | 1 | 2 / 7,946 | enhanced-risk support insufficient; facts removed by unchanged hard evidence filter |
| 5 | BLOCKED | 0 | 3 / 0 | 0 | 0 / 0 | published timestamp unavailable |
| 6 | BLOCKED | 0 | 3 / 0 | 0 | 0 / 0 | published timestamp unavailable |
| 7 | BLOCKED | 2 | 6 / 0 | 0 | 8 / 7,611 | HTTP 403; no accepted record |
| 8 | BLOCKED | 2 | 6 / 2 | 1 | 4 / 18,537 | exact synthesis diagnostic: `grounded_research_source_synthesis_research_core_proposition_not_supported` |
| 9 | BLOCKED | 0 | 2 / 0 | 0 | 0 / 0 | public source unavailable |
| 10 | BLOCKED | 0 | 2 / 0 | 0 | 0 / 0 | public source unavailable |
| 11 | BLOCKED | 0 | 2 / 0 | 0 | 0 / 0 | public source unavailable |
| 12 | BLOCKED | 0 | 2 / 0 | 0 | 0 / 0 | public source unavailable |

Replay totals: 44 bounded public requests, 7 enhanced-risk plan/replan calls, 4 source-synthesis calls, 19 provider attempts, 58,251 accounted research tokens, and 2 evidence-qualified candidates. No unexplained generic planner or synthesis blocker remains.

Qualified source identities are bound in the canonical JSON by exact URL, source ref, document ID, and publisher:

- rank 1: Reuters (`SRC_D9D7CE4F7636AC54`, `public-news-listing-58f4eac22670931ba463`), MarketWatch (`SRC_4A31DD33EA3B34DA`, `public-news-listing-d3b70f798c5e4fe8f63b`), CNN (`SRC_E96EFCFE6F407346`, `public-news-listing-6e7cd95f14205ff02412`);
- rank 2: Financial Times (`SRC_D272C590604D0A5E`, `public-news-listing-0511e2e5bbb6bdffc6da`).

## Zero-write end-to-end result

Rank 1 ran through the normal writer and deterministic factual/safety/reader-value path:

- one writer call; 8,979 tokens; no ordinary semantic-review call;
- title: `US retail sales post first decline in nine months in July`;
- 81 words;
- factual gate: `PASS`;
- reader-value gate: `INSUFFICIENT_READER_VALUE`;
- editorial status: `NO_PUBLICATION`;
- release preparation: `BLOCKED_TEXT_IMAGE_RELEASE_CANDIDATE_REHEARSAL`;
- publication plan destinations: 1;
- public writes: 0;
- publishing adapter/coordinator calls: false/false;
- unknown write: 0;
- pending reconciliation: 0.

This is the task-authorized truthful later-stage rejection: research yield recovered and factual grounding passed; the product correctly refused to manufacture a low-value publication.

## Validation and safety

- Focused suite: 195 passed.
- Exact replay classification: `PASS_V1_GROUNDED_RESEARCH_YIELD_RECOVERED`.
- CodeGraph regeneration/check: `CODEGRAPH_CURRENT`.
- Deployment: NO. The new implementation remains isolated for owner/ChatGPT audit, as required; production was neither restarted nor mutated.
- First natural post-deploy opportunity: not applicable.
- Canonical publication/readback: none created by this task.
- Synthetic triggers: 0.
- Synthetic X captures: 0.
- Test public writes: 0.
- V2 mutations: 0.
- Secret/session exposure: 0.

Caveats: replay provider availability required the repository's existing process-local, expiring `PRO_ONLY` build-acceptance incident seam; production configuration was not changed. Pytest exited 0 but Windows emitted its known post-run temporary-directory cleanup `PermissionError` after reporting success.

Exact next action after owner/ChatGPT audit: merge the dedicated branch, deploy at a proven idle boundary, and observe the first natural opportunity toward `ACHIEVE_AND_MEASURE_REAL_USEFUL_CANONICAL_ARTICLE_YIELD_TOWARD_5_8_PER_ACTIVE_DAY_WITH_ASYNC_FANOUT_TO_ALL_READY_AUTHORIZED_DESTINATIONS`.
