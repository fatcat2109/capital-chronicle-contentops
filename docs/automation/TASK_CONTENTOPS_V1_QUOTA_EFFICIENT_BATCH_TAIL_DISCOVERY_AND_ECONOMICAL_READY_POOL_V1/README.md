# V1 batch/tail discovery ready-pool closure correction B

Authority date: 2026-08-23
Final task classification: `FAIL_V1_EVIDENCE_READY_POOL_NOT_ACCEPTED`

## Repository state

Fresh fetch verification found `origin/master` at
`c4239a96513c24fc9f7f331025386756d0248569` and the remote task branch at
`e494ea8fbc9d21bc0a6604b1a76c3696b5266907` before Correction B, with master as the exact merge
base and no unexpected drift.

Commit `d1bbc0721341fa17a1c7fdc17a47da88562b04f4` preserved and pushed the independently useful
request-budget repair. Explicit autonomous batch/tail mode now propagates the existing 96-request
coordinator ceiling to the default official/public loaders; the per-candidate limit remains 6 and
all evidence, hash, freshness, capability, claim, permission, and publication gates are unchanged.

## Sourceability parity finding

Before Correction B, the acceptance runner did not exercise the same sourceability inputs as the
Daily App path:

- Daily App loads the persisted routing-only `source_route_health_v1.json` snapshot and supplies it
  to prepared frontier construction.
- Daily App passes the same non-empty snapshot into the canonical cycle, where it becomes
  preselection `sourceability_observations` and can rerank materially comparable candidates.
- The runner built its frontier without `autonomous_source_discovery_available=True`, supplied no
  persisted route-health snapshot to the builder, and supplied no snapshot to the canonical cycle.

The focused correction reuses those existing seams. The runner now loads the same routing-only
snapshot path when present, feeds it to both frontier construction and the canonical cycle, and
marks autonomous discovery available during frontier construction. It adds no ranking system and
grants no factual, numeric, permission, or publication authority.

At the final proof epoch the canonical persisted route-health file was absent. The receipt therefore
truthfully records an empty current snapshot, `prepared_frontier_autonomous_source_discovery_available=true`,
and `preselection_sourceability_observations_consumed=false`. No observations were fabricated.

See `sourceability_route_health_parity_audit_v1.json` for the capability classifications.

## Final proof

One fresh post-correction zero-write proof ran at cutoff `2026-08-23T14:32:51.390611Z`, loaded 282
current headline identities, and prepared a 12-candidate frontier using the production discovery-
aware ordering.

One distinct candidate passed the governed evidence-ready pool:

- cluster `rolling-x-global-cluster-82db0cbb80577ed8baae`;
- headline `cc-x-headline-5b1a65456b1dc62be206f3d1`.

The required four-candidate pool was not reached. Remaining candidates terminated on unresolved
URL discovery, 401/access failures, unavailable public sources, or missing governed evidence. The
exact residual blocker is `ALL_RANKED_CLUSTERS_EVIDENCE_BLOCKED`. No further proof was run.

Economics remained within every hard ceiling: 1 batch turn, 1 tail turn, 2 total turns, 1,237,551
accounted discovery tokens, and 16 deterministic requests. Compared with 35 turns / 10,237,897
tokens, the exact deltas are -33 turns / -9,000,346 tokens. The natural 1M target was not achieved,
but the hard 2M token ceiling passed. No monetary savings are claimed.

Writer calls `0`; article generation `0`; derivative generation `0`; public/provider writes `0`;
`UNKNOWN_WRITE=0`; browser/CDP actions `0`; Automation mutations `0`; Capital Chronicle mutations
`0`; V2 mutations `0`; secret/session reads `0`.

## Validation

206 focused tests passed across batch/tail, evidence adapters/loaders, Daily App route-health
persistence, preselection sourceability reranking, prepared frontier construction, and the canonical
newsroom cycle. Compileall, CodeGraph generation/check, receipt hash validation, staged-diff review,
and `git diff --check` passed.

Do not start the 4/32 proof from this result.
