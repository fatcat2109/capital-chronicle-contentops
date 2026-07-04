# 0174CV X Official-Docs Account-Binding Requirements

Strictly local, official-doc-grounded, requirements-only X packet. No X API call, no OAuth, no token exchange, no developer-portal login, no account binding, no posting.

## Inherited posture

- Inherits the conservative 0174CT/0174CU posture: live posting is `blocked_until_new_explicit_task_and_operator_go`.
- This task only deepens the X requirements; it does not enable any live path.

## Endpoint + auth (symbolic)

- Endpoint family: `x.api.v2.posts.manage_posts.create_post` (expected `POST /2/tweets`).
- Create Post also performs edit via `edit_options`; edit is forbidden until separately scoped.
- Auth model: OAuth 2.0 user context / user access token, not initiated now.

## Official docs inspected

- Create or Edit Post (`docs.x.com/x-api/posts/create-post`) -- accessible.
- Authentication / OAuth 2.0 user context (`docs.x.com/resources/fundamentals/authentication`) -- accessible.
- Developer Portal access tiers (`developer.x.com/en/portal`) -- gated (login required, not performed) -> blocker.

## Text-only dry-run payload contract

- Allowed: `text` (required), `made_with_ai` (optional boolean only if later needed).
- Forbidden until scoped: `card_uri`, `community_id`, `direct_message_deep_link`, `edit_options`, `for_super_followers_only`, `geo`, `media`, `nullcast`, `paid_partnership`, `poll`, `quote_tweet_id`, `reply`, `reply_settings`, `share_with_followers`, and any raw post/user/community/place/media ids.

## Forbidden adjacent feature families

edit post, delete post, repost, quote, bookmarks, likes, replies, DMs, media upload, communities, trends/search/scraping, webhooks/activity subscriptions, metrics/usage fetch.

## What this did NOT do

No X (or Telegram/LinkedIn) API call. No OAuth flow, token exchange, or developer-portal login. No account binding, no credential or env read, no credential-entry schema. No post/edit/delete/repost/quote/bookmark/like/reply/DM. No metrics fetch, webhook, or scraping. The module never browses docs at runtime; docs reading was an Antigravity/operator activity before writing symbolic packet data.

## Next

Recommended next task: `TASK_CONTENTOPS_0174CW_X_OAUTH_USER_CONTEXT_DESIGN_AND_REDIRECTION_POLICY_NO_TOKEN_NO_LIVE_V0`.
