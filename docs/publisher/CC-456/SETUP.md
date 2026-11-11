# CC-456: prepared actions for Jim

No keys were entered or displayed by this run. The real runner reached its
first API request boundary and returned `X_API_KEYS_NOT_SET`, without sending
a network request or spending credit. CC-455 remains the manual reply route.

1. **Submit developer onboarding as @Capitalnicle.** The existing browser task
   leaves [the developer console](https://console.x.com/onboarding) open. Account
   name: `Capital Chronicle Mention Replies`. Paste the use-case text below into
   its description. Create the app with Read and Write permission and user-context
   OAuth 1.0a access for that same account. Request X's written AI-reply approval;
   the returned approval reference is the runner's `--x-approval-ref` argument.

   ```text
   Capital Chronicle requests prior written approval for an AI-powered reply bot on @Capitalnicle. It reads the account's mentions through X's official API and generates English, source-checked replies only to posts that directly mention @Capitalnicle or verifiably quote its own posts. It never sends unsolicited replies, likes, follows, or direct messages, and never posts replies through browser automation. Each reply adds a dated fact from our own public analysis or a permitted cited source, stays within 280 characters, and offers analysis rather than financial advice. We send at most one automated reply per interaction, honor STOP and other explicit opt-out requests, suppress already answered or uncertain interactions, and retain exact public readbacks. Polling, when enabled by the owner, is every 15 minutes; local requests reserve a maximum of USD 0.50 per day in prepaid credit. We do not sell or redistribute raw X data, use it for model training, or enable automatic credit recharge.
   ```

2. **Buy the smallest available prepaid amount after onboarding.** The current
   [official price page](https://docs.x.com/x-api/getting-started/pricing) states
   that there is no minimum spend, but publishes no minimum credit-purchase
   amount. The console currently stops at developer onboarding, before billing.
   **USD 1 is the proposed initial purchase, not a verified checkout minimum.**
   Select USD 1 if accepted; otherwise the smallest amount and its displayed price
   must be read at checkout. Leave auto-recharge off. No purchase, saved payment
   method or account setting was changed by the agent. An exact smallest price
   cannot be supplied truthfully before that person-only setup step.

3. **Run this command yourself to store the four values, with input hidden.**
   The script prompts for the app API key and secret, then its own-account access
   token and secret. It writes only to Windows Credential Manager and prints
   the stored names. Do not paste a key into this chat, command arguments or files.

   ```powershell
   python "A:\Capital Chronicle\ContentOps\scripts\set_x_api_keys.py"
   ```

   Targets: `CapitalChronicle/X_API_KEY`, `CapitalChronicle/X_API_KEY_SECRET`,
   `CapitalChronicle/X_ACCESS_TOKEN`, `CapitalChronicle/X_ACCESS_TOKEN_SECRET`.
   `--name X_API_KEY` (or any one of the other names) updates only that value.

4. **The Automated label stays off.** Decision 122 records X's label/operator
   requirement and the conflict with decision 109 item 5. Only Jim changes that
   profile setting; this item neither enables it nor invents platform compliance.

The installed one-shot commands below are ready for the existing editorial route.
They add no schedule. No Claude or paid model API is called. `api-poll` returns
the exact native request to author; `api-publish` consumes that request and its
real response, refreshes Jim's pack, and calls the sole publication coordinator.

```powershell
python "A:\Capital Chronicle\ContentOps\scripts\run_sourced_replies.py" api-poll --store "A:\Capital Chronicle\Runtime\ContentOps\contentops_daily_app_v1.sqlite3"
python "A:\Capital Chronicle\ContentOps\scripts\run_sourced_replies.py" api-publish --store "A:\Capital Chronicle\Runtime\ContentOps\contentops_daily_app_v1.sqlite3" --request "<returned request_path>" --response "<native response.json>" --mentions-feed "<returned mentions_feed_path>" --x-approval-ref "<X written approval reference>"
```

For 96 polls per day over 30 days, empty mentions responses cost USD 0 in returned
post resources. Sending 2,880 empty requests does not itself cost USD 14.40. The implemented daily
identity verification adds a conservative USD 0.30 per month. The held feed showed
zero mentions at the check; that is not an API census of the whole account.
At one new mention per day, polling and its author expansion plus daily identity
reads are about USD 0.63/month if Owned Reads apply, or USD 0.75 at ordinary rates.
Replies, target checks and reply readbacks are additional. No cadence was enabled.

The [pricing record](pricing-and-rules.json) gives the assumptions. X bills per
returned resource: USD 0.001 for qualifying own-account mentions, USD 0.005 for
ordinary posts, USD 0.010 per user, USD 0.010 per summoned write, and USD 0.200 for
a write with a URL. For the local USD 0.50 cap, the code assumes ordinary read
rates, no daily deduplication, and a USD 0.015 write ceiling without a URL. Each
run stores estimated cost, its conservative upper bound and unresolved requests;
an invoice charge remains unknown until the console supplies it.
