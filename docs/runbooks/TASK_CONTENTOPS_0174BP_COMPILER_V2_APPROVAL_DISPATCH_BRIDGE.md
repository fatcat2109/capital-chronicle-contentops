# TASK_CONTENTOPS_0174BP — Compiler v2 Approval/Dispatch Bridge (registry-aligned, parallel)

LOCAL ONLY | DRY-RUN / EVIDENCE-ONLY | FAIL-CLOSED | CANDIDATE-ONLY
NO LIVE / API / CREDENTIAL / NETWORK / SCHEDULER / DISPATCH / POSTING / SCRAPING

Baseline master: `6fa1f1f0a428bf225d64551d29d2bd8c3b3d01f2`
Subject: `fix: repair platform payload compiler v2 contract drift`
Branch: `task/0174bp-compiler-v2-dispatch-bridge-alignment`

## Purpose

`scd_compiler_v2_dispatch_bridge.py` is a **new, parallel** local-only reconciliation
module that bridges the accepted platform payload compiler v2 output/report against
two downstream candidates: the approval-ledger candidate and the dispatch-gate /
freeze candidate. It re-derives payload hashes locally over compiler v2 payload
objects using deterministic canonical JSON and **blocks on any mismatch**.

The bridge never edits or replaces the compiler, registry v2, dispatch gate, domain
model, publish readiness, or redacted audit modules. It is purely additive evidence.

## Authoritative four-object contract

The repaired contract exposes four explicit objects, each validated to
`{validation_state, reasons}` with state in `{PASS, BLOCKED, REVIEW_REQUIRED, UNKNOWN}`:

| Object | Builder | Role |
| --- | --- | --- |
| Payload hash manifest | `build_compiler_v2_payload_hash_manifest` | Re-derives canonical-JSON SHA-256 over each compiler v2 payload object |
| Approval bridge packet | `build_compiler_v2_approval_bridge_packet` | Reconciles manifest against approval-ledger candidate — **candidate-only** |
| Dispatch bridge packet | `build_compiler_v2_dispatch_bridge_packet` | Reconciles against dispatch-gate / freeze candidate — **non-executable** |
| Approval-dispatch bridge report | `build_compiler_v2_approval_dispatch_bridge_report` | Authoritative roll-up over the three sub-objects |

The legacy combined `SCDCompilerV2DispatchBridgeResult`
(`build_compiler_v2_dispatch_bridge_result`) is retained for backward compatibility
only. It is **not** the authoritative object; the bridge report is.

## Candidate-only semantics

The valid new path must never imply approval has happened or that dispatch is
executable. In the valid path:

- `approval_state` is `approval_candidate_only` or `manual_review_required`.
- `auto_approved = false`, `operator_approved = false`, `approval_bypass = false`.
- `operator_review_required`, `manual_review_required`, `redacted_audit_required`,
  `kill_switch_check_required`, `revocation_required` are all `true`.
- `dispatch_state` is freeze-candidate-only; `operator_approval_present = false`,
  `executable_dispatch = false`, `freeze_candidate_only = true`.
- `precondition_summary.platform_compile_pass = false` and
  `precondition_summary.executable_dispatch_allowed = false`.

`operator_approved: true` and `decision_state: approved_mock_only` may appear only in
hostile/degraded cases or legacy compatibility fixtures, never in the valid new path.

## Hash binding

Hashes are re-derived now over local compiler v2 payload objects using deterministic
canonical JSON (`hash_algorithm = canonical_json_sha256`). No external data, no runtime
source fetch, no platform/API behavior. The bridge compares derived hashes to provided
refs and **BLOCKs on mismatch** (`payload_hash_match = false` ⇒ BLOCKED).

## Fail-closed design

- `REQUIRED_FALSE_FLAGS` (public_ready, live_ready, dispatch_ready,
  executable_dispatch, platform_api_allowed_now, credential_read_allowed_now,
  scheduler_enabled_now, posting_enabled_now, …) force BLOCKED if any is `true`.
- Declared-PASS that contradicts a sub-object state is escalated to BLOCKED via the
  registry's `_apply_declared_state`.
- Roll-up precedence is `BLOCKED > UNKNOWN > REVIEW_REQUIRED > PASS`; empty is `UNKNOWN`.
- Forbidden-runtime and secret detectors are **single-sourced** from
  `scd_platform_capability_registry_v2` (`_unsafe_runtime_hits`, `_secret_hits`); no
  detector literals are re-typed here. No `requests`/`httpx`/`urllib`/`socket`/
  `subprocess`/`os.environ` imports.

## Fixtures

Under `fixtures/scd_compiler_v2_dispatch_bridge/`:
- `payload_hash_manifest_valid_review_required.json`, `..._valid_pass_manual_only.json`.
- `approval_bridge_packet_valid_review_required.json`, `..._valid_pass_manual_only.json`.
- `dispatch_bridge_packet_valid_review_required.json`, `..._valid_pass_manual_only.json`.
- `approval_dispatch_bridge_report_valid_review_required.json`, `..._valid_pass_manual_only.json`.
- `hostile_degraded_cases.json` — legacy combined-result adversarial cases.
- `hostile_degraded_cases_v2_objects.json` — 21 adversarial cases for the four new
  objects, each applying exactly one mutation and expected to fail closed.

The manual-only compiler output slice
`fixtures/scd_platform_payload_compiler_v2/compiler_v2_output_valid_manual_only.json`
lets tests re-derive manual-only hashes. Valid fixtures carry derived hashes only, use
symbolic refs, keep all live/approval/dispatch flags false, and never use
`approved_mock_only`.

## Verification

```
python -m pytest tests/test_scd_compiler_v2_dispatch_bridge.py -q   # 43 passed
python -m pytest tests/ -q                                          # 3060 passed, 28 skipped
python -m pytest tests/test_security_scans.py -q                    # 1 passed
git diff --check                                                    # clean
```

## Boundaries preserved

No provider/platform/LLM API. No credential/env lookup. No network. No scheduler.
No dispatch/posting/webhooks/scraping/autonomous replies/DMs. No public-ready output.
No operator approval and no executable dispatch in the valid path. The compiler v2,
registry v2, dispatch gate, domain model, publish readiness, and redacted audit
modules and their tests/schemas are untouched.
