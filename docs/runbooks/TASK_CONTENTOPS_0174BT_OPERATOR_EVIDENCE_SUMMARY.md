# TASK_CONTENTOPS_0174BT — Operator Evidence Summary (Compiler v2 Chain)

## Purpose

The accepted compiler v2 evidence chain is correct but fragmented across multiple
objects. To verify a single draft, an operator currently has to read eight separate
objects:

```
compiler v2 output
  -> compile report v2
  -> payload hash manifest
  -> approval/dispatch bridge report        (0174BP, authoritative rollup)
       -> publish-readiness alignment       (0174BR)
       -> redacted-audit alignment          (0174BR)
```

`scd_operator_evidence_summary` rolls that chain into **one compact, operator-facing
summary object**. The summary explains the chain state **without making the chain
executable**. It is the local evidence object that a future UI can safely render. It
is **not** UI implementation.

> [!IMPORTANT]
> This layer is **evidence-only**. It never grants readiness, approval, dispatch,
> public-ready/live-ready status, platform/provider API access, credential/env reads,
> scheduler/posting/scraping/replies/DMs, and it never creates an audit event or edits
> any audit allow-list. PASS means only that the summary object is internally
> consistent and evidence-only.

## Module

`live_contentops/scd_operator_evidence_summary.py`

### Public API

- `build_operator_evidence_summary(bridge_report, readiness_alignment, audit_alignment)`
  — validates each bound component with its authoritative validator, rolls up the three
  states (fail-closed precedence), derives the canonical `bridge_report_hash` over the
  supplied bridge report, records lineage/hash consistency as boolean flags, and returns
  a compact summary packet. Never mutates inputs. Grants nothing even on PASS.
- `validate_operator_evidence_summary(packet)` — fail-closed validation of a summary
  packet, returns `{"validation_state": ..., "reasons": [...]}`.
- `derive_operator_evidence_summary_id(bridge_report_id)` — deterministic id helper.
- `OPERATOR_EVIDENCE_SUMMARY_VALIDATORS` — kind→validator registry for data-driven
  hostile-matrix tests.

### Binding

Lineage is bound by ids taken from the **authoritative bridge report**
(`bridge_report_id` / `compiler_output_id` / `compile_report_id` /
`payload_hash_manifest_id`) plus the canonical `bridge_report_hash` derived with the
shared `canonical_json_sha256` helper over the bridge-report object. Per-platform
payload hashes are **not** re-derived here — 0174BP owns the payload hash manifest. The
two 0174BR alignment objects are bound by `readiness_alignment_id` /
`audit_alignment_id` and cross-checked for lineage/hash consistency at build time.

## State semantics

Four-state model with fail-closed precedence:

```
BLOCKED > UNKNOWN > REVIEW_REQUIRED > PASS
```

| State | Meaning |
| --- | --- |
| `PASS` | Summary is internally consistent and evidence-only; all three bound components are PASS. **Never** means publish/dispatch/operator-approved/live/public-ready. |
| `REVIEW_REQUIRED` | No blockers/unknowns, but a bound component is REVIEW_REQUIRED. |
| `UNKNOWN` | Required lineage / alignment id missing, a component state is invalid, the bridge hash cannot be established, or a bound component is UNKNOWN. |
| `BLOCKED` | Any contradiction (see below). |

### BLOCKED conditions

- Any required-false flag is true (`public_ready`, `live_ready`, `dispatch_ready`,
  `executable_dispatch`, `platform_api_allowed_now`, `credential_read_allowed_now`,
  `credentials_requested_now`, `scheduler_enabled_now`, `posting_enabled_now`,
  `autonomous_replies_enabled_now`, `dms_enabled_now`, `scraping_enabled_now`,
  `audit_event_created`, `audit_allowlist_modified`, `readiness_granted`).
- Any required-true evidence flag is not true (`evidence_only`, `non_executable`,
  `manual_review_required`, `local_only`, `operator_visible`, `ui_ready_packet`,
  `bridge_report_bound`, `bridge_hash_matches`, `lineage_ids_consistent`).
- Wrong `operator_summary_mode` / `allowed_operator_action` literal.
- Recorded bridge-hash mismatch or lineage-id mismatch across bound objects.
- Inconsistent `blocker_count` / `review_required_count` / `unknown_count`, or a
  `rollup_state` inconsistent with the component states.
- A bound component validates BLOCKED.
- Declared `validation_state` PASS contradicting a computed non-PASS state.
- Forbidden runtime vocabulary or secret-like values anywhere in the packet.

### Missing vs mismatch (documented fail-closed choice)

- **Missing** required lineage / alignment ids → **UNKNOWN** (cannot establish lineage).
- Present-but-**mismatched** lineage ids or bridge hash → **BLOCKED** (contradiction).

## Schema

`schemas/scd_compiler_v2_operator_evidence_summary.schema.json`

## Fixtures

`fixtures/scd_operator_evidence_summary/`

- `operator_evidence_summary_valid_pass_manual_only.json` — built from the accepted
  0174BP PASS bridge report + 0174BR PASS alignments.
- `operator_evidence_summary_valid_review_required.json` — built from the accepted
  0174BP REVIEW_REQUIRED bridge report + 0174BR REVIEW_REQUIRED alignments.
- `hostile_degraded_cases.json` — 35 adversarial/degraded cases, each asserting a
  non-PASS fail-closed outcome.

Fixtures are generated deterministically from the accepted 0174BP/0174BR fixtures.

## Tests

`tests/test_scd_operator_evidence_summary.py`

## Validation performed

| Gate | Result |
| --- | --- |
| `py_compile` module + test | clean |
| `pytest tests/test_scd_operator_evidence_summary.py` | 7 passed |
| `pytest` 0174BP + 0174BR regression | 55 passed |
| `pytest tests/test_security_scans.py` | 1 passed |
| `pytest tests/` (full suite) | 3079 passed, 28 skipped |
| `git diff --check` | clean |

## Hard boundaries

No live posting, platform/provider API, credential/env reads, scheduler, dispatch,
audit event creation, audit allow-list modification, autonomous replies/DMs, scraping,
readiness/public-ready claims, financial advice, signal framing, or fake current market
truth. This layer is parallel/additive and edits no accepted 0174BN/0174BP/0174BR
module.
