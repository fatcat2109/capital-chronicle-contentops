# V6 Live / Env Scope Contract

Any task that uses environment variables (`.env`), live endpoints, webhooks, provider APIs, or browser operators must define the following scope contract fields in its prompt objective.

## Required Scope Fields

1. **Task Label**: The exact `TASK_CONTENTOPS_V6_*` string on line one.
2. **Platform / Family**: The specific target platform or API service family.
3. **Action Class**: The task classification from the `task_classification_matrix.json`.
4. **Credential Key Names Only**: List of the environment variable key names needed (e.g. `DISCORD_BOT_TOKEN`, `SUBSTACK_EMAIL`). Never output or check in actual values.
5. **Secret Handling**: Strict instructions for redacting and handling credential values.
6. **Host/Path/Method Allowlist**: Clear list of permitted endpoints and methods (e.g. POST requests only to `https://discord.com/api/webhooks/`).
7. **Request Count / Budget**: Maximum number of network calls or API requests allowed during execution.
8. **Timeout**: The network request or CDP browser step timeout.
9. **Retry Policy**: Maximum retries and backoff logic.
10. **Payload Hash Requirement**: If performing a live write, the payload must be pre-hashed and confirmed before dispatch.
11. **Destination Binding**: Verified channel ID or webhook pointer mapping.
12. **Approval Condition**: Conditions under which the operator (Jim) must approve the action.
13. **Redacted Audit Fields**: List of fields to be written to the final public audit log.
14. **Stop Conditions**: Specific events that trigger fail-safe termination.
15. **Rollback / Manual Fallback**: Steps to reverse or manually address failures.
