# P0-2A source reachability correction and one V1 canary retry

Classification: `NO_PUBLICATION_VALID / P0_2_ACCEPTANCE_NOT_PROVEN`

The P0-2 forensic replay proved one mechanical source-reachability failure among twelve
candidate abstentions. The Qatar/missing-pilots candidate had an accessible Al Jazeera article,
but the old public-secondary path (a) under-scored its short exact title, (b) could not resolve the
opaque Google News RSS locator to publisher bytes, and (c) did not recognize the publisher's
`publishedDate` meta field. The bounded correction resolves a discovery item only through the
same reputable publisher's news sitemap, fetches the exact publisher article, and gives authority
only to those publisher bytes. Listings, snippets, sitemap metadata, and model output remain
discovery-only.

The corrected real probe accepted the exact Al Jazeera article at
`https://www.aljazeera.com/news/2026/8/18/qatar-rejects-irans-false-claims-about-missing-pilots`.
The request sequence was Google News RSS (200, 47,964 bytes) -> Al Jazeera news sitemap (200,
94,796 bytes) -> publisher article (200, 202,493 bytes). The raw article SHA-256 was
`bffca90648681a7c3a7ce1058cb88b65336b5ac458b7fd0dcf3c2784648c260f`; canonical extracted text
SHA-256 was `453d57d843f1db43430428c887236aa349915f41f232e54edef75619011de1f8`;
publisher time was `2026-08-18T12:39:43Z`; visible content was 768 words. No browser, login,
paywall, anti-bot bypass, snippet promotion, or arbitrary crawler was used.

The other eleven historical candidates remained legitimate abstentions: disallowed ZeroHedge
bindings, stale or irrelevant locators, no exact reputable result, an unresolved/paywalled WSJ
listing, or unsupported precise claims. No request budget was exhausted. The original P0-2 raw
artifacts preserved per-candidate request counts and accepted research-plan receipts but did not
persist every HTTP status or the exact model-generated strings for rank 6; the replay records that
limitation instead of inventing history. The complete compact matrix is in
`prior_12_candidate_failure_matrix_v1.json`.

Focused validation passed: 84 evidence/research/loader/adapter/viability tests, 9 P0 authority and
context tests, and 101 publication/readback tests. A broader continuous-intelligence run had one
pre-existing published-corpus fixture failure; the same failure reproduced on the untouched exact
P0-2 starting worktree, while all task-focused suites passed. Runtime import preflight passed under
the ContentOps-owned stable interpreter.

Canonical recovery found no resumable obligation, made zero publish calls and zero readback calls,
and left the production database byte-identical. The one authorized manual trigger was
`operator-trigger-c1443a4dfd9f44d1835c1c80`; its work item was
`operator-requested-operator-trigger-c1443a4dfd9f44d1835c1c80`. Fresh ingestion added 46 headline
identities and produced a twelve-candidate frontier. The opportunity evaluated all twelve,
performed 22 bounded public retrieval requests, accepted zero documents, and terminated
`REJECTED / NO_PUBLICATION / ALL_RANKED_CLUSTERS_EVIDENCE_BLOCKED`. It did not reach editorial or
destination-readiness stages: XHIGH workers 0, publication adapters 0, public writes 0,
`UNKNOWN_WRITE=0`, pending reconciliation 0, and pending triggers 0.

Every current candidate's Capital Chronicle resolution stayed
`CONTEXT_DISCOVERY_ONLY / PUBLICATION_PACKET_NOT_AVAILABLE`; no CC values were regenerated,
repaired, or promoted. The four existing V1 tasks remain `PAUSED`. Protected `v1.0` remains the
immutable commit `6983bfb3ef300414b744f3f8f97ca81ff699348b`. The exact remaining blocker is one genuine future
article plus all eight derivatives confirmed and reconciled for owner artifact audit; P0-2
acceptance is not proven by this truthful abstention.
