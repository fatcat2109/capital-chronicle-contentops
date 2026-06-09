# Telegram Live Precheck Hardening

As of 0092, local Telegram supervised live-pilots must pass an exact pre-flight check before attempting to hit the network or the adapter gate.

## Key Rules

1. **No Wrapper Scripts**: Operator environments must be populated via standard shell mechanisms (e.g. `$env:TELEGRAM_BOT_TOKEN="xxx"`). Using ad-hoc python wrappers to inject `.env` variables at runtime is strictly forbidden to prevent accidental execution masking.
2. **Process Environment Only**: Live commands read `TELEGRAM_BOT_TOKEN` and `TEST_TELEGRAM_CHANNEL` from the current shell environment only.
3. **No `.env` Content Reads**: The python codebase has no `python-dotenv` or similar secret parsing capabilities.
4. **Exact Operator GO**: The exact approval phrase is required and tested locally before reaching network scope.
5. **Zero Retry Loop**: `live_attempt_count` must be zero to prevent "blind retry" scenarios. Any failure requires manual reset and explicit re-authorization.
6. **Untracked Operator State**: If an operator creates an `.env` file locally, it is classified strictly as `OPERATOR_OWNED_UNTRACKED_SECRET_FILE_PRESENT`. The system will acknowledge its presence in logs but will deliberately refuse to read its contents.
