# V1 fast-ship article path and single-article acceptance

Classification:
`PASS_TRUE_CANONICAL_SINGLE_ARTICLE_ZERO_WRITE_ACCEPTANCE / OWNER_AUDIT_REQUIRED`

## Repository identity

- fresh master/start: `9710b56589c544157095adcb4d4585e60e8ed460`;
- branch: `codex/v1-fast-ship-article-path-single-acceptance-v1`;
- execution lane: `CODEX_EXECUTION`;
- task: `TASK_CONTENTOPS_V1_FAST_SHIP_ARTICLE_PATH_AND_SINGLE_ARTICLE_ACCEPTANCE_V1`.

## Product correction

The canonical native worker-return path now applies the existing deterministic representation
normalizer before final qualification and consumes the normalized article. It mirrors visible-copy
aliases, structured data, identity, coordinator-bound timestamps, slug/mode aliases, governed
cluster/headline/evidence identity, ordinary evidence provenance, and source-resolved public copy.
Stale annotations absent from public copy are removed. Representation and metadata-only findings
remain observable warnings; unsupported causality, numbers, quotations, evidence/source binding,
event state, Capital Chronicle authority, permission, public identity, and `UNKNOWN_WRITE` remain
hard.

The first owner-review article is superseded because it inferred source omissions from a partial
paywall/navigation projection. The accepted bytes supported positive headline facts but contained
no explicit governed omission claim. The canonical validator now emits hard
`unproven_source_omission_claim` whenever public copy asserts that a source omitted information
without an exact supported claim/evidence binding. Partial sources remain eligible for positive
claims they actually prove.

Root-cause classification is
`ACCEPTED_EVIDENCE_WAS_PARTIAL_AND_SOURCE_COVERAGE_WAS_OVERCLAIMED`. The accepted document was a
`READ_ONLY_PUBLIC_HTTP_GET` response (`148377` bytes, `content_truncated=false`) whose canonical
projection was a subscription/navigation shell, SHA-256
`1b44ee410458d10bfffc6e99e8eb31c6de62d58ddece427f56057b0a78ab4c25`. Its claim-evidence contract
was absent. The governed research packet retained three positive headline facts but incorrectly
treated absent deeper content as source uncertainty. No paywall bypass or owner-audit fact was used
in the correction.

The current routing spine now states that 4/32 is a throughput/economics benchmark and daily-output
diagnostic, not a prerequisite for proving one safe qualified article. The final target remains 5–8
useful published articles per production day without filler.

## Qualified article

- title: `Blank Street raises General Atlantic funds for expansion and ice-cream push`;
- mode: `BREAKING_BRIEF`;
- story: `rolling-x-semantic-reserve-537e5b4936dd16eb619a`;
- article body/content identity:
  `be0812df7c983c1e8192d57aac7c6d814acd87207e6b040b0f9b31107d12707a`;
- article manifest file SHA-256:
  `31facbf0567aed45d74da9b7d4137edc41f96663bb1a60acf55c9ae49881ceda`;
- word count: `141`;
- source identity: `www.ft.com` / evidence
  `public-secondary-dc8ac2e4033d4a59c1fb` / canonical content
  `1b44ee410458d10bfffc6e99e8eb31c6de62d58ddece427f56057b0a78ab4c25`;
- hard blockers: none;
- soft warnings: none;
- deterministic representation repairs:
  `canonical_slug_alias_mismatch`, `institutional_edge_article_packet_binding_mismatch`,
  `editorial_mode_representation_mismatch`.

Exactly eight derivative intents were compiled, all `UNDISPATCHED`:

| Destination | Payload SHA-256 |
| --- | --- |
| Telegram | `f487e43718c26f0d8c71c501721a4418588d9bb3a9e32ebf5549a280fccec20b` |
| X | `7b219da7a7fdf97057c243ca548821edf182a3e9f0c1c2d4b9d72f341ce78390` |
| Discord | `5bab7497f233cf451c4acd6c61b4b9e3daa15c8ec81063d316fcb965c8345191` |
| LinkedIn | `0363af8172f5506e2db6ee48298ede280457e1833eb77ee59f5a270d06792844` |
| Facebook Page | `3fcaae0b29fa97deaa2de149c0e3bdc8b4587c77c7ffdc52dac61149f876686d` |
| Instagram Business | `ea7f4316030209c70a47ec1a0fc3c8bb71af46ac30d23fe321865041f5f335f8` |
| Threads | `555f850e1066d2643573bb0b9bac9a355023ef74441a3ccaf22660c60839dbae` |
| YouTube Community | `3b4c641a753d7ca28b2369dc6bc51fec4466df9ed4647816639960a68417eec3` |

## Worker and safety

- corrective run: one fresh isolated `gpt-5.6-sol / XHIGH` worker and zero revisions;
- public writes / publication-provider writes / `UNKNOWN_WRITE`: `0 / 0 / 0`;
- Automation mutations / fifth Automation / browser publication / Capital Chronicle mutation /
  production-store reset / V2 work: `0 / 0 / 0 / 0 / 0 / 0`.

The accepted PR #19 Stage-A packet was reused without importing owner-audit facts. The corrected
article uses only the three positive facts in the governed research packet.

## Evidence and validation

- runtime root:
  `A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\v1_fast_ship_source_omission_repair_20260824T170000Z`;
- canonical cycle:
  `frontier_1\canonical_zero_write_rehearsal\rolling_x_newsroom_cycle_evidence_v1.json`,
  SHA-256 `fa217e2e7e8bf7b0aac5ed14b0d97203c4212b4f5b1858fe0cb49d054b4d9cb3`;
- article manifest: `frontier_1\canonical_zero_write_rehearsal\article_manifest_v1.json`;
- qualified record:
  `frontier_1\canonical_zero_write_rehearsal\qualified_article_record_v1.json`,
  SHA-256 `0820b3a13f9d0b2f7568a1675380d59ca84fbd4c3b9242de5a0038ff9fcb8a2a`;
- focused source-omission/institutional/worker/newsroom tests: `42 passed`;
- compileall: PASS;
- `git diff --check`: PASS;
- CodeGraph generation/check: `CODEGRAPH_CURRENT`.

This PASS authorizes independent Jim/ChatGPT audit and PR review only. It does not authorize public
writes, Automation mutation/enablement, a 4/32 claim, or `V1_FINAL_PRODUCT_ACCEPTED`.
