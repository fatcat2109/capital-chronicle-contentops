# IDE CLI Quickstart (After 0123)

**Task:** `TASK_CONTENTOPS_0124_PROJECT_SOURCES_REFRESH_AFTER_0123_V0`

The ContentOps local environment uses a structured CLI. The operator-facing commands are strictly read-only, emitting diagnostic JSON or human-readable Markdown to stdout. No state is modified; all output relies on local JSON fixtures.

## 0123 Daily Operator Commands

```bash
# View skeleton status and constraints
python -m live_contentops.cli status

# View the preferred, human-readable Daily Operator Workbench (Markdown)
python -m live_contentops.cli pre-alpha-daily-operator-markdown-export

# View the raw JSON for the local editorial packet and prompt variables
python -m live_contentops.cli pre-alpha-daily-operator-content-run-summary

# View the raw JSON generated for specific platform template requirements
python -m live_contentops.cli pre-alpha-platform-manual-templates-summary
```

## Intake and Audit Commands

```bash
# View the deterministic validation of operator-approved artifacts from the core repo
python -m live_contentops.cli pre-alpha-approved-cc-artifact-intake-summary
```

## Post-Publish Optional Reminders

```bash
# Optional manual recordkeeping after a human operator publishes externally
python -m live_contentops.cli pre-alpha-manual-publish-record-summary

# Optional manual performance data entry placeholder
python -m live_contentops.cli pre-alpha-manual-performance-record-summary

# Optional local qualitative content performance review based on manual records
python -m live_contentops.cli pre-alpha-content-performance-review-summary
```

## Exploring All CLI Options
```bash
# Lists all registered commands categorized by daily flow vs. internal debug 
python -m live_contentops.cli operator-command-summary
```
