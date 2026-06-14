# TASK_CONTENTOPS_0174BR — Compiler v2 Bridge → Publish Evidence Alignment (parallel)

LOCAL ONLY | EVIDENCE-ONLY | FAIL-CLOSED | NO READINESS GRANT | NO AUDIT EVENT
NO LIVE / API / CREDENTIAL / NETWORK / SCHEDULER / DISPATCH / POSTING / SCRAPING

Baseline master: `09e0c34cdd4b438c46e49b77561be6f7ef94e2f9`
Subject: `fix: add missing manual-only compiler v2 fixture`
Branch: `task/0174br-compiler-v2-bridge-publish-evidence-alignment`

## Purpose

`scd_compiler_v2_bridge_publish_evidence.py` is a **new, parallel** local-only
evidence-alignment module. It binds the ALREADY-ACCEPTED compiler v2
approval-dispatch bridge report (0174BP) to two downstream concerns as
**evidence only**:

1. `compiler_v2_bridge_publish_readiness_alignment`
2. `compiler_v2_bridge_redacted_audit_alignment`

The module never grants publish/readiness, approval, dispatch, or public-ready
status; never calls a provider/platform API, reads credentials/env, or
schedules/posts; never creates a real audit event or edits any audit event
allow-list; and never edits any accepted module (readiness, audit, bridge,
registry, compiler, gate, or domain). It is purely additive evidence.

## Two-object contract

Each object is validated to `{validation_state, reasons}` with state in
`{PASS, BLOCKED, REVIEW_REQUIRED, UNKNOWN}`:

| Object | Builder | Role |
| --- | --- | --- |
| Publish-readiness alignment | `build_compiler_v2_bridge_publish_readiness_alignment` | Binds the bridge report to publish-readiness evidence — **no readiness grant** |
| Redacted-audit alignment | `build_compiler_v2_bridge_redacted_audit_alignment` | Binds the bridge report to FUTURE redacted-audit evidence — **no event creation** |

Both validators are registered in
`COMPILER_V2_BRIDGE_PUBLISH_EVIDENCE_VALIDATORS` for data-driven hostile tests.

## Bridge-report binding method

The bound bridge report is identified by its lineage ids
(`bridge_report_id`, `compiler_output_id`, `compile_report_id`,
`payload_hash_manifest_id`) plus a canonical `bridge_report_hash` derived with
the shared `canonical_json_sha256` helper over the whole bridge report object.

Per-platform payload hashes are **not** re-derived here — 0174BP already owns
the payload hash manifest. Each builder runs the authoritative
`validate_compiler_v2_approval_dispatch_bridge_report` on the bound report and
propagates its four-state result. PASS is only reachable when the bound bridge
report itself validates PASS and zero contradictions exist; PASS still grants
nothing.

## Evidence-only / no-grant semantics

In the valid path:

- `readiness_granted = false`, `publish_ready = false`, `public_ready = false`.
- `audit_event_created = false`, `audit_allowlist_modified = false`,
  `audit_event_type_registered_now = false`; the requested event type is a
  future-only label, never a live registration.
- `secrets_redacted = true`; `credential_values_present`,
  `token_values_present`, `raw_vendor_payload_present` are all `false`.
- `local_only`, `evidence_only`, `non_executable`, `manual_review_required`,
  `bridge_report_bound`, `redacted_safe` are all `true`.
- All live/dispatch/API/credential/scheduler/posting `*_now` flags are `false`.

## Fail-closed design

- Required-false flags force BLOCKED if any is `true`; required-true flags force
  BLOCKED if any is not `true`.
- A declared-PASS that contradicts the computed state is escalated to BLOCKED
  via the registry's `_apply_declared_state`.
- Roll-up precedence is `BLOCKED > UNKNOWN > REVIEW_REQUIRED > PASS`.
- A bound bridge report that is BLOCKED ⇒ BLOCKED; UNKNOWN ⇒ UNKNOWN;
  REVIEW_REQUIRED ⇒ REVIEW_REQUIRED.
- Forbidden-runtime and secret detectors are **single-sourced** from
  `scd_platform_capability_registry_v2` (`_unsafe_runtime_hits`,
  `_secret_hits`); no detector literals are re-typed here. No
  `requests`/`httpx`/`urllib`/`socket`/`subprocess`/`os.environ` imports.

## Fixtures

Under `fixtures/scd_compiler_v2_bridge_publish_evidence/`:
- `publish_readiness_alignment_valid_pass_manual_only.json`,
  `publish_readiness_alignment_valid_review_required.json`.
- `redacted_audit_alignment_valid_pass_manual_only.json`,
  `redacted_audit_alignment_valid_review_required.json`.
- `hostile_degraded_cases.json` — 22 adversarial cases for the two objects, each
  applying exactly one mutation and expected to fail closed.

Valid fixtures are regenerated deterministically from the builders; the
`bridge_report_hash` is derived, never hand-written.

## Verification

```
python -m pytest tests/test_scd_compiler_v2_bridge_publish_evidence.py -q   # 55 passed
python -m pytest tests/ -q                                                  # 3072 passed, 28 skipped
python -m pytest tests/test_security_scans.py -q                            # 1 passed
git diff --check                                                            # clean
```

## Boundaries preserved

No provider/platform/LLM API. No credential/env lookup. No network. No
scheduler. No dispatch/posting/webhooks/scraping/autonomous replies/DMs. No
public-ready output. No readiness grant. No audit event creation and no audit
allow-list modification. The compiler v2, registry v2, dispatch gate, domain
model, publish readiness, and redacted audit modules and their tests/schemas are
untouched.
