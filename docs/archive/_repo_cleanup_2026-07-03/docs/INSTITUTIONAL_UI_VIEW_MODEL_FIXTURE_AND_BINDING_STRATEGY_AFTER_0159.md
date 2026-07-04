# Institutional UI View-Model Fixture and Binding Strategy (After 0159)

Task label: TASK_CONTENTOPS_0159_INSTITUTIONAL_UI_VIEW_MODEL_CONTRACT_V2_V0
Repo: A:\Capital Chronicle\tools\cc-live-contentops
Branch: master
Authority: governed by
`docs/INSTITUTIONAL_UI_VIEW_MODEL_CONTRACT_V2_AFTER_0159.md`.

Contract/spec only. No active front-end code, no network, no env, no credentials.

## Fixture Philosophy

- Deterministic: the same fixture in always renders the same view out.
- Local-only and embeddable: fixtures are plain JSON, embeddable for `file://`
  rendering using the existing `ui/daily_content_studio/fixture_data.js` pattern.
- Redacted by construction: fixtures never contain secrets, env paths, raw vendor
  data, raw platform responses, raw request URLs, public-ready copy, or signal
  language.
- Safe-by-default: all live/credential/api/scheduler/scraping flags are false.

## Valid Fixture

`fixtures/institutional_ui_view_model_contract_v2_valid.json` represents the full
contract with all 12 required screens, the component registry, the status token
registry, the safety banner set, the global state model, the redaction policy, the
evidence_ref policy, the blocked_action policy, the safety policy, the fixture
strategy, and the future handoff. It validates `packet_status: pass`.

## Invalid Fixtures

`fixtures/institutional_ui_view_model_contract_v2_invalid_live_enabled.json`
flips `live_posting_enabled_now`, `platform_api_allowed_now`, and
`credential_read_allowed_now` to true and sets `packet_status: pass`. The
validator must fail closed on this fixture, demonstrating the fail-closed contract.

Additional negative cases are covered programmatically in the test module by
mutating the valid packet:
- platform_api_allowed_now true;
- credential_read_allowed_now true;
- active_frontend_code_changed true;
- missing required screen;
- missing required status token;
- missing required component;
- public_ready_final_copy_generated true;
- screenshot-safe redaction disabled;
- telegram_pilot_gate missing CHANNEL_PERMISSION_UNVALIDATED;
- publish_readiness_tower enabling publish-all;
- content_calendar including a scheduled/live state;
- visual_export_studio without screenshot redaction;
- settings_safety_policy displaying credentials.

## Binding Strategy

- token IDs: the view model references status_token_id values from the 0158
  vocabulary; the status_token_registry is the source of truth.
- component IDs: every rendered region maps to a component_id from the 0158
  taxonomy via the component_registry.
- screen IDs: every screen maps to a stable screen_id; the fixture provides one
  fixture_id per screen.
- field IDs: each component instance carries exactly its required_fields and none
  of its forbidden_fields.
- status bindings: each component instance carries status tokens from the registry;
  status is always paired with label + icon.
- redaction flags: any credential/secret field carries a redacted token and never
  a value/snippet/length/hash.
- blocked reason arrays: any BLOCKED state carries blocked_reasons[] with
  plain-language text.
- evidence refs: evidence-facing components carry evidence_ref/source_ref
  references only — never raw payloads.

## Fixture Generation

The deterministic CLI summary
(`pre-alpha-institutional-ui-view-model-contract-v2-summary`) builds the packet
in-memory from the validator module and validates it. A future task may serialize
this into an embeddable `fixture_data.js`-style asset for the 0160 shell; that
serialization is out of scope here.

## Forbidden Fixture Content

Fixtures must not include:
- real token / chat ID;
- env path;
- raw platform response;
- raw request URL;
- public-ready social post text;
- trading / signal / advice language.
