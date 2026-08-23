# V1 production-day shared discovery budget and multi-frontier closure — Correction C

Authority date: 2026-08-24
Final task classification: `CURRENT_HOST_RUNTIME_PROOF_REQUIRED`

## Preserved accepted lineage

- `real_zero_write_acceptance_receipt_v1.json` remains the prior valid single-frontier Correction B
  receipt and was not overwritten.
- `sourceability_route_health_parity_audit_v1.json` remains valid.
- Commit `d1bbc0721341fa17a1c7fdc17a47da88562b04f4` remains the accepted explicit-mode loader
  ceiling repair.
- Commit `dea6d21465b4ac3bffb1f3c983a36d07dcba5e64` remains the accepted sourceability parity repair.

## Correction C implementation

The quota-efficient discovery receipt is now cumulative and bound to the exact
`newsroom_production_day_id`. A later cycle restores prior turns, accounted tokens, deterministic
requests, failures, and covered story identities, then receives only the residual allowance from
the unchanged hard production-day envelope:

- deterministic network requests: 96 total;
- batch turns: 2 total;
- tail turns: 2 total;
- discovery turns: 4 total;
- accounted discovery tokens: 2,000,000 total.

Default official and public loaders share one aggregate residual request counter. The Daily App
loads the latest cumulative receipt from existing cycle artifacts for the same production day and
carries it through bounded catch-up attempts. No new store or scheduler was added.

The proof runner freezes one current rolling universe and cutoff, carries cumulative evaluated
headline identities and routing-only source health, walks at most four frontiers, rejects repeated
headline/story work, and stops immediately at four governed ready candidates. It does not carry a
prior single-opportunity prepared state; that would incorrectly promote historical
`NOT_PROMOTED_BEFORE_EXPIRY` dispositions into multi-frontier terminal authority.

## Mode/risk proportional acceptance

Ready acceptance now consumes the canonical contract kind rather than imposing one claim-count
rule on every candidate:

- `ORDINARY_MINIMUM_TRUSTWORTHY_EVIDENCE_PACKET` requires its exact packet PASS/hash, a directly
  bound non-empty core proposition, accepted source/document identity, HTTPS URL, canonical content
  hash, current freshness, `public_claim_allowed=true`, and zero blockers.
- `ENHANCED_CLAIM_EVIDENCE_CONTRACT` still requires its exact contract PASS/hash, at least one
  supported claim with bound accepted document identities, zero fabricated claims, and zero
  blockers.

Every candidate receipt exposes `ready_contract_kind`, `ready_contract_status`, and
`ready_contract_sha256`. No mode alone grants acceptance or authority.

## One fresh production-day proof

The single authorized current-universe run used production day
`newsroom-production-day-2026-08-24-bangkok`, a frozen universe of 157 headline identities, and
completed one 12-identity frontier before exposing a harness integration defect. It produced zero
ready candidates and retained 145 held identities.

Observed cumulative budget:

- batch/tail/total turns: 1 / 1 / 2;
- accounted discovery tokens: 362,493;
- deterministic requests: 14;
- unused batch/tail/total turns: 1 / 1 / 2;
- unused tokens: 1,637,507;
- unused deterministic requests: 82.

The raw run receipt is preserved as
`production_day_shared_discovery_acceptance_receipt_v1.json`. Its exact runtime classification is
`FAIL_V1_EVIDENCE_READY_POOL_NOT_ACCEPTED`; all attempted frontier candidates were evidence-blocked.

The run then stopped because the first implementation passed `prior_prepared_state` into frontier
2. The canonical builder correctly interpreted the frozen single-opportunity held dispositions as
terminal and returned no candidates despite 145 held identities. Correction C now follows the
accepted multi-frontier harness: carry evaluated identities, quota accounting, and route health,
but rebuild each later frontier from the same frozen universe without importing prior
single-opportunity terminal dispositions.

The task explicitly forbids a second real proof. Therefore the corrected multi-frontier continuation
is deterministically validated but requires a later exact current-host revalidation. Exact residual
blocker:

`CORRECTED_MULTI_FRONTIER_CONTINUATION_CURRENT_HOST_REVALIDATION_REQUIRED`

## Safety and validation

The real run recorded writer/article/derivative/public/provider writes and `UNKNOWN_WRITE` all at
zero. No browser/CDP action, Automation mutation, Capital Chronicle mutation, V2 work, or secret/
session read occurred.

220 focused tests passed across quota carry-forward, aggregate loader budgeting, production-day
artifact reuse, Daily App catch-up carry, multi-frontier identity isolation, source-health routing,
ordinary/enhanced evidence contracts, canonical cycle, and existing batch/tail URL-only authority.
Compileall, CodeGraph generation/check, receipt hash validation, and `git diff --check` passed.

Do not start the 4/32 proof from this result.
