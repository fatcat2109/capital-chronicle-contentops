# Discord Webhook Official Documentation Evidence — Preflight Phase

## Inspection Details
* **Source Title**: Discord Developer Portal — Webhooks Documentation & Resources
* **Source URL**: https://discord.com/developers/docs/resources/webhook
* **Date Inspected**: 2026-07-02
* **Verify Action**: Supervised preflight check only. No live connections initiated to the webhook endpoint.

## Payload Shape & Header Requirements
Discord Webhook invocations expect an HTTP POST request:
* **Headers**: `Content-Type: application/json`
* **JSON Properties**:
  * `content` (string, max 2000 chars): Message body text.
  * `allowed_mentions` (object): Configures user/role ping rules.

## Allowlist Constraints
* **Allowed Host**: `discord.com`
* **Allowed Method**: `POST`
* **Allowed Path Shape**: `/api/webhooks/{webhook.id}/{webhook.token}`
