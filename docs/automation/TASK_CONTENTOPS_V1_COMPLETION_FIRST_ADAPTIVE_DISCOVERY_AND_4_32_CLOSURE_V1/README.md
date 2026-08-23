# V1 completion-first adaptive discovery and 4/32 closure

Authority date: 2026-08-24

Final classification:
`BLOCKED_STAGE_A_GENUINE_EXTERNAL_PROVIDER_USAGE_LIMIT / STAGE_B_NOT_AUTHORIZED`

## Repository identity

- repository: `fatcat2109/capital-chronicle-contentops`;
- fresh master: `c4239a96513c24fc9f7f331025386756d0248569`;
- starting branch head: `0d99cf7038ec6ad852b81d7e408fa2c8c835dd17`;
- implementation commit before the runtime proof:
  `b29ee336a5982e20af7cbc06774a996d3527a0dd`;
- continuation branch: `codex/v1-quota-efficient-batch-tail-discovery-v1`;
- PR: `#19`.

## Implementation

The canonical quota-efficient session now uses a completion-first adaptive allocation policy.
The development proof receives one unified 24-turn / 18,000,000-token / 384-request emergency
envelope. It stops at four governed candidates or genuine exhaustion and prefers productive fresh
unseen batches. TAIL is eligible only after deterministic resume proves both a previously
discovered eligible URL and a concrete access/status failure; returned tail URLs must be distinct
from prior URLs.

Production defaults remain the prior bounded values and the development envelope is not promoted
as production policy. Deterministic retrieval, hashing, freshness, evidence admission, claim
binding, source/publisher policy, Capital Chronicle/numeric authority, permission, and all public
write gates are unchanged.

Receipts now persist URL resolution, ready-candidate gain, tokens, deterministic requests, and
marginal URL/ready yield per turn, plus exact tail eligibility and allocation decisions. The exact
discovery contracts are carried across production-day frontiers so a justified later tail can
request a genuinely distinct route without rediscovery.

## Stage A runtime result

The proof froze one fresh 24-hour universe at `2026-08-23T22:41:06.340945Z` for
`newsroom-production-day-2026-08-24-bangkok`:

- frozen universe: 126 headline identities;
- deterministic pre-discovery progression: 10 distinct stories / 12 distinct headlines;
- remaining held universe: 114 headline identities;
- governed ready candidates: 0;
- completed discovery turns: 0 BATCH / 0 TAIL;
- accounted discovery tokens: 0;
- deterministic read-only requests: 18;
- provider failure: `CHATGPT_USAGE_LIMIT_REACHED`;
- provider turn completed: false.

The authenticated `OfficialCodexUrlDiscoveryProvider` stopped before completing the first BATCH
turn. No source URL or model output was admitted as evidence. Because this is an explicitly
permitted genuine external dependency stop, the proof was not retried and the still-useful frozen
universe was not declared exhausted.

The raw aggregate receipt was written before a receipt-only classification correction and therefore
retains its original generic `FAIL_V1_EVIDENCE_READY_POOL_NOT_ACCEPTED` label. Its exact blocker,
provider failure record, zero completed turns, and safety counters are internally consistent. The
runner now deterministically classifies the same pre-turn provider condition as
`CURRENT_HOST_RUNTIME_PROOF_REQUIRED`; the task-level truthful classification remains the more
specific external-provider blocker above.

## Stage B

Stage A did not reach four governed candidates, so the conditional existing 4/32 proof was not
authorized or started:

- qualified zero-public-write articles: 0;
- derivative intents: 0;
- HIGH/XHIGH article-worker receipts: 0;
- public/provider writes: 0;
- `UNKNOWN_WRITE`: 0.

## Validation and safety

- focused affected suite: 223 passed;
- focused post-runtime classification regression: 36 passed;
- compileall: PASS;
- CodeGraph generation/check: `CODEGRAPH_CURRENT`;
- `git diff --check`: PASS;
- writer/article/derivative generation: `0 / 0 / 0`;
- public/provider writes: `0 / 0`;
- browser/CDP publication actions: 0;
- Automation / Capital Chronicle / V2 mutations: `0 / 0 / 0`;
- secret/session reads: 0;
- `UNKNOWN_WRITE`: 0.

## Evidence

- `stage_a_current_production_day_acceptance_v1.json` — immutable raw Stage A receipt;
- `final_task_receipt_v1.json` — task-level classification and exact conditional Stage B result;
- `tests_and_validation_v1.json` — focused deterministic validation and safety receipt;
- runtime root:
  `A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\v1_completion_first_adaptive_stage_a_20260823T224056Z`.

Exact residual blocker: `CHATGPT_USAGE_LIMIT_REACHED`.
