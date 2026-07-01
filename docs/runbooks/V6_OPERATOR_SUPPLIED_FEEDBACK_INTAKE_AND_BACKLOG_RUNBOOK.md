# V6 Operator-Supplied Feedback Intake and Backlog Loop

This runbook covers the local/manual-only feedback intake loop for the accepted manual distribution lanes.

## Scope

- Operators paste audience feedback, questions, or editorial notes into local fixtures.
- Deterministic builders emit an intake packet and a backlog summary packet.
- Backlog candidates are grouped by tags only; no LLM/provider call is made.

## Safety boundaries

- No env or credential read.
- No provider, LLM, platform API, browser session, public URL fetch, scrape, or verification.
- No approve, send, publish, dispatch, schedule, reply, DM, like, repost, or quote-post action.
- Optional URL/reference text is treated as operator-supplied text and hashed locally only.

## Commands

```powershell
python -m live_contentops.operator_supplied_feedback_intake_v6
python -m live_contentops.operator_feedback_backlog_summary_v6
pytest tests/test_operator_supplied_feedback_intake_and_backlog_v6.py
```

## Operator interpretation

The backlog summary is ready for manual operator review only. It is not a live readiness packet, not a public verification result, and not financial advice.
