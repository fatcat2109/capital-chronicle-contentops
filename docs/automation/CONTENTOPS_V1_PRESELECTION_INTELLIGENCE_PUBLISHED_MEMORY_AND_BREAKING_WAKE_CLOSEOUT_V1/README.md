# V1 Preselection Intelligence / Published Memory / Breaking Wake Closeout

Task:

`TASK_CONTENTOPS_V1_PRESELECTION_INTELLIGENCE_PUBLISHED_MEMORY_AND_BREAKING_WAKE_CLOSEOUT_V1`

Result:

`COMPLETE_IMPLEMENTED_AND_VALIDATED_WITH_FDA_G_RESTART_BOUNDARY_CAVEAT`

This correction closes the independently audited gaps in the prior continuous-intelligence
foundation. It does not rewrite that historical task or its evidence.

Delivered behavior:

- published memory now recognizes only a canonical Substack article whose production dispatch
  is `DISPATCH_CONFIRMED` and whose exact coordinator reconciliation is
  `RECONCILED_CONFIRMED`; nine surface objects deduplicate to one article;
- actual canonical article text is recovered locally and hashed from its exact UTF-8 text;
  missing historical text is explicit `CONTENT_UNAVAILABLE`;
- the existing rolling-X `cluster_id` is propagated as the canonical story/update-chain
  identity where no separate prior identity exists; no parallel story ID was invented;
- published-memory novelty, actual story-scoped Capital Chronicle matches, portfolio
  concentration, selected/held state, and article/update mode run over the compact shortlist
  before targeted evidence and writing;
- low-delta repeats stop before the expensive path, while a material follow-up retains its
  previous article identity/title/body hash/time/full local text/current chain/new headline and
  source candidates/reason summary;
- all Capital Chronicle DuckDB stores and table schemas are discovered read-only with a compact
  fingerprint/cache; only deterministic schema-relevant tables are queried deeply;
- source-event-time-valid new intake rows create a stable zero-LLM material-event identity and
  a durable canonical work item, so KILL_SWITCH/restart cannot lose the wake and the same event
  cannot execute twice;
- active intake remains 240 seconds and idle backoff is capped at 300 seconds;
- SHADOW_ONLY now proceeds through release/package preparation while publication authority is
  disabled, enabling a real article/review/package proof with zero writes;
- the real current read-only canary reports a four-item zero-model bounded candidate projection
  with actual novelty, CC richness/matches, portfolio penalties, and selected/held state while
  explicitly leaving governed hierarchical assignment and publication authority untouched;
- V5 Today exposes the corrected decision, mode, prior article, material delta, decision reason,
  stopped stage, CC match count, wake state, rolling headline count, canonical article counts,
  and next window without inventing unavailable values.

Validation and current-state evidence are recorded in
`closeout_evidence_v1.json`. Controlled SHADOW artifacts remain outside Git under
`A:\Capital Chronicle\Runtime\ContentOps\preselection_closeout_shadow_v1`.

The one controlled production restart preserved the exact schema-9 store and immutable
production epoch. A scheduled 01:00 UTC window began on the old supervisor at the restart
boundary after the safe-idle preflight; it reached only portfolio context and rolling intake
before shutdown. No assignment/evidence/article/package/dispatch or unknown write occurred.
After its original lease expired, the new supervisor canonically transitioned it through
`STALE_WINDOW_CLAIM_RECOVERED` to `STALE_WINDOW_CLAIM_RECOVERED_NO_PUBLICATION` / `REJECTED`
without rerun, manual state mutation, or a second restart. This is a new FDA-G source-code epoch
and an honest soak caveat; FDA-G is not declared accepted.
