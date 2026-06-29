# V6 Official Platform Docs Verification - Source Notes

These notes summarize the public platform documentation researched during verification.

## 1. Substack Documentation Source Summary

* **URL Checked**: `https://substack.com/help/api` (Substack Developer/Publisher Support Docs)
* **Status**: **UNVERIFIED / BLOCKED**
* **Verification Note**: 
  > [!WARNING]
  > Substack official API publishing documentation not verified from official public docs; manual/browser fallback or later operator-provided official source required.
  > Claims of `official_api_supported_for_required_action` using draft API endpoints, bearer tokens, or specific request budgets are not verifiably supported by current official public Substack documentation.
* **Mechanism**: Unverified.
* **Authentication**: Unverified.
* **Endpoint Surface**: Unverified.
* **Rate Limits**: Unverified.
* **Write Allowed Later**: False.

---

## 2. Discord Documentation Source Summary

* **URL Checked**: `https://discord.com/developers/docs/resources/webhook` (Discord Developer Portal - Resource/Webhook)
* **Status**: **VERIFIED**
* **Mechanism**: Public Channel Webhook executing.
* **Authentication**: Token-bearing URL endpoint suffix.
* **Endpoint Surface**: `POST /api/webhooks/{webhook.id}/{webhook.token}`
* **Rate Limits**: Standard rate limits apply (5 requests per 5 seconds bucket).
* **Payload Constraints**: JSON payload structure supporting simple message text strings or rich embeds objects. Maximum payload size is 8MB.
* **Write Allowed Later**: True, supported via executing webhooks.
