# Project Source Export (After 0123)

**Task:** `TASK_CONTENTOPS_0124_PROJECT_SOURCES_REFRESH_AFTER_0123_V0`
**Baseline:** `master`, HEAD `ab3aa01`

This bundle represents the safe, local-only snapshot of the pre-alpha ContentOps system after the formalization of the Approved CC Artifact Intake contract (task 0123). It is curated specifically to be uploaded to ChatGPT as Project Sources.

## Scope of Export
This export contains only safe markdown documentation and JSON schemas. It does not include:
- Executable Python code or tests.
- Internal tools or scripts.
- Secrets, credentials, `.env` files, or API keys.
- Raw provider logs, vendor data, or channel IDs.

This ensures the LLM's context contains the rules, architecture, and current operator workflow without risking credential leakage or flooding the token limit with backend boilerplate. The bundle has been curated to < 20 files to remain lean and tightly focused on the active edges of the control plane.

## Deletion Guidance for ChatGPT Project Sources
If you are an operator updating ChatGPT Project Sources:
1. Delete any older `cc-live-contentops` bundles (e.g., `AFTER_0121`, `AFTER_0118`, `AFTER_0112`, `AFTER_0108`, `AFTER_0101`, `AFTER_0074`).
2. Upload the new contents of the `project_sources_bundle_AFTER_0123` folder.
3. This ensures the LLM understands the newly consolidated 0123 workflow and active artifact intake schemas.
