# cc-live-contentops

Future live control plane skeleton for Capital Chronicle.

**CURRENT STATUS:**
- This repo is a future live control plane skeleton. Currently, it operates exclusively in **Pre-Alpha Local-Only Mode**.
- No keys, no network, no provider calls, no platform APIs, no scheduling execution, no publishing, no scraping, no autonomous replies/DMs.
- No core repo mutation.
- All live capabilities require future explicit GO.

## Current Pre-Alpha Operator Workflow
For the authoritative guide on the daily manual publish sequence and performance review workflow, please see:
[PRE_ALPHA_OPERATOR_WORKFLOW_CONSOLIDATION_AFTER_0118.md](docs/PRE_ALPHA_OPERATOR_WORKFLOW_CONSOLIDATION_AFTER_0118.md)

**Minimal Commands:**
- `python -m live_contentops.cli pre-alpha-daily-operator-markdown-export` : (PREFERRED) View the daily readable workbench.
- `python -m live_contentops.cli operator-command-summary` : View all available operator commands.
- `python -m live_contentops.cli status` : Show local skeleton status.
