# V6 Exact Operator Approval Signature Verifier Operator Runbook - No Approval No Send

Review-only. No provider call. No live send. No approval granted now. No outbox/dispatch readiness.

## Operator Flow

1. Start with valid operator approval ledger gate scaffold bundle.
2. Generate exact operator approval signature verifier scaffold.
3. Review future exact approval declaration template shape.
4. Do not treat sample template as Jim approval.
5. Do not prepare outbox, dispatch, or publish from this scaffold.

## Prohibited

- Provider calls.
- Live send.
- Approval granted now.
- Outbox or dispatch readiness.
- Env or `.env` reads.
- Credential value reads.
- Browser sessions.
- Platform APIs.
- Executable request artifacts.
- Public URLs or metrics.
- Financial advice, signal-service framing, buy/sell/hold, entries/exits, targets, or position sizing.

## Review Notes

Jim owns final authority. This scaffold checks shape only. Future exact phrase may be required later, but phrase is not provided in this scaffold.