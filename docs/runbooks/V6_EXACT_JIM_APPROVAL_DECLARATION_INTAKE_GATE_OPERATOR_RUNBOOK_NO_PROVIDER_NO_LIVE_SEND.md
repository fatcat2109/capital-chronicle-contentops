# V6 Exact Jim Approval Declaration Intake Gate Operator Runbook - No Provider No Live Send

Approval intake only. No provider. No live send. No outbox execution. No dispatch readiness. Accepted approval is only for future outbox preparation.

## Operator Flow

1. Start with accepted exact operator approval signature verifier scaffold bundle.
2. Optionally provide explicit local Jim approval declaration file.
3. Validate exact phrase, payload hash binding, revalidation proof, and no-side-effect flags.
4. Treat accepted result only as future outbox preparation eligibility.
5. Do not execute outbox, dispatch, publish, or live send from this gate.

## Required For Accepted Declaration

- Operator is jim.
- Provided phrase exactly matches required phrase.
- Payload preview IDs, payload hashes, and platforms are non-empty.
- Approval hash binding is present.
- Payload hashes revalidated now is true.
- Revalidation report ID and expires-at string are present.
- Human review remains required.

## Prohibited

- Provider calls.
- Env or `.env` reads.
- Credential value reads.
- Network calls.
- Browser sessions.
- Executable request artifacts.
- Public URLs or metrics.
- Publication readiness.
- Dispatch readiness.
- Live send.
- Financial advice or signal-service framing.

Jim owns final authority. Do not infer, simulate, or invent approval.