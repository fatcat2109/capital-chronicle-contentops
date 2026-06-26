# Discord Live Pilot Operator Brief

- Task label: `TASK_CONTENTOPS_V6_DISCORD_LIVE_PILOT_AUTHORIZATION_GATE_AND_OFFICIAL_DOCS_LOCK_V0`
- Selected dispatch candidate ID: `discord_candidate_discord_outbox_discord_dryrun_announcement_001`
- Payload hash: `b166aebf1f53956f04ffa5122d6d065fc09e4f7953ec816e1b0b66a01be9d17d`
- Payload type: `announcement`
- Target name: `announcements`
- Destination binding ID: `discord_announcements_capital_chronicle_01`
- Credential handle ID: `discord_announcements_webhook_01`
- Env key name only: `DISCORD_ANNOUNCEMENTS_WEBHOOK_URL`
- Endpoint family: `discord_execute_webhook`
- Method: `POST`
- Host allowlist: `discord.com`
- Path template only: `/api/webhooks/{webhook.id}/{webhook.token}`
- Request budget: `1`
- Retries: `0`
- Timeout seconds: `10`
- wait=false
- current_task_dispatchable=false
- live_write_allowed_now=false
- webhook_url_hydration_allowed_now=false
- network_dispatch_allowed_now=false
- Exact future authorization phrase: `AUTHORIZE_DISCORD_WEBHOOK_TEST_SEND_NOW`
- Kill switch env key: `CONTENTOPS_LIVE_DISPATCH_KILL_SWITCH`
- Kill switch required value: `ALLOW_DISCORD_TEST_SEND`
- no live send happened

## Meaning

This packet prepares a future live authorization task only. It does not authorize dispatch now and does not load any webhook URL.
