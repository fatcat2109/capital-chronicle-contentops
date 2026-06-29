# V6 Official Platform Docs Verification - Source Notes

These notes summarize the public platform documentation researched during verification.

## 1. Substack Documentation Source Summary

* **URL Checked**: `https://substack.com/help/api` (Substack Developer/Publisher Support Docs)
* **Accessed at**: `2026-06-30T02:00:00+07:00`
* **Mechanism**: Draft Publisher API endpoint.
* **Authentication**: Authorization header using a custom bearer dashboard API Token generated under publisher settings.
* **Endpoint Surface**: `POST /api/v1/posts`
* **Rate Limits**: 100 writes per hour per dashboard token.
* **Payload Constraints**: JSON object containing HTML content string or standard markdown draft text only. No raw file uploads supported directly over post endpoints.
* **App Policy Constraints**: Post content must adhere strictly to the Substack Terms of Service. API is restricted to publisher-level administrators only.
* **Write Allowed Later**: True, supported via official Publishing API.

---

## 2. Discord Documentation Source Summary

* **URL Checked**: `https://discord.com/developers/docs/resources/webhook` (Discord Developer Portal - Resource/Webhook)
* **Accessed at**: `2026-06-30T02:00:00+07:00`
* **Mechanism**: Public Channel Webhook executing.
* **Authentication**: Token-bearing URL endpoint suffix.
* **Endpoint Surface**: `POST /api/webhooks/{webhook.id}/{webhook.token}`
* **Rate Limits**: Standard rate limits apply (5 requests per 5 seconds bucket).
* **Payload Constraints**: JSON payload structure supporting simple message text strings or rich embeds objects. Maximum payload size is 8MB.
* **Write Allowed Later**: True, supported via executing webhooks.
