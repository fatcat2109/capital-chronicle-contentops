# Telegram Supervised Live Runbook (Second Private Sandbox)

## Preparation Checklist
1. **Queue Item Ready**: Ensure exactly one supervised item is queued and structurally valid.
2. **One-Shot Packet**: Ensure the policy gate allows execution to the designated `TEST_TELEGRAM_CHANNEL`.
3. **Precheck Layer Valid**: Must report `live_attempt_count == 0` and `wrapper_script_requested == False`.

## No-Wrapper Policy
Operators MUST NOT use scripts like `run_with_env.py` to inject variables. All environment variables must be injected directly into the shell before execution.

## Operator Environment Setup
If you have an untracked `.env` file, the system will explicitly report its presence (`OPERATOR_OWNED_UNTRACKED_SECRET_FILE_PRESENT`) but will deliberately ignore its contents. You MUST load variables into the shell process manually.

In PowerShell:
```powershell
# Set variables
$env:TELEGRAM_BOT_TOKEN="your_actual_token"
$env:TEST_TELEGRAM_CHANNEL="-100..."

# Verify presence WITHOUT printing values
Write-Output "Token present: $([bool]$env:TELEGRAM_BOT_TOKEN)"
Write-Output "Channel present: $([bool]$env:TEST_TELEGRAM_CHANNEL)"
```

## Explicit Next-Task Authorization
The next live GO phrase must be explicitly provided by the user in the future task prompt (e.g., `TASK_CONTENTOPS_0094`). It cannot be implied from this runbook.

## Zero-Retry Policy
Only **ONE** execution command is permitted.
If the execution fails (e.g., 404, auth error), you MUST STOP.
* No automatic retries.
* No changing `.env` variables and running the same command again.
* You must generate a new operator explicit decision and reset the attempt count.

## Execution Command
(Only run after exact phrase authorization is received in future task)
```powershell
python -m live_contentops.cli telegram-live-pilot-execute
```

## Evidence Redaction Checklist
Before generating the final evidence packet, ensure:
- The actual bot token is never printed, staged, or committed.
- The actual private channel ID is replaced with `-100<REDACTED>`.
- Any raw JSON response from Telegram containing `id`, `chat`, `from`, or `sender_chat` IDs is redacted.

## Manual Rollback & Cleanup
If the execution succeeds but needs rollback:
1. Note the `msg_id` from the redacted output.
2. The operator must manually delete the message in the Telegram client.
3. Remove the token from the shell:
```powershell
Remove-Item Env:\TELEGRAM_BOT_TOKEN
Remove-Item Env:\TEST_TELEGRAM_CHANNEL
```
