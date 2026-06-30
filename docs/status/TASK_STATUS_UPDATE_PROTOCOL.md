# Task Status Update Protocol

## Mandatory future rule

1. Every Antigravity task must read `docs/status/CURRENT_PROJECT_STATUS.md` and `docs/status/current_project_status.json` before planning edits.
2. Every task must update both status files before final commit unless it is explicitly read-only/no-commit.
3. If the task changes dashboard/UI authority, next task pointer, live/env/provider capability, accepted blockers, or canonical surface, the status doc must be updated in the same task.
4. Final evidence must include status-doc update summary.
5. If status doc conflicts with GitHub remote or fetched repo files, mark BLOCKED and create a reconciliation prompt.
6. Do not use chat memory or Project Sources as runtime authority when status doc and repo files disagree.
7. For UI tasks, canonical dashboard path must be checked from the status doc and authority map before any implementation.
8. Stale standalone UI pages must not become canonical through convenience.

## Commit discipline

Non-read-only tasks must stage the updated status markdown and JSON alongside the task change. If the task cannot safely update status, it must stop before commit and report why.

## Final evidence discipline

Final evidence must name whether the status files were updated, summarize changed status fields, and cite the canonical dashboard surface used for UI work.
