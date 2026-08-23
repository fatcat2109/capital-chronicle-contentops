# V1 quota-efficient batch/tail discovery and economical ready-pool evidence

Authority date: 2026-08-23
Final task classification: `CURRENT_HOST_RUNTIME_PROOF_REQUIRED`

## Implementation boundary

The canonical ranked evidence walk now performs deterministic acquisition first, caches exact
story-bound receipts, sends only exact `SOURCE_DISCOVERY_REQUIRED` identities to one bounded batch
turn, resumes deterministic retrieval/hash/freshness/claim admission, and permits a bounded tail
only for the still-unresolved subset. `OfficialCodexUrlDiscoveryProvider` remains the sole model
provider. The existing evidence adapter, official/public loaders, source-route health, canonical
hashing, freshness, claim, permission, numeric-authority, and publication gates remain authority.

Routine discovery still defaults off. The batch/tail path requires the existing explicit
`autonomous_source_discovery_enabled=True` opt-in. Budgets fail closed at two batch turns, two tail
turns, four total discovery turns, 2,000,000 accounted tokens, 12 stories per turn, and the unchanged
96 deterministic-network-request production-day ceiling.

Model output remains URL-only locator input. Batch identity/headline/prior-blocker coverage is
locally exact; cross-story binding, snippets, summaries, non-HTTPS/unregistered hosts, missing
coverage, unexpected actions, and authority escalation are rejected before deterministic resume.

## Deterministic implementation proof

Focused tests prove:

- four exact story identities share one batch model turn;
- deterministic-ready frontiers use zero discovery turns;
- unresolved-only tail membership and one-tail-per-identity bounding;
- cross-story/headline binding rejection before deterministic resume;
- snippets/summaries/model claims grant no evidence authority;
- same-candidate deterministic/resumed receipt reuse without rediscovery;
- token and turn ceilings fail closed without a per-candidate fallback loop;
- real loader/hash/freshness/claim gates remain downstream authority;
- four-ready aggregation stays distinct and stops before writer/article/derivative/publication.

The in-process end-to-end fixture reached four distinct governed evidence-ready candidates with one
batch turn, zero tail turns, 120 accounted discovery tokens, zero writer/article/derivative/public
writes, and `UNKNOWN_WRITE=0`.

## Fresh current-universe proof

One fresh canonical zero-write attempt loaded 335 current headline identities and prepared the
normal bounded 12-candidate frontier. Deterministic acquisition used 19 network requests, below the
unchanged ceiling. Nine exact unresolved identities reached the batch boundary.

The ChatGPT-authenticated App Server then rejected execution before a model turn because the account
had reached its Codex usage limit. A separate minimal provider diagnostic confirmed the same exact
host response and reported availability again at `Aug 30th, 2026 2:12 PM`. No API-key fallback,
alternative credential, secret/session read, extra proof retry, or invented URL/evidence was used.

Therefore the observed `0` discovery turns / `0` discovery tokens are not an economic acceptance
result. Four fresh ready candidates were not produced, and the required PASS classification is
forbidden until one fresh current-host proof completes under the implemented ceilings.

Exact receipts:

- `real_zero_write_acceptance_receipt_v1.json` — first current-universe cycle extraction;
- `host_runtime_blocker_receipt_v1.json` — exact sanitized host blocker and safety counts;
- `tests_and_validation_v1.json` — deterministic validation and repository checks.

## Safety result

Writer calls `0`; article generation `0`; derivative generation `0`; public/provider writes `0`;
`UNKNOWN_WRITE=0`; browser/CDP publication actions `0`; Automation mutations `0`; Capital Chronicle
mutations `0`; V2 mutations `0`; secret/session reads `0`.

No monetary savings are claimed because no exact price/cost receipt exists.
