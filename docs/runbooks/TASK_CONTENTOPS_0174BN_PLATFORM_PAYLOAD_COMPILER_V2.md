# TASK_CONTENTOPS_0174BN — Platform Payload Compiler v2 (registry-aligned, parallel)

LOCAL ONLY | DRY-RUN / MANUAL-EXPORT ONLY | FAIL-CLOSED
NO LIVE / API / CREDENTIAL / NETWORK / SCHEDULER / DISPATCH / POSTING / SCRAPING

Baseline master: `3ff6a9cf31440a78aa77228181b12a13b80be094`
Subject: `feat: add grounded platform capability registry v2`
Branch: `task/0174bn-platform-payload-compiler-v2-registry-aligned`

## Purpose

`scd_platform_payload_compiler_v2.py` is a **new, parallel** payload compiler aligned
with the grounded platform capability registry v2. It expands platform coverage from
the 5 platforms of the frozen 0174AR compiler to the **9 registry-approved platforms**
(`telegram`, `x_twitter`, `linkedin`, `facebook_page`, `instagram`, `threads`,
`tiktok`, `substack_newsletter`, `generic_manual`) and routes payload shape by the
registry's `current_repo_allowed_state` semantics.

The existing 0174AR compiler (`scd_platform_payload_compiler.py`), its schemas,
fixtures, and tests are left completely unchanged. v2 is additive.

## What it does

- Validates four v2 contract objects, each returning `{validation_state, reasons}`
  with state in `{PASS, BLOCKED, REVIEW_REQUIRED, UNKNOWN}`:
  - `SCDPlatformConstraintProfileV2`
  - `SCDPlatformPayloadCompilerV2Input`
  - `SCDPlatformPayloadCompilerV2Output`
  - `SCDPlatformPayloadCompileReportV2`
- Provides `compile_platform_payloads_v2()`, a deterministic local helper that
  **invents nothing**: source text/citations/limitations/disclosures are carried
  verbatim; no new links, hashtags, handles, claims, or metrics; character overflow
  is flagged (count vs limit), never silently truncated.
- Provides `rollup_compile_report_v2()` with fail-closed precedence
  (`BLOCKED > UNKNOWN > REVIEW_REQUIRED > PASS`; empty set is `UNKNOWN`).

## Shape routing

| Shape | Platforms |
| --- | --- |
| `manual_export` | `substack_newsletter`, `generic_manual` |
| `dry_run` | all others (`telegram`, `x_twitter`, `linkedin`, `facebook_page`, `instagram`, `threads`, `tiktok`) |

`tiktok` remains `REVIEW_REQUIRED` (last-priority / high-friction) even when no
hostile condition is present. No platform compiles to any live shape.

## Alias map

`newsletter -> substack_newsletter`, `substack -> substack_newsletter`,
`x`/`twitter`/`x/twitter` -> `x_twitter`. The legacy 0174AR compiler keeps its own
`newsletter` id unchanged; only v2 canonicalizes.

## Safety design

- Imports only `re`-free internal modules plus the registry v2 module. No
  `requests`/`httpx`/`urllib`/`socket`/`subprocess`/`os.environ`.
- Forbidden-runtime and secret detectors are **single-sourced** from
  `scd_platform_capability_registry_v2` (`_unsafe_runtime_hits`, `_secret_hits`), so
  detector literals are never re-typed here.
- `REQUIRED_FALSE_FLAGS_V2` (public_ready, live_eligibility, live_ready,
  dispatch_ready, and every `*_now` flag) force BLOCKED if any is `true`.
- Declared-PASS that contradicts the computed state is escalated to BLOCKED via the
  registry's `_apply_declared_state`.

## Fixtures

Under `fixtures/scd_platform_payload_compiler_v2/`:
- `constraint_profiles_v2_valid.json` — 9 profiles at expected states.
- `compiler_v2_input_valid_all_platforms.json`, `compiler_v2_input_aliases_valid.json`.
- `compiler_v2_output_valid_all_platforms.json` (9 payloads, per-platform shapes).
- `compiler_v2_report_valid_review_required.json`, `compiler_v2_report_valid_pass_manual_only.json`.
- `registry_profiles_input.json`.
- `hostile_degraded_cases.json` — adversarial inputs whose expected state is
  BLOCKED/UNKNOWN/REVIEW_REQUIRED (these legitimately carry forbidden strings as
  block-test inputs).

Valid fixtures use symbolic citation refs only (no URL schemes), neutral wording
(no trading-signal words), `operator_review_required = true`, and all live flags false.

## Verification

```
python -m py_compile live_contentops/scd_platform_payload_compiler_v2.py tests/test_scd_platform_payload_compiler_v2.py
python -m pytest tests/test_scd_platform_payload_compiler_v2.py -q          # 33 passed
python -m pytest tests/test_scd_platform_payload_compiler.py tests/test_scd_platform_capability_registry_v2.py tests/test_publish_automation_readiness.py tests/test_redacted_publish_audit_log.py tests/test_scd_domain_model.py tests/test_scd_editorial_workbench.py -q  # 191 passed
python -m pytest -q                                                          # 3010 passed, 28 skipped
python -m pytest tests/test_security_scans.py -q                             # 1 passed
git diff --check                                                             # clean
```

## Boundaries preserved

No provider/platform/LLM API. No credential/env lookup. No network. No scheduler.
No dispatch/posting/webhooks/scraping/autonomous replies/DMs. No public-ready output.
No financial advice or signal framing. The frozen 0174AR compiler and its
tests/schemas are untouched.
