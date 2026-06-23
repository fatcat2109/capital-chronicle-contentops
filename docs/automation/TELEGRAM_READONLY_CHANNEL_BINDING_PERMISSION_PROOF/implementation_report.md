# Telegram Read-Only Channel Binding Permission Proof R1 Repair

Task: `TASK_CONTENTOPS_TELEGRAM_READONLY_CHANNEL_BINDING_PERMISSION_PROOF_V0`
Repair task: `TASK_CONTENTOPS_TELEGRAM_READONLY_CHANNEL_BINDING_PERMISSION_PROOF_R1_REPAIR_PATCH_V0`

## Result

- Result classification: `BLOCKED_GETME_FAILED`
- Request budget used: `1` of `3`
- Live read-only request performed: `True`
- Live write allowed now: `False`
- Send permission unlocked now: `False`

## Stop Conditions

- `BLOCKED_GETME_FAILED`

## Credential Policy

- Credential key names checked only: `TELEGRAM_BOT_TOKEN, TELEGRAM_BOT_API_TOKEN, CONTENTOPS_TELEGRAM_BOT_TOKEN`
- Channel key names checked only: `TELEGRAM_CHANNEL_ID, TELEGRAM_TARGET_CHANNEL_ID, TELEGRAM_CHAT_ID, CONTENTOPS_TELEGRAM_CHANNEL_ID_OR_HANDLE`
- Selected credential key name: `TELEGRAM_BOT_TOKEN`
- Selected channel key name: `TELEGRAM_CHAT_ID`
- No token value, length, prefix, suffix, digest, hash, raw URL, raw header, raw response, raw channel ID, or raw user ID persisted.

## CLI Compatibility

- `live_contentops/cli.py` hook retained as compatibility-only.
- Default CLI-style invocation blocks before network.
- Live read-only calls require explicit operator GO and execute flags.

## Candidate Packets

- Account binding candidate never enables live write, dispatch, public posting, or live dispatch validity.
- Live gate candidate never enables gate pass, live write, or live dispatch validity.
