# Discord Webhook Official Documentation Evidence

## Inspect Details
* **Source Title**: Discord Developer Portal — Webhooks Documentation
* **Source URL**: https://discord.com/developers/docs/resources/webhook
* **Date Inspected**: 2026-07-02
* **Scope Check**: Read-only verification of webhook structures. Zero network requests made to live discord webhook endpoints.

## Endpoint allowlist
* **Host**: `discord.com`
* **Method**: `POST`
* **Path Shape**: `/api/webhooks/{webhook.id}/{webhook.token}`

## Webhook Payload Shape
A Discord Webhook execution payload is sent as `application/json` content, supporting standard text messages and rich embeds:

```json
{
  "content": "Message body text",
  "username": "Optional Override Name",
  "avatar_url": "https://example.com/avatar.png",
  "tts": false,
  "embeds": [
    {
      "title": "Rich Embed Title",
      "description": "Embed description text",
      "color": 3447003
    }
  ]
}
```

## Safety Invariant
The Webhook URL token (`{webhook.token}`) acts as a shared secret. It must never be committed to public/private repositories, logged in cleartext, or printed to the console output.
