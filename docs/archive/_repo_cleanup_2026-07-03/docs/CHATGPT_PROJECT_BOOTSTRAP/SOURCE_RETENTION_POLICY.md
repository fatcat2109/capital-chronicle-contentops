# Source Retention Policy

## Keep As Project Source

Prefer zero Project Sources. If Jim wants one source, keep only this folder:

```text
docs/CHATGPT_PROJECT_BOOTSTRAP/
```

## Do Not Keep As Project Source

- Raw pasted worker transcripts.
- No-extension ChatGPT response files.
- Old upload bundles.
- Stale task prompts whose state is now represented in repo status.
- Screenshots or PDFs unless a committed doc explicitly names them as current authority.
- Duplicate copies of committed docs.

## Normalize Instead

If a chat response matters, normalize it into committed repo artifacts:

- `docs/status/` for current state and blockers.
- `docs/automation/` for deterministic packets/evidence.
- `docs/reports/` for durable reports.
- Tests or code when behavior matters.

Then commit and push. Chat text alone is not durable authority.

## Refresh Rule

After each meaningful repo update, ChatGPT should ask Antigravity to verify current GitHub HEAD and status docs before framing next work.
