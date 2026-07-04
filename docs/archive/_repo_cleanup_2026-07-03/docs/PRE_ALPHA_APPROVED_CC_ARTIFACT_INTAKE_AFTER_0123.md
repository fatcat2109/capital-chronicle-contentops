# Pre-Alpha Approved Capital Chronicle Artifact Intake

**Task:** `TASK_CONTENTOPS_0123_APPROVED_CAPITAL_CHRONICLE_ARTIFACT_INTAKE_CONTRACT_V0`

## Purpose
This document defines the deterministic intake contract for operator-approved Capital Chronicle artifacts. This represents the bridge between the external/sibling core Capital Chronicle repository (where financial data analysis and research occurs) and this local ContentOps skeleton.

## Operating Principles
- **Operator-Supplied / Exported-Only:** The intake mechanism relies entirely on artifacts provided by the operator via local JSON fixtures. It does NOT fetch artifacts from the core repository.
- **No Core Repo Access:** It does not read from or mutate the core `cc_core` repository.
- **No Public-Postable Output:** The intake process only routes artifacts to a local review/intake-ready state (`accepted_for_local_contentops_review`) or blocks them (`blocked`). It never creates publish-ready output.

## Required Fields
To be evaluated, an artifact must at least contain:
- `source_artifact_id`: The ID of the artifact in the core system.
- `operator_approval_ref`: A reference to the operator's manual approval.
- `approval_status`: Must be explicitly set to `"approved"`.
- `content_type`: The type of content (e.g., `market_note`, `macro_education`, `deep_dive`, `data_primer`).
- `freshness`: A definition of the data's recency/time boundary.
- `limitations`: Explicit boundaries or warnings on the data.

## Fail-Closed Behavior
Artifacts are automatically blocked and flagged for unsafe content or missing boundaries. Block conditions include:
- Missing explicit operator approval.
- Missing `source_artifact_id`, `freshness`, or `limitations`.
- Unrecognized `content_type`.
- The artifact implies confident forecast capabilities but the data quality/sufficiency explicitly blocks forecasting.
- The artifact uses proxy data but fails to surface it in the proxy flags.
- Missing or degraded data is hidden.
- Raw vendor data is included with redistribution permitted (violating licensing).
- The artifact contains forbidden financial advice, signal service, "buy/sell/hold", or execution language.
- The artifact contains instructions or flags attempting to enable auto-publish, API payloads, or public-postable states.

## Future Artifact Intake
This local fixture-based contract formalizes how real external artifacts will be structurally validated and triaged into ContentOps. By establishing a strictly filtered, operator-supervised intake funnel, the system ensures that when live pipelines are eventually connected, hazardous inputs (like financial advice or unapproved proxy data) are blocked at the perimeter before ever reaching the prompt engine or editorial reviewers.

## CLI Usage
To view the deterministic summary of the current artifact intake queue (based on local fixtures):
```bash
python -m live_contentops.cli pre-alpha-approved-cc-artifact-intake-summary
```
