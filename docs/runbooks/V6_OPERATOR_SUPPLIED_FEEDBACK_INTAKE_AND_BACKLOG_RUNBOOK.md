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
## V5 adapter regen/check guardrail

- Canonical packets are the source of truth:
  - `docs/automation/V6_OPERATOR_SUPPLIED_FEEDBACK_INTAKE_AND_BACKLOG/operator_supplied_feedback_intake_packet.json`
  - `docs/automation/V6_OPERATOR_SUPPLIED_FEEDBACK_INTAKE_AND_BACKLOG/operator_feedback_backlog_summary_packet.json`
- The V5 adapter `ui/contentops_v5/src/data/operatorFeedbackBacklogAdapter.ts` must be regenerated or checked after either packet changes.
- Use the deterministic local checker:

```powershell
python live_contentops/operator_feedback_backlog_v5_adapter_codegen_v6.py
pytest tests/test_operator_feedback_backlog_v5_adapter_codegen_v6.py
```

The check is local and deterministic only. It does not read env values, credentials, browser session data, cookies, localStorage, sessionStorage, tokens, public URLs, provider APIs, LLM APIs, platform APIs, or live platform state.
