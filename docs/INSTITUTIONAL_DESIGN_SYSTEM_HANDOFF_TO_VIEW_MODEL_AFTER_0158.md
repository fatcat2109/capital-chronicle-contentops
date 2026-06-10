# Institutional Design System Handoff to View-Model (After 0158)

Task label: TASK_CONTENTOPS_0158_INSTITUTIONAL_DESIGN_SYSTEM_AND_FUTURISTIC_FINTECH_VISUAL_CONTRACT_V0
Repo: A:\Capital Chronicle\tools\cc-live-contentops
Branch: master
Authority: governed by
`docs/INSTITUTIONAL_DESIGN_SYSTEM_AND_FUTURISTIC_FINTECH_VISUAL_CONTRACT_AFTER_0158.md`.

Planning/spec only. This doc defines how task 0159 (UI View-Model Contract v2)
must convert this design system into a schema-validated, redacted, fixture-driven
view-model contract. No API/browser/env dependency is introduced.

## Binding Overview

0159 must bind data to the stable identifiers defined here:
- token IDs (design tokens from the visual contract section 6);
- status token IDs (section 7 vocabulary);
- component IDs (component taxonomy `component_id` values);
- screen IDs (visual contract section 11);
- field IDs (per-component `required_fields`).

## Required View-Model Bindings

- token IDs: the view model references design-token IDs; it never embeds raw hex
  outside the token map. A single token map is the source of truth.
- component IDs: every rendered region maps to a `component_id` from the taxonomy.
- screen IDs: every screen maps to a stable `screen_id`.
- field IDs: each component instance carries exactly its `required_fields` and none
  of its `forbidden_fields`.
- status bindings: each component instance carries one or more status tokens from
  the canonical vocabulary; status is always paired with label + icon.
- redaction flags: any credential/secret field carries a `redacted: true` flag and
  a redacted token; never a value/snippet/length/hash.
- blocked reason arrays: any BLOCKED state carries `blocked_reasons[]` with
  plain-language text.
- evidence refs: evidence components carry `evidence_ref`/`source_ref` references
  only — never raw vendor payloads.

## Global Safety Header Binding

The view model must expose a `global_safety_header` consumed by the Global Safety
Ribbon with: `kill_switch_status`, `live_disabled`, `not_public_postable`,
`review_only`, `local_only`. All default to the safest value when unknown.

## Test Fixtures

0159 must provide deterministic fixtures:
- one valid view-model fixture rendering every screen's required safety state;
- negative fixtures that fail closed: secret-visible, live-enabled, public-ready,
  signal-language, missing-safety-banner, market-direction-color.

## Future Static UI Compatibility

- The view model must be embeddable for `file://` rendering (the existing
  `ui/daily_content_studio/fixture_data.js` pattern), requiring no fetch, no CDN,
  no external scripts, and no storage.
- The 0160 shell prototype consumes the view model to render the static shell.

## No API / Browser / Env Dependency

- The view model is produced by a deterministic CLI summary from existing repo
  packets/fixtures, then embedded. It never reads `.env`, never calls a network/
  platform/provider API, and never triggers browser automation.
- Antigravity remains future-only until 0167 browser QA.

## Handoff Acceptance For 0159

0159 is acceptable when it:
- defines a view-model schema referencing token/component/screen/field IDs here;
- enforces redaction flags and blocked reason arrays;
- exposes the global safety header;
- ships valid + negative fixtures;
- adds a deterministic validator + CLI summary with all live/credential/api/
  scheduler/scraping flags false and secret_visible_count 0;
- introduces no dependency, no backend, no network, no env read.
