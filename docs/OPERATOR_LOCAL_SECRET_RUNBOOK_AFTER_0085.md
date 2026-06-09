# Operator Local Secret Runbook
**Status**: ACTIVE
**Purpose**: Define the secure boundary for operator secret injection during supervised live pilots.

## 1. The Secret Model
The `cc-live-contentops` repository is explicitly engineered to be fail-closed and stateless concerning secrets. 
* The repo contains code, tests, policies, and placeholders ONLY.
* Real secrets MUST live strictly OUTSIDE the repo.
* The operator loads secrets into the process environment ONLY for a scoped live task.
* The AI/IDE MUST NOT read secret files, nor paste real tokens into docs or logs.

## 2. External Secret Management
We recommend storing your actual secrets in an external `.env` file that is completely separate from this repository.
**Safe External Secret File Path Example:**
`A:\Capital Chronicle\secrets\cc-live-contentops.telegram.env`

**Content Structure (with placeholders):**
```env
TELEGRAM_BOT_TOKEN=REPLACE_WITH_REAL_TOKEN_OUTSIDE_REPO
TEST_TELEGRAM_CHANNEL=REPLACE_WITH_PRIVATE_SANDBOX_CHANNEL_ID_OUTSIDE_REPO
```

## 3. Operator Execution Process (PowerShell)
To execute an approved supervised live pilot, the operator must manually parse the external secret file into their local process environment and run the command.

```powershell
# 1. CD into the repository
cd "A:\Capital Chronicle\tools\cc-live-contentops"

# 2. Parse the external secret file into the process environment
# (Assuming you have a script or manually source it. Manual assignment is safest for single keys)
$env:TELEGRAM_BOT_TOKEN="real_token_from_your_vault"
$env:TEST_TELEGRAM_CHANNEL="-100xxxxxxx"

# 3. Run the approved CLI command
python -m live_contentops.cli telegram-live-pilot-execute
```
> [!WARNING]
> The AI audit tasks must NEVER run the `telegram-live-pilot-execute` command. Doing so violates the core boundary.

## 4. Verification Commands
Operators should periodically verify that no secrets have leaked into the repository.
* `git status --short` (Ensure no `.env` is tracked, except `.env.example`).
* `git ls-files | findstr /I "env token secret credential key"` (Check tracked files).
* `git grep "bot[0-9]\+:"` (Scan for Telegram bot tokens).
* `git log -p | findstr ".env"` (Check if `.env` was ever committed).

If a token is found, stop immediately and initiate token rotation.

## 5. Token Rotation Guidance
* **Immediate Rotation**: Rotate immediately if a token was committed to git, pasted into a markdown document, or exposed to the IDE logs.
* **No Rotation Required**: If only placeholder names (like `REPLACE_WITH_REAL_TOKEN_OUTSIDE_REPO`) are committed, no rotation is needed.
* **Private IDs**: Private channel IDs should be redacted from docs using `[REDACTED_TELEGRAM_PRIVATE_SANDBOX_CHANNEL_ID]`.

## 6. Future Automation Stance
* Approved live tasks may read process environment variables **only when explicitly scoped** (e.g., the supervised pilot).
* There is **no automatic reading** of `.env` files by default in the execution flow.
* **No public channel posting** is permitted during the pilot phase.
* **No autonomous posting, scheduling, replies, or DMs** are permitted.
* **No metrics scraping/fetching** is allowed unless separately approved.
