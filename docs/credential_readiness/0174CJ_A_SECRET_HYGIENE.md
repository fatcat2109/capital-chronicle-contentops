# 0174CJ_A — Secret Hygiene: Untrack Local Env and Harden .gitignore Guard

**Task:** `TASK_CONTENTOPS_0174CJ_A_SECRET_HYGIENE_UNTRACK_ENV_AND_GITIGNORE_GUARD_V0`

## Summary

The repository previously tracked a local `.env` file in git, and the
`.gitignore` did not cover environment/secret files. Worse, `.gitignore` was
stored as UTF-16LE, which git parses unreliably, so several intended ignore
rules were not consistently applied.

This task fixes repo secret hygiene **before** any live Telegram API validation
(0174CK). No live API call is made here.

## What changed

1. **Untracked `.env` from the git index** using `git rm --cached .env`.
   - The local working-copy file was **preserved** (not deleted from disk).
   - `.env` is now an untracked, ignored, local-only file.

2. **Rewrote `.gitignore` as clean UTF-8** (it was UTF-16LE before) and added
   explicit secret/log guard patterns:
   - `.env`, `.env.local`, `.env.*` (with an allow-exception for `*.env.example`)
   - `*.pem`, `*.key`, `secrets.json`, `credentials.json`
   - `*.log`, `logs/`
   - Preserved the prior `__pycache__/` and `outputs/` rules.

3. **Added a static guard test** (`tests/test_env_secret_hygiene.py`) that fails
   if `.env` / `.env.local` are tracked again, and asserts the ignore patterns
   are present in `.gitignore`.

## Safety guarantees

> [!IMPORTANT]
> Raw `.env` contents were **never** opened, read, printed, `cat`-ed, `grep`-ed,
> screenshotted, or otherwise inspected during this task. Only git index/ignore
> *state* (tracked vs ignored) was queried — never file contents.

- `.env` remains **local only**. It is not staged or committed by this task.
- No token was rotated by the agent. No Telegram API was called.

## Operator action required (rotation)

> [!CAUTION]
> If real secrets were **ever** committed to git history (this `.env` was tracked
> prior to this task), untracking does **not** remove them from past history. The
> operator must treat any previously committed credentials as **potentially
> exposed** and rotate them manually, outside the repo:
> - Rotate the Telegram bot token via BotFather (revoke + reissue).
> - Rotate any other secrets that were present in the tracked `.env`.
> - Optionally scrub git history (e.g. `git filter-repo`) if the remote must be
>   purged. This is an operator decision and is out of scope for this task.

## Live gate status

Live Telegram API validation (`0174CK`) remains **blocked** until the operator
explicitly confirms either:
- secrets have been rotated, **or**
- the operator formally accepts the residual risk with a documented rationale.

## Next task

`TASK_CONTENTOPS_0174CK_TELEGRAM_LIVE_GATE_READ_ONLY_BOT_ID_VALIDATION_V0`
(bounded, read-only `getMe` identity validation — only after rotation/acceptance).
