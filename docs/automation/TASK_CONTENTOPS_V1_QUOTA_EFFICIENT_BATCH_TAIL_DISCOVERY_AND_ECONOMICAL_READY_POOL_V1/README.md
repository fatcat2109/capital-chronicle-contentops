# V1 quota-efficient batch/tail discovery current-host acceptance revalidation

Authority date: 2026-08-23
Final task classification: `FAIL_V1_EVIDENCE_READY_POOL_NOT_ACCEPTED`

## Repository and host state

Fresh fetch verification found `origin/master` at
`c4239a96513c24fc9f7f331025386756d0248569` and the task branch at
`e494ea8fbc9d21bc0a6604b1a76c3696b5266907`, with master as the exact merge base and no unexpected
drift.

The fresh supported App Server preflight passed with ChatGPT authentication, SDK `0.147.0`,
`gpt-5.6-sol / HIGH`, an ephemeral thread, read-only sandbox, deny-all approval mode, and no API-key
environment. The prior `CHATGPT_USAGE_LIMIT_REACHED` receipt is no longer current and has been
removed.

ContentOps assignment used only the two owner-confirmed local 9Router routes:
`vx/gemini-3.5-flash(high)` and `vx/gemini-3.1-pro-preview(high)`.

## Demonstrated defect and bounded repair

The first server-available proof exposed one concrete coordinator/loader mismatch. The quota
session enforced the unchanged deterministic ceiling of 96 requests, but the default official and
public loaders remained capped at 24 and the public loader terminated deterministic resume when
total accounting was only 35. The bounded repair propagates the existing coordinator ceiling to
the default loaders only when explicit autonomous batch/tail discovery is enabled. The quota
session remains the hard 96-request authority, and the per-candidate limit remains 6. Evidence,
hash, freshness, capability, claim, permission, and publication gates are unchanged.

Focused validation passed 88 tests. Compileall, CodeGraph generation/check, and `git diff --check`
passed.

## Final post-repair proof

The fresh post-repair zero-write proof ran at cutoff `2026-08-23T14:01:59.304858Z`, loaded 288
current headline identities, and prepared the bounded 12-candidate frontier.

One distinct candidate passed deterministic retrieval, content hashing, freshness, capability, and
claim gates:

- `rolling-x-global-cluster-94935b83bf36a4332d4d`, headline identities
  `cc-x-headline-60b2102d06ca1c9cb74fb4a1` and
  `cc-x-headline-567cf76077899037f72d4e6f`.

The required four-candidate pool was not reached. Remaining candidates truthfully terminated on
unresolved discovery, 403/404/access failures, stale or unresolved latest-event state, missing
follow-up identity/material delta, or missing governed evidence. The exact remaining blocker is
`ALL_RANKED_CLUSTERS_EVIDENCE_BLOCKED`. No further retry, speculative prompt tuning, gate weakening,
or ceiling increase was performed.

Economics passed: 1 batch turn, 1 tail turn, 2 total discovery turns, 310,521 accounted discovery
tokens, and 22 deterministic requests. Compared with 35 turns / 10,237,897 tokens, the exact deltas
are -33 turns / -9,927,376 tokens. No monetary savings are claimed.

Writer calls `0`; article generation `0`; derivative generation `0`; public/provider writes `0`;
`UNKNOWN_WRITE=0`; browser/CDP actions `0`; Automation mutations `0`; Capital Chronicle mutations
`0`; V2 mutations `0`; secret/session reads `0`.

`real_zero_write_acceptance_receipt_v1.json` is the coherent final receipt. No host blocker receipt
is retained. Do not start the 4/32 proof from this result.
