# Pre-Alpha Platform-Specific Manual Export Templates (After Task 0110)

## What this is

Task 0110 adds a local-only **platform-specific manual export template** layer on
top of the existing 0107 manual export batch and 0108 publish-record layers. It
takes CLEAN 0107 manual export packets and produces deterministic, per-platform
copy/paste template records for the operator.

This is **platform-specific manual copy/paste formatting only**. It improves the
operator copy/paste workflow by adapting approved text to a platform family's
expected shape (short-form vs professional long-form vs markdown) and attaching
conservative formatting guidance and a mandatory operator final-check reminder.

## What this is NOT

This layer **does not**, and **cannot**:

- post, schedule, or send anything
- call a platform API, provider, LLM, network, or search endpoint
- generate platform API payloads or request bodies
- scrape platforms or ingest metrics (automatic or otherwise)
- read credentials or `.env`
- auto-publish or auto-approve
- produce public-postable output
- verify current/exact platform specifications
- emit financial advice, buy/sell/hold, position sizing, price targets, signal
  language, or guaranteed prediction
- emit fake Capital Chronicle alpha output

Every record and the packet itself pin non-publishing flags and the packet
**fails closed** (`packet_status="blocked"`) on any unsafe condition.

## Supported platform families

| Platform family | Manual template format    | Notes |
| --------------- | ------------------------- | ----- |
| `x`             | `short_form_plain_text`   | conservative ~280 char local guidance |
| `threads`       | `short_form_plain_text`   | concise short-form local guidance |
| `linkedin`      | `professional_long_form`  | professional long-form local guidance |
| `newsletter`    | `newsletter_markdown`     | markdown long-form |
| `generic`       | `generic_markdown`        | generic markdown |

Any other platform family (e.g. `tiktok`, `facebook_page`, `instagram`) is
**unsupported** and routed to `unsupported_or_blocked_exports`, failing the
packet closed.

## Conservative local guidance, not verified specs

Platform length/format notes are **conservative local guidance only**. They are
not verified current platform specifications. Verifying actual current platform
rules is the operator's responsibility before any manual posting. Each record's
`formatting_notes` and the packet `operator_final_checklist` state this
explicitly, and the summary reports `current_platform_spec_verified=false`.

## Template behavior

- Only CLEAN 0107 export packets
  (`export_status=prepared_for_operator_review`, `manual_copy_ready=true`, no
  `blocked_reasons`) produce template records.
- Blocked export packets are preserved in `unsupported_or_blocked_exports`, never
  templated as clean.
- Unknown platform families fail closed and appear in
  `unsupported_or_blocked_exports`.
- Source attribution (`source_artifact_ids` or `is_general_process_content`) and
  `limitations` are carried into every template record; missing attribution
  blocks.
- Every `copy_paste_text` is wrapped with a leading
  `[MANUAL COPY/PASTE - OPERATOR FINAL CHECK REQUIRED - NOT PUBLIC POSTABLE]`
  marker and a trailing verification reminder.
- No platform API payload / request body is ever generated.

## Hard-boundary flags (pinned)

```
local_only                          = true
fixture_only                        = true
manual_copy_paste_only              = true
operator_final_check_required       = true
platform_api_call_allowed_now       = false
provider_call_allowed_now           = false
network_call_allowed_now            = false
scheduler_allowed                   = false
automatic_metrics_ingestion_allowed = false
scraping_allowed                    = false
credential_or_env_read_allowed      = false
live_execution_allowed_now          = false
auto_publish                        = false
public_postable                     = false
```

## Files

- `schemas/pre_alpha_platform_manual_template_packet.schema.json`
- `live_contentops/pre_alpha_platform_manual_templates.py`
- `fixtures/pre_alpha_platform_manual_templates/valid_platform_manual_template_config.json`
- `tests/test_pre_alpha_platform_manual_templates.py`
- CLI command: `pre-alpha-platform-manual-templates-summary`

## CLI

```
python -m live_contentops.cli pre-alpha-platform-manual-templates-summary
```

Prints a deterministic JSON summary including `packet_status`,
`platform_template_record_count`, `unsupported_or_blocked_count`,
`platform_family_counts`, `unsafe_flag_count`, and all non-network / provider /
platform / scheduler / scraping / credential flags pinned false.

## Determinism

The packet chains deterministically off the accepted 0107 default fixture (which
itself chains off 0106 -> 0105 -> ...). Repeated runs produce identical output
(stable IDs/order/counts via the shared `STATIC_TIMESTAMP` convention). Every
clean eligible export maps to exactly one `platform_template_record`.

## Operator final check

The operator final check remains **mandatory**. This system never decides that
content is publish-ready or platform-ready. It only formats approved text for
manual copy/paste and surfaces conservative guidance plus a final-check
reminder.
