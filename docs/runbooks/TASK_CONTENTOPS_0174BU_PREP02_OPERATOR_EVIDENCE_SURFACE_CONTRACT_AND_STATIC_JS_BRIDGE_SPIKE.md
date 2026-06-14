# Runbook: Operator Evidence Surface Contract + Static JS Bridge Spike

- **Task label:** TASK_CONTENTOPS_0174BU_PREP02_OPERATOR_EVIDENCE_SURFACE_CONTRACT_AND_STATIC_JS_BRIDGE_SPIKE_V0
- **Mode:** Prep02 only — contract layer, fixtures, deterministic static JS bridge. No heavy V4 UI integration.
- **Source baseline:** `add55ea1c7447770cb9382f86af1794b951ae8f1` ("feat: add operator evidence summary for compiler v2 chain")
- **Source summary task:** TASK_CONTENTOPS_0174BT_OPERATOR_EVIDENCE_SUMMARY_V0

## Purpose

Provide a deterministic, local-only, fail-closed contract layer that projects an
ALREADY-ACCEPTED 0174BT operator evidence summary into a compact, UI-safe surface
object the later heavy 0174BU V4 work can consume. This layer grants nothing. PASS
means only: the surface object is internally consistent, evidence-only, and UI-safe.
It never grants publish / readiness / approval / dispatch / public-ready / live-ready
status, never calls a platform or provider API, never reads credentials or env,
never schedules, posts, scrapes, replies, DMs, creates an audit event, or edits an
audit allow-list.

## Files created

- `schemas/scd_operator_evidence_surface_contract.schema.json` — surface packet schema.
- `live_contentops/scd_operator_evidence_surface_contract.py` — projection + fail-closed validator + static JS bridge string builder.
- `tests/test_scd_operator_evidence_surface_contract.py` — 5 contract tests.
- `fixtures/scd_operator_evidence_surface/evidence_surface_valid_pass_manual_only.json` — PASS projection.
- `fixtures/scd_operator_evidence_surface/evidence_surface_valid_review_required.json` — REVIEW_REQUIRED projection.
- `fixtures/scd_operator_evidence_surface/hostile_degraded_cases.json` — fail-closed mutation matrix.
- `tools/build_operator_evidence_surface_js.py` — deterministic JS artifact generator.
- `ui/institutional_operator_cockpit_v4/operator_evidence_surface.js` — generated static bridge (NOT yet wired into V4).

## Contract fields

The projected surface packet carries: surface schema version + id; source baseline
head/subject/task label; lineage ids (operator evidence summary, compiler output,
compile report, payload hash manifest, bridge report id + hash, readiness alignment,
audit alignment); component states + rollup + blocker/review/unknown counts; a
component state matrix; a no-grant label and allowed-local-action string; a blocked
actions list; evidence path nodes; a required-false flag matrix; truth-model notes;
and the validation state + blocked reasons.

- **Required-true flags (forced true):** evidence_only, non_executable, manual_review_required, local_only, ui_surface_ready.
- **Required-false flags (forced false):** public_ready, live_ready, dispatch_ready, executable_dispatch, platform_api_allowed_now, credential_read_allowed_now, scheduler_enabled_now, posting_enabled_now, audit_event_created, audit_allowlist_modified, readiness_granted.

## Fail-closed precedence

`BLOCKED > UNKNOWN > REVIEW_REQUIRED > PASS`. A required-false flag observed true, or
a required-true flag observed not-true, is BLOCKED. A missing lineage/hash id yields
UNKNOWN (lineage cannot be established). A declared PASS that contradicts a computed
non-PASS fail-closes to BLOCKED.

## Fixture semantics

- **PASS fixture** projects from the accepted 0174BT PASS summary and validates `PASS`.
- **REVIEW fixture** projects from the accepted 0174BT REVIEW summary and validates
  `REVIEW_REQUIRED` — the true source semantics are preserved; no false PASS is forced.
- **Hostile/degraded cases** apply single mutations to a freshly built valid PASS
  packet and assert fail-closed outcomes (see table below).

| case_id | mutation | expected |
| --- | --- | --- |
| required_false_credential_read_true_blocks | credential_read_allowed_now = true | BLOCKED |
| required_true_evidence_only_false_blocks | evidence_only = false | BLOCKED |
| missing_bridge_report_hash_unknown | bridge_report_hash = "" + validation_state = UNKNOWN | UNKNOWN |
| declared_pass_after_missing_bridge_hash_blocks | bridge_report_hash = "" (keep declared PASS) | BLOCKED |
| static_bridge_prefix_safe | none | JS prefix `window.CC_OPERATOR_EVIDENCE_SURFACE =` |

## Generated JS bridge behavior

`tools/build_operator_evidence_surface_js.py` reads the PASS surface fixture and emits
`ui/institutional_operator_cockpit_v4/operator_evidence_surface.js`, which defines
exactly one frozen read-only global, `window.CC_OPERATOR_EVIDENCE_SURFACE`, using
deterministic canonical JSON (sorted keys, fixed indent). The artifact is then frozen
via `Object.freeze`.

- `python tools/build_operator_evidence_surface_js.py --write` regenerates the artifact.
- `python tools/build_operator_evidence_surface_js.py --check` fails if the on-disk
  artifact is stale (not byte-identical to a fresh regeneration), proving determinism.

The generator scans its own generated output and rejects any networking / storage /
credential token (remote URL schemes, `fetch(`, `XMLHttpRequest`, `WebSocket`,
`EventSource`, `sendBeacon`, `localStorage`, `sessionStorage`, env-var access, dotfile
secrets, API-key / bearer-token / endpoint / market-data strings).

## No credentials / API / network

No file in this task reads credentials, env files, API keys, tokens, secret stores,
browser profiles, platform config, or provider config. No network call, scheduler,
posting, scraping, upload, export, or browser automation is performed. The contract
module imports only domain-model + capability-registry helpers; the generator imports
only `json` / `pathlib` / `argparse` / `sys`.

## Validation commands

```
python -m py_compile live_contentops/scd_operator_evidence_surface_contract.py tests/test_scd_operator_evidence_surface_contract.py tools/build_operator_evidence_surface_js.py
python tools/build_operator_evidence_surface_js.py --write
python tools/build_operator_evidence_surface_js.py --check
python -m pytest tests/test_scd_operator_evidence_surface_contract.py tests/test_scd_operator_evidence_summary.py -q
python -m pytest tests/test_security_scans.py -q
git diff --check
```

## Protected paths (not edited by this task)

`ui/institutional_operator_cockpit_v4/index.html`, `view_model.js`, `cockpit.js`,
`styles.css`; `live_contentops/scd_operator_evidence_summary.py`,
`scd_compiler_v2_dispatch_bridge.py`, `scd_compiler_v2_bridge_publish_evidence.py`,
`scd_platform_payload_compiler_v2.py`; existing 0174BN/0174BP/0174BR/0174BT
schemas/fixtures/tests (read-only); `ui/institutional_shell/**`;
`docs/design_references/**`; `docs/browser_qa/**`; and all env / credential / token /
platform-adapter / provider-API / scheduler / posting / scraping / ingestion paths.

## Next task

`TASK_CONTENTOPS_0174BU_HEAVY_OPERATOR_EVIDENCE_SURFACE_V4_INTEGRATION_BUILDER_V0`
— wire the generated bridge into the V4 cockpit surface (heavy UI integration).
