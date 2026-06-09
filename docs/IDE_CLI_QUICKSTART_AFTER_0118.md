# IDE CLI Quickstart (After 0118)

**Task:** `TASK_CONTENTOPS_0119_PROJECT_SOURCES_REFRESH_AFTER_0118_V0`
**Baseline:** `master`, HEAD `5b6b493`

If you are an agent joining this repository after a session break, here is the immediate operational state and your required context.

## 1. Safety Bounds
- **We are in Pre-Alpha Local-Only mode.**
- There are no LLMs attached to the execution flow.
- There are no APIs, no networks, no scheduled tasks, and no autonomous publishers.
- Do NOT add `requests`, `openai`, `httpx`, or any networking libraries.
- Do NOT read `.env` or access credentials.
- Do NOT infer publication or metrics without manual operator entry.

## 2. Operator Commands
The operator interacts with the system solely via `python -m live_contentops.cli <command>`.

**To see all operator commands:**
```bash
python -m live_contentops.cli operator-command-summary
```

**The current 7-step Operator Workflow is detailed in:**
`docs/PRE_ALPHA_OPERATOR_WORKFLOW_CONSOLIDATION_AFTER_0118.md`

## 3. How to Execute Tests
All new code must pass rigorous local testing and security scans.
```bash
python -m pytest -q
```
*(This should execute all tests locally including `test_security_scans.py` without attempting any live operations.)*
