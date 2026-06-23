# Social Credentials Manual Setup Matrix

No values belong in this document.

| Platform | Env key | Priority | Notes |
|---|---|---:|---|
| Telegram | `TELEGRAM_BOT_TOKEN` | P0 | BotFather token, local only |
| Telegram | `TELEGRAM_CHANNEL_ID` | P0 | Channel id or handle |
| Telegram | `TELEGRAM_OPERATOR_CHAT_ID` | P1 | Operator test chat id |
| X | `X_CLIENT_ID` | P0 | OAuth app client id |
| X | `X_CLIENT_SECRET` | P0 | OAuth app secret |
| X | `X_ACCESS_TOKEN` | P1 | Local token only |
| X | `X_REFRESH_TOKEN` | P1 | Local token only |
| X | `X_USER_ID` | P1 | Account id |
| X | `X_ACCESS_TIER_CLASS` | P2 | Tier label only |
| LinkedIn | `LINKEDIN_CLIENT_ID` | P0 | App client id |
| LinkedIn | `LINKEDIN_CLIENT_SECRET` | P0 | App secret |
| LinkedIn | `LINKEDIN_ACCESS_TOKEN` | P1 | Local token only |
| LinkedIn | `LINKEDIN_MEMBER_URN` | P1 | Member URN |
| LinkedIn | `LINKEDIN_ORGANIZATION_URN` | P2 | Organization URN |
| Meta | `META_APP_ID` | P0 | Meta app id |
| Meta | `META_APP_SECRET` | P0 | Meta app secret |
| Meta | `META_ACCESS_TOKEN` | P1 | Local token only |
| Meta | `FACEBOOK_PAGE_ID` | P1 | Page id |
| Meta | `FACEBOOK_PAGE_ACCESS_TOKEN` | P1 | Page token only |
| Meta | `INSTAGRAM_BUSINESS_ACCOUNT_ID` | P2 | Instagram business account id |
| Meta | `THREADS_USER_ID` | P2 | Threads user id |
| TikTok | `TIKTOK_CLIENT_KEY` | P0 | App key |
| TikTok | `TIKTOK_CLIENT_SECRET` | P0 | App secret |
| TikTok | `TIKTOK_ACCESS_TOKEN` | P1 | Local token only |
| TikTok | `TIKTOK_REFRESH_TOKEN` | P1 | Local token only |
| TikTok | `TIKTOK_OPEN_ID` | P1 | Open id |
| YouTube | `YOUTUBE_CLIENT_ID` | P0 | OAuth client id |
| YouTube | `YOUTUBE_CLIENT_SECRET` | P0 | OAuth client secret |
| YouTube | `YOUTUBE_REFRESH_TOKEN` | P1 | Local token only |
| YouTube | `YOUTUBE_CHANNEL_ID` | P1 | Channel id |
| YouTube | `YOUTUBE_CLIENT_SECRETS_JSON_PATH` | P0 | Local path only, never commit file |
| Substack | `SUBSTACK_PUBLICATION_URL` | P2 | Publication URL |
| Substack | `SUBSTACK_EMAIL_OR_ACCOUNT_HINT` | P2 | Account hint, no password |

Run:

```powershell
python -m live_contentops.social_credential_setup_workbench inventory --repo-root . --json
```

Process env is not checked unless `--include-process-env` is passed.
