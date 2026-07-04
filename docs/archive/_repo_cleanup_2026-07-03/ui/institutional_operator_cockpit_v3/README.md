# Operator Cockpit V3 (brandkit-grounded clean-room rebuild)

Task: TASK_CONTENTOPS_0174B_OPERATOR_COCKPIT_V3_BRANDKIT_GROUNDED_CLEAN_ROOM_REBUILD_V0

## Purpose

A local-only, static, fixture-driven, evidence-grade Operator Cockpit for
Capital Chronicle ContentOps. V3 is a clean-room rebuild grounded in the
quarantined Stitch "Technical Matte" brandkit, pushed toward a futuristic
institutional macro research / content-governance control room while preserving
every safety boundary.

This replaces the paused/superseded V2 incremental repair. V2
(`ui/institutional_operator_cockpit_v2/`) is retained untouched as legacy
failed-candidate evidence; it is not modified, deleted, or renamed by this task.

## How To Use

Open `index.html` directly in a browser (file://). Everything renders from the
local canonical view model. There is no build step and no server.

## Safety Boundaries (hard)

- Local-only, static, fixture-driven. No runtime network: no fetch, no
  XMLHttpRequest, no WebSocket, no EventSource, no remote dependency.
- No remote CDN / fonts / icons / scripts. Local system font stacks only.
- Kill switch active. Live posting disabled. Platform/provider/Telegram APIs
  disabled. Scheduler disabled. Scraping disabled.
- Credential read disabled. Env read disabled. No secrets read/printed/displayed.
- No financial advice, no buy/sell/hold, no position sizing, no signal-service
  framing, no market-direction color semantics.
- No enabled controls implying publish/post/send/schedule/dispatch/API/export.

## Source Of Truth vs Provenance

- Current operational truth comes only from
  `CC_COCKPIT_V3_VIEW_MODEL.global_state`:
  - Current Repo Baseline: `c56ccd9`
  - V2 Build Candidate: `dd55114`
  - Design Reference Quarantine: `1024cdf`
  - Automated Browser QA Evidence: `75f9d47`
  - Visible Browser QA Evidence: `c56ccd9`
  - Product UI Track: V3 clean-room rebuild
  - Product UI Status: `AWAITING_0174B_V3_AUDIT`
- `680d03d` is a historical pre-0174R docs/setup baseline only and is NOT current
  build truth. It appears only under the Evidence Vault commit timeline labelled
  historical.
- Historical screen provenance (`15b87ff`, `1c03ca0`, `444ef2c`) lives in
  `historical_screen_provenance`, labelled "Not Runtime Authority".
- Stitch reference provenance is "Visual Reference Only / Not Runtime Authority".

## Screens

Command Center, Content Studio, Publish Readiness Tower, Evidence Vault,
Content Calendar / Workflow Board, Visual Export / Screenshot-Safe Mode,
Settings / Safety Policy.

## Status Token Contract

Critical statuses carry `status`, `severity`, `label`, `reason`,
`evidence_ref_ids`, `allowed_actions`, `blocked_actions`, `current_truth`,
`historical_provenance`, and an optional `caveat`. Allowed vocabulary: PASS,
DEGRADED, BLOCKED, REVIEW_REQUIRED, LIVE_DISABLED, NOT_PUBLIC_POSTABLE,
FUTURE_ONLY, UNKNOWN, SECRET_REDACTED. PASS means system/validation-safe only;
never publish-ready, live-ready, forecast-ready, or market-positive.

## Reference

See `docs/TASK_CONTENTOPS_0174B_V3_BRANDKIT_EXTRACTION.md` and
`docs/TASK_CONTENTOPS_0174B_V3_TASTE_ALIGNMENT_PLAN.md` for the brandkit
extraction and taste gate that grounded this rebuild. Stitch references are
quarantined under `docs/design_references/` and were used as advisory visual
reference only (not copied, not imported, not runtime).
