# LIMITED LIVE PILOT DESIGN (IF FUTURE GO)

## Disclaimer
This document outlines a **future** pilot design. The repository is currently **NOT APPROVED** for live credentials or network access. This design assumes all operator prerequisites have been satisfied.

## Pilot Target
- **Platform:** Telegram
- **Environment:** Dedicated Private Staging Channel (invite-only)

## Cadence and Limits
- **Maximum Output:** 1 post per day.
- **Provider Access:** Limited to 1 LLM model call per execution sequence.

## Security Constraints
- **Approval:** Manual, explicit operator CLI approval is required for **every single post**.
- **Autonomy:** No autonomous replies, no DMs, no comments.
- **Content:** No market calls, no personalized financial advice, no live current-event claims without an explicitly provided local source bundle.

## Operational Lifecycle
1. **Kill Switch Check:** The operator manually clears the kill switch daily.
2. **Bundle Ingestion:** System reads a safe offline source bundle.
3. **Provider Generation:** System contacts LLM provider with the source bundle and strict schema.
4. **Policy Engine Check:** Deterministic gating filters any unsafe phrasing.
5. **Approval Queue:** Content is held in the queue.
6. **Operator Review:** Operator reads the exact payload and types `publish_now`.
7. **Adapter Execution:** System sends payload to the private Telegram channel.
8. **Audit Logging:** Every stage is recorded in the append-only audit log.
9. **Rollback:** If required, operator uses the manual delete method (to be built).

## STOP Conditions
The pilot must be immediately aborted and the kill switch activated if:
- A secret leaks in any log.
- An unapproved post goes live.
- The system attempts to post more than the configured rate limit.
- The LLM provider exhibits significant hallucination or safety violations.
- A platform API change breaks the staging contract.
