# Project Source Export (After 0121)

**Task:** `TASK_CONTENTOPS_0122_PROJECT_SOURCES_REFRESH_AFTER_0121_V0`
**Baseline:** `master`, HEAD `271153a`

This bundle represents the safe, local-only snapshot of the pre-alpha ContentOps system after the Markdown UX export (task 0121). It is curated specifically to be uploaded to ChatGPT as Project Sources.

## Scope of Export
This export contains only safe markdown documentation and JSON schemas. It does not include:
- Executable Python code or tests.
- Internal tools or scripts.
- Secrets, credentials, `.env` files, or API keys.
- Raw provider logs, vendor data, or channel IDs.

This ensures the LLM's context contains the rules, architecture, and current operator workflow without risking credential leakage or flooding the token limit with backend boilerplate.

## Deletion Guidance for ChatGPT Project Sources
If you are an operator updating ChatGPT Project Sources:
1. Delete any older `cc-live-contentops` bundles (e.g., `AFTER_0118`, `AFTER_0112`, `AFTER_0108`, `AFTER_0101`, `AFTER_0074`).
2. Upload the new contents of the `project_sources_bundle_AFTER_0121` folder.
3. This ensures the LLM understands the newly consolidated 0121 workflow.
