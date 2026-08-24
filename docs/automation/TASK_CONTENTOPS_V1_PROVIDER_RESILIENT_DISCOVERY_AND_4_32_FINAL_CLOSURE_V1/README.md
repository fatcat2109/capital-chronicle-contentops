# V1 provider-resilient discovery and 4/32 final closure

Authority date: 2026-08-24

Final classification:
`PASS_STAGE_A_PROVIDER_RESILIENCE / STAGE_B_INCOMPLETE_NON_QUALIFIED`

## Repository identity

- repository: `fatcat2109/capital-chronicle-contentops`;
- fresh master: `c4239a96513c24fc9f7f331025386756d0248569`;
- starting branch head: `869c9485c78c4dc360c49f26645542be219625fd`;
- branch: `codex/v1-quota-efficient-batch-tail-discovery-v1`;
- PR: `#19`.

## Architecture delta

The canonical evidence path now degrades across one provider-resilient cascade:

1. deterministic exact/public/official locator and retrieval;
2. query-text-only 9Router replan through
   `vx/gemini-3.1-pro-preview(high)` -> `vx/gemini-3.5-flash(high)`;
3. deterministic Google News RSS, same-publisher robots/news/generic sitemap discovery,
   bounded same-host sitemap-index selection, exact-title relevance, and direct publisher-byte
   retrieval;
4. optional `OfficialCodexUrlDiscoveryProvider` last resort.

Model query text cannot contain or generate URLs and grants no evidence, factual, numeric,
permission, or publication authority. Exact source bytes still pass the unchanged deterministic
retrieval, hash, freshness, publisher, claim, CC/numeric-authority, and permission gates.

The optional Codex provider is now disabled for the remainder of a production-day proof after an
availability failure such as `CHATGPT_USAGE_LIMIT_REACHED`; useful unseen provider-independent work
continues. The unified development guardrail is 96 locator/planning invocations, 26,000,000
accounted tokens, 1,024 deterministic requests, and 16 requests per candidate. These are proof
runaway ceilings, not production budgets.

Stage B can reuse Stage A evidence only when the frozen-universe hash, prepared frontier, accepted
semantic checkpoints, cluster, headline set, canonical `story_evidence_scope_id`, and effective
mode match. A nondeterministic diagnostic request hash may be rebound inside that exact scope;
source/content/contract hashes remain unchanged and reuse grants no authority.

## Stage A — PASS

- cutoff: `2026-08-23T23:46:33.626619Z`;
- production day: `newsroom-production-day-2026-08-24-bangkok`;
- frozen universe: 121 headline identities;
- progression: five frontiers, 44 distinct stories / 58 distinct headlines;
- remaining held identities: 63;
- ready candidates: 4;
- total locator/model invocations: 44;
- provider-independent 9Router replans: 41, all accepted on Pro;
- optional Codex BATCH turns: 3;
- Codex usage-limit failures: 0;
- BATCH / TAIL: `3 / 0`;
- accounted semantic/discovery tokens at candidate #4: 712,842;
- deterministic read-only requests at candidate #4: 386;
- public/provider writes and `UNKNOWN_WRITE`: 0.

Ready candidates:

1. `rolling-x-semantic-reserve-537e5b4936dd16eb619a` —
   `ORDINARY_MINIMUM_TRUSTWORTHY_EVIDENCE_PACKET`,
   `024d1f4840eb4def580a3a5acf5c99f9c8718e329054602d5963c5ca4e6e220e`;
2. `rolling-x-global-cluster-17153eaa0270b7d634e4` —
   `ORDINARY_MINIMUM_TRUSTWORTHY_EVIDENCE_PACKET`,
   `c2c554e35dec07a7127c9bcefb4329176e1c99ee9a9c6f35c172ab5745d930f9`;
3. `rolling-x-semantic-reserve-17c72ad7cdfb9bf74630` —
   `ENHANCED_CLAIM_EVIDENCE_CONTRACT`,
   `fe4980d80b18c3899cd162b0eb76a38950164ac64f07be634c27e3593913fc32`;
4. `rolling-x-global-cluster-823dd0e338b183cb3b74` —
   `ORDINARY_MINIMUM_TRUSTWORTHY_EVIDENCE_PACKET`,
   `11c6a0fde1f17e778af45cac61646482cb54a7d6aef43c7e80045a25d715abe3`.

## Stage B — incomplete / non-qualified

The accepted four-frontier zero-write harness immediately consumed the Stage A frozen universe.
Two reversible reuse defects were repaired in-task: fresh assignment identity drift and a
nondeterministic `query_elapsed_ms` contribution to the diagnostic request hash. The final proof
reused the exact Stage A prepared frontier, accepted semantic checkpoints, and four cached
story-scope receipts before reaching the XHIGH article boundary.

One fresh isolated `gpt-5.6-sol / XHIGH` worker authored the first candidate and used its one
bounded same-worker revision. The current-schema revision passed the worker envelope but failed the
unchanged deterministic public-copy consistency validators:

- `social_hook_social_lede_mismatch`;
- `epistemic_claim_not_present_in_public_copy`;
- `structured_data_description_mismatch`.

Per the task's stop rule, no second candidate worker, second revision, filler article, or gate
weakening occurred.

- qualified zero-public-write articles: 0 / 4;
- derivative intents: 0 / 32;
- attempted article candidate:
  `rolling-x-semantic-reserve-537e5b4936dd16eb619a`;
- qualified article identities: none;
- XHIGH worker attempts / returns / revisions: `1 / 1 / 1`;
- public/provider writes: `0 / 0`;
- `UNKNOWN_WRITE`: 0.

The task session itself was explicitly requested as `gpt-5.6-sol / XHIGH`; no separate exposed
HIGH coordinator receipt is claimed.

## Validation

- provider-resilient evidence/newsroom/router suite: 288 passed;
- existing 4/32/operator/article-worker suite after final reuse repair: 129 passed;
- focused provider cascade subset: 74 passed;
- compileall: PASS;
- CodeGraph generation/check: `CODEGRAPH_CURRENT`;
- `git diff --check`: PASS.

## Safety

- writer workers created: 1 exact isolated XHIGH worker;
- bounded same-worker revisions: 1;
- qualified articles / derivative intents: `0 / 0`;
- public writes / provider writes / `UNKNOWN_WRITE`: `0 / 0 / 0`;
- browser/CDP publication actions: 0;
- Automation / Capital Chronicle / V2 mutations: `0 / 0 / 0`;
- secret/session reads: 0;
- production-store reset / fifth Automation: `0 / 0`.

## Evidence

- `stage_a_provider_resilient_acceptance_v1.json` — Stage A raw PASS receipt;
- `final_task_receipt_v1.json` — final Stage A/Stage B classification;
- `tests_and_validation_v1.json` — deterministic validation receipt;
- Stage A runtime root:
  `A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\v1_provider_resilient_stage_a_20260823T234625Z`;
- final Stage B runtime root:
  `A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\v1_provider_resilient_4_32_scope_reuse_revision_20260824T012000Z`.

Exact residual blockers are the three deterministic Stage B copy-consistency failures above.
