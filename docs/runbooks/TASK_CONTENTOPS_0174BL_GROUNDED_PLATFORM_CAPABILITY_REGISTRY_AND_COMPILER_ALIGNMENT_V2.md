# Grounded Platform Capability Registry & Compiler Alignment v2 — TASK_CONTENTOPS_0174BL

LOCAL ONLY | ADVISORY ONLY | FAIL-CLOSED | NOT PUBLIC POSTABLE
NO LIVE POSTING | NO PLATFORM API | NO CREDENTIALS | NO NETWORK
NO SCHEDULING | NO REPLIES/DMS | NO SCRAPING | NO LIVE METRICS
HUMAN (OPERATOR) APPROVAL REQUIRED

Baseline commit: `7998154e43b95342cce4d43b798b3db7ed2d9da5`
Module: `live_contentops/scd_platform_capability_registry_v2.py`

## Purpose

The v2 grounded platform capability registry models, validates, and reconciles
official-documentation-backed platform publishing capability metadata. It answers
one question deterministically and fail-closed: *for each platform, what does the
official documentation say is possible, and what is the repository allowed to do
about it right now?* The answer in this task is always the same for live behavior:
nothing. Capability is recorded as future-gated advisory metadata only.

This module never calls a platform API, reads/requests credentials, builds a
client, opens a socket, schedules work, dispatches content, scrapes, or grants
public/live/dispatch readiness. Every object carries a `validation_state` in
`{PASS, BLOCKED, REVIEW_REQUIRED, UNKNOWN}`.

## Domain Objects

The registry validates nine object kinds, each with a JSON schema in `schemas/`
and a validator in the module:

| Kind | Schema | Validator |
| --- | --- | --- |
| Official doc source | `scd_platform_official_doc_source.schema.json` | `validate_platform_official_doc_source` |
| Official docs verification pack | `scd_platform_official_docs_verification_pack.schema.json` | `validate_platform_official_docs_verification_pack` |
| Capability profile v2 | `scd_platform_capability_profile_v2.schema.json` | `validate_platform_capability_profile_v2` |
| Credential slot policy | `scd_platform_credential_slot_policy.schema.json` | `validate_platform_credential_slot_policy` |
| Live gate checklist | `scd_platform_live_gate_checklist.schema.json` | `validate_platform_live_gate_checklist` |
| Dry-run payload policy matrix | `scd_platform_dry_run_payload_policy_matrix.schema.json` | `validate_platform_dry_run_payload_policy_matrix` |
| Registry↔compiler alignment report | `scd_platform_registry_compiler_alignment_report.schema.json` | `validate_platform_registry_compiler_alignment_report` |
| Publish readiness alignment report | `scd_platform_publish_readiness_alignment_report.schema.json` | `validate_platform_publish_readiness_alignment_report` |
| Redacted audit alignment report | `scd_platform_redacted_audit_alignment_report.schema.json` | `validate_platform_redacted_audit_alignment_report` |

## Approved Platforms (v2)

`telegram`, `x_twitter`, `linkedin`, `facebook_page`, `instagram`, `threads`,
`tiktok`, `substack_newsletter`, `generic_manual`.

## Fail-Closed Rules

The validators enforce these invariants. Any violation downgrades the state
(BLOCKED > UNKNOWN > REVIEW_REQUIRED > PASS via `_rollup` / `_state`):

- **Forbidden runtime values → BLOCKED.** Any string containing live/runtime
  markers (`http://`, `https://`, platform API hosts, `authorization`, `bearer`,
  `token=`, `api_key`, `access_token`, `client_secret`, `refresh_token`,
  `webhook`, `sendmessage`, `setwebhook`, `getupdates`, `dispatch`, `publish now`,
  `go live`, `scheduler`, `scrape`, `autonomous reply`) is blocked.
- **Secret-like values → BLOCKED.** Bot tokens, `sk-`/`ghp_`/`xoxb-`/`AKIA`/`ya29.`
  patterns, private key headers, and bearer-token shapes are blocked anywhere they appear.
- **Forbidden flags must be false.** The twelve `*_now`/readiness flags
  (`REQUIRED_DISABLED_FLAGS`) must be false on every capability profile; any true
  value is BLOCKED.
- **Signal language → BLOCKED.** Financial signal terms (buy/sell/hold/long/short,
  `target price`, `our model predicts`, etc.) in capability text are blocked.
- **Declared-PASS contradiction → BLOCKED.** If a packet declares
  `validation_state: PASS` but the computed state is not PASS, the result is BLOCKED
  with `declared_pass_contradicts_computed_state`. (Honest objects must declare the
  state they can actually justify.)
- **Off-allowlist doc domain → BLOCKED; missing docs → UNKNOWN; stale (>365d) docs
  → REVIEW_REQUIRED.**

## Expected Valid-Fixture States

The reference fixtures in `fixtures/scd_platform_capability_registry_v2/`
produce these states:

- Verification pack: **PASS**
- Capability profiles: **REVIEW_REQUIRED** for the seven future-gated API platforms
  (telegram, x_twitter, linkedin, facebook_page, instagram, threads, tiktok),
  **PASS** for `substack_newsletter` and `generic_manual` (manual-export-only, no
  future live gate claimed).
- Credential slot policy: **PASS** (all slots future-only, no values).
- Live gate checklist (Telegram): **PASS** (all live/dispatch flags false).
- Dry-run payload policy matrix: **PASS**.
- Registry↔compiler alignment report: **REVIEW_REQUIRED** (registry-only platforms
  need future compiler expansion — see below).
- Publish readiness alignment report: **PASS** (still dry-run only).
- Redacted audit alignment report: **PASS** (logging future-only, no live event).
- Registry summary roll-up: **REVIEW_REQUIRED** (inherits the lowest non-blocking state).

## Registry ↔ Compiler Alignment

The existing `scd_platform_payload_compiler.APPROVED_PLATFORMS` set is
`{x_twitter, linkedin, telegram, newsletter, generic_manual}`. The v2 registry adds
`facebook_page`, `instagram`, `threads`, `tiktok`, and `substack_newsletter` (the
registry uses `substack_newsletter` where the compiler uses the older `newsletter`
label). `build_registry_compiler_alignment_report` records these registry-only
platform ids and sets `compiler_expansion_required_later = true`, yielding
REVIEW_REQUIRED. This is intentional: the compiler is not expanded in this task;
the report documents the gap as future work without granting any capability now.
The report still enforces `credential_allowed_now`, `live_allowed_now`, and
`public_ready_allowed_now` all false (any true value is BLOCKED).

## Hostile / Degraded Coverage

`fixtures/scd_platform_capability_registry_v2/hostile_degraded_cases.json` holds
15 adversarial packets, each asserting a specific fail-closed outcome:
missing docs (UNKNOWN), unofficial source (BLOCKED), stale docs (REVIEW_REQUIRED),
live enabled / credential requested / endpoint URL active / token value present /
dispatch enabled / scheduler enabled / public ready / signal language /
declared-PASS-with-unknowns / readiness contradiction / audit platform-api-called /
compiler credential-allowed (all BLOCKED).

## Verification

```
python -m pytest tests/test_scd_platform_capability_registry_v2.py -q
```

Regression scope (must stay green): the compiler, readiness, audit, domain model,
and editorial workbench tests that this module depends on.

## Components

- `live_contentops/scd_platform_capability_registry_v2.py`
- `schemas/scd_platform_*.schema.json` (nine schemas listed above)
- `fixtures/scd_platform_capability_registry_v2/*.json`
- `tests/test_scd_platform_capability_registry_v2.py`
- `docs/platform_official_docs/TASK_CONTENTOPS_0174BL_PLATFORM_OFFICIAL_DOCS_VERIFICATION_PACK.md`
