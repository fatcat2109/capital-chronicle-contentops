# V6 25-Task / Roadmap Ledger

This ledger maps the V6 roadmap to current repo evidence. It is a roadmap/progress aid, not runtime authority over GitHub. Status values are conservative: fixture/manual evidence is not live/provider/API evidence.

## Status Vocabulary

- `complete`: implemented and accepted for its stated local/product scope.
- `complete_fixture_only`: complete using fixture/manual/operator-supplied evidence only.
- `complete_pre_live_no_send`: complete up to pre-live/dry-run/governance boundary with no live send.
- `partially_complete`: meaningful repo evidence exists, but lane is not complete.
- `pending`: no accepted implementation evidence found for the lane in this refresh.
- `deferred`: intentionally later/not active.
- `blocked_until_explicit_live_scope`: cannot proceed without exact live/provider/platform authorization.

## Ledger

| # | Task / Lane | Status | Current repo evidence and caveats |
|---:|---|---|---|
| 01 | V6 master plan authority | complete | Expanded in `current_v6_master_plan.md`; GitHub remote remains runtime authority. |
| 02 | Unified redacted credential capability matrix | complete | Redacted capability/readiness artifacts exist; no raw secret values are authority. |
| 03 | Platform universe and adapter taxonomy | partially_complete | Multiple registry/adapter docs exist; live platform behavior remains gated. |
| 04 | Canonical Substack article workflow | complete_fixture_only | Canonical article and Substack manual export/evidence packets exist locally. |
| 05 | AI research grounding lane | complete | Research/canonical article packet builders exist for local deterministic workflow. |
| 06 | SEO and editorial refinement lane | partially_complete | SEO/editorial packet docs exist; continue verifying per future task scope. |
| 07 | Platform-native variant generator | partially_complete | Variant preview/hash/outbox docs and tests exist; not all platforms are live. |
| 08 | Discord webhook/community drop lane | complete_pre_live_no_send | Discord dry-run/outbox/pre-live artifacts exist; no live send is claimed here. |
| 09 | Telegram remote operator lane | deferred | Operator lane direction exists; live execution requires future explicit scope. |
| 10 | Approval/outbox/audit integration | partially_complete | Payload hash, approval, outbox, and audit artifacts exist across lanes. |
| 11 | Public URL capture and reconciliation | complete_fixture_only | Substack and LinkedIn URL/audit imports are operator-supplied/manual only. |
| 12 | Community feedback intake | complete_fixture_only | Operator-supplied feedback intake packet exists locally; no live community activity, scrape, fetch, API, browser, or provider call is claimed. |
| 13 | LLM feedback summarizer | deferred | Current backlog summary uses deterministic tag grouping only; no LLM/provider call is claimed. |
| 14 | Backlog/next-idea generator | complete_fixture_only | Deterministic backlog candidates are generated from operator-supplied fixture feedback; recommendations remain review-only. |
| 15 | Media asset export lane | pending | No accepted live/media lane completion claimed by this refresh. |
| 16 | V6 UI command surface | partially_complete | Canonical dashboard is `ui/contentops_v5/`; read-only evidence cards are integrated. |
| 17 | Operator review dashboard | partially_complete | V5 Approval Queue/Evidence Vault show fixture/manual evidence; no live controls authorized. |
| 18 | Credential setup workbench alignment | blocked_until_explicit_live_scope | Credential/env value reads are forbidden unless a future exact scope allows safe handling. |
| 19 | Platform registry alignment | partially_complete | Registry docs exist; future tasks should verify current code before edits. |
| 20 | Adapter safety policies | partially_complete | Safety docs and tests exist; platform/live adapters remain gated. |
| 21 | Browser/CDP supervised adapter boundary | blocked_until_explicit_live_scope | Browser/CDP must be supervised and cannot read session/secret stores. |
| 22 | Manual fallback playbooks | complete_fixture_only | Substack and LinkedIn runbooks exist for manual evidence loops. |
| 23 | Evidence packet standardization | partially_complete | Hash/evidence packet conventions exist across Substack/LinkedIn/Discord lanes. |
| 24 | End-to-end dry-run acceptance | partially_complete | Local/manual/pre-live pieces exist; no end-to-end live path is accepted. |
| 25 | Final product readiness review | pending | Requires roadmap reconciliation and explicit acceptance criteria. |

## Accepted Lane Highlights

- Status docs/protocol exist in `docs/status/`.
- Canonical dashboard is `ui/contentops_v5/`.
- Substack manual publication evidence is complete as fixture/manual local evidence.
- LinkedIn manual publication evidence is complete as fixture/manual local evidence and accepted at `83c53fd3a39b377d9f74fa70cd8b6a5357689ecb` after this status repair.
- Discord pre-live docs may exist, but this ledger does not claim live send.
- Live/provider/platform execution remains blocked unless separately scoped.

## Soft Recommendation

Recommended next lane at the time of this refresh: roadmap review or another manual/deferred distribution lane that does not require provider/API/browser/live action. This is not authoritative truth; future tasks must re-read GitHub remote and status docs.

## How to Update This Ledger

1. Update this file only on roadmap/lane completion or execution-plan refresh.
2. Use conservative statuses and distinguish local/fixture/manual evidence from live/API/provider evidence.
3. Never hardcode a future next task as permanent truth.
4. Keep recommendations soft and timestamp/context dependent.
5. If a lane claims live/public/API verification, cite committed evidence and tests; otherwise mark it manual/fixture/pre-live.
