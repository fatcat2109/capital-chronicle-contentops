# Social Automation Source Manifest (0174EA)

Task origin: TASK_CONTENTOPS_0174EA_SOCIAL_AUTOMATION_RESEARCH_AND_ARCHITECTURE_CONTEXT_PACK_V0

> [!IMPORTANT]
> The operator-supplied research is **advisory context, not runtime authority**. GitHub repo docs and official platform docs must be re-checked from primary sources before any implementation. Ephemeral ChatGPT citation IDs (e.g. `turnNNviewN`) from the pasted research are **not** persistent citations and were deliberately not preserved as repo authority.

## Open-Source Reference Repositories
| Project | URL |
|---|---|
| Postiz | https://github.com/gitroomhq/postiz-app |
| autopost-social-media | https://github.com/fawaziwalewa/autopost-social-media |
| Free-AI-Social-Media-Scheduler | https://github.com/Anil-matcha/Free-AI-Social-Media-Scheduler |
| laravel-social-auto-post | https://github.com/HamzaHassanM/laravel-social-auto-post |
| owlstack-laravel | https://github.com/owlstacks/owlstack-laravel |

## Official Platform Docs (stable entry URLs — re-verify before implementation)
| Platform | Entry doc URL | Verification status in source research |
|---|---|---|
| X | https://docs.x.com/ | Cited (pay-per-use writes, OAuth 2.0 user context). Re-verify pricing/limits. |
| LinkedIn | https://learn.microsoft.com/en-us/linkedin/ | Cited (`w_member_social`, `/rest/posts`, review tiers). Re-verify scopes/review. |
| Telegram | https://core.telegram.org/bots/api | Cited (`sendMessage`, `allow_paid_broadcast`). Generally stable. |
| TikTok | https://developers.tiktok.com/doc/content-posting-api-get-started/ | Cited (scope `video.publish`, audit, private-only). Re-verify audit rules. |
| YouTube | https://developers.google.com/youtube/v3/docs/videos/insert | Cited (`youtube.upload`, unverified-project private). Re-verify quota/audit. |
| Bluesky | https://docs.bsky.app/ | Cited (session JWTs, `app.bsky.feed.post`, blob upload). Re-verify. |
| Mastodon | https://docs.joinmastodon.org/methods/statuses/ | Cited (`POST /api/v1/statuses`, `Idempotency-Key`). Generally stable. |
| Discord | https://discord.com/developers/docs/resources/webhook | Cited (webhook posting, rate-limit headers). Re-verify rate rules. |
| Reddit | https://www.reddit.com/dev/api | Cited (exact redirect URI match, `/api/submit`, `/api/v1/subreddit/post_requirements`). Re-verify. |

## Unresolved / Gated Items (NOT verified)
> [!WARNING]
> The following were blocked, rate-limited, or unfound in the source research session. Do not represent them as officially verified or implementation-ready.

| Item | Status in source research | Required action |
|---|---|---|
| Facebook (Meta) docs | "Not Logged In" — not fully readable | Re-check from an authenticated Meta developer session |
| Instagram (Meta) docs | "Not Logged In" — not fully readable | Re-check from an authenticated Meta developer session |
| Threads docs | HTTP 429 Too Many Requests on fetch | Re-fetch later; do not assume rules from memory |
| Substack publishing API | No public official developer/publishing API source found | Treat as manual fallback until an official supported API is confirmed |
| Medium API | Historically deprecated / archived per general knowledge | Re-verify support status before any integration |
| Postiz write-path retry policy | Temporal in stack implies orchestration retries, but write-path retry not verified in source | Verify in source before modeling on it |

## Source Authority Note
- Pasted operator research (Vietnamese summary + "Social Media Automation Research Report") is advisory only.
- All GitHub and official-platform claims must be re-confirmed from primary sources at implementation time.
- No ephemeral ChatGPT `turn...view...` IDs are persistent citations; they were stripped and replaced by the stable URLs above with explicit caveats.
- Where official docs were gated/429/unfound, this manifest states that plainly rather than implying verification.
