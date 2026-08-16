# Platform Automation Eligibility

Official-document re-verification date: `2026-08-16`

| Surface | Official transport | Server-side use for this owner model | Per-post creator consent | Review/audit | Required account | Timed captions | Localized metadata | Alternate audio | Status/readback | Current classification | Exact blocker |
|---|---|---|---|---|---|---|---|---|---|---|---|
| YouTube normal video | Yes: `videos.insert`, `videos.update`, captions, `videos.list` | Yes, after account/project authorization | OAuth grant; no separate provider-mandated interactive choice was found per post | API project audit needed to lift applicable private-only restriction | Authorized YouTube channel; long-upload verification for >15 minutes | Yes | Yes, BCP-47 `localizations` | No verified public Data API uploader; Studio/eligible-account UI only | Strong owner readback for upload/privacy/processing/metadata/captions | `APP_REVIEW_REQUIRED` | Audited project, authorized channel, credentials and one exact live canary are absent |
| YouTube Shorts | Yes: normal `videos.insert`; no separate Shorts endpoint/flag | Yes, after account/project authorization | Same as normal video | Same audit restriction | Authorized standard channel | Yes | Yes | Same Studio/account-gated gap | Strong video readback; Shorts-feed classification has no verified Data API flag | `APP_REVIEW_REQUIRED` | Same setup plus later product-level Shorts classification readback |
| TikTok Direct Post | Technically yes | **No for the current autonomous internal utility model** | **Yes**: current creator identity/privacy/interaction UI, editable metadata and express consent | App approval and audit for public visibility | Authorized TikTok creator | No verified sidecar transport | No | No | Publish status and public post ID when moderation makes it public | `PRODUCT_POLICY_BLOCKED` | Official sharing guidelines reject a utility used to upload to accounts managed by the developer/team; classification is `OFFICIAL_API_NOT_ELIGIBLE_FOR_THIS_INTERNAL_AUTOMATION_MODEL` |
| Instagram Reel | Yes: container, processing, `media_publish`, media readback | Yes for an authorized professional account | OAuth/app authorization; no separate per-post interactive consent requirement found | Standard Access for owned/managed app-added accounts; Advanced Access for other accounts | Instagram professional account | No verified sidecar transport | No | No | Container status plus published media ID/product type/permalink | `ACCOUNT_SETUP_REQUIRED` | Login variant, professional identity, access level, token, Graph version and canary not configured |
| Instagram Story | Yes: `STORIES` container and `media_publish` | Yes for an authorized eligible account | Same as Instagram Reel | Same access model | Instagram Business account in reviewed Facebook Login contract | No | No ordinary Story metadata contract | No | Container and published media ID available; exact Story post-readback/duration needs live re-verification | `ACCOUNT_SETUP_REQUIRED` | Business-account eligibility, Graph version and exact Story duration/readback preflight |
| Facebook Page Reel | Yes: initialize, `rupload`, status, finish/publish | Yes for an authorized Page after permission/access setup | Page authorization; no separate provider-mandated interactive choice found per post | App Review/Advanced Access depends on Page ownership/use model | Managed Facebook Page | No verified Reels sidecar transport | No | No | `video_id`, phase status and Video/Page readback | `ACCOUNT_SETUP_REQUIRED` | Page access, permissions, current Graph version and canary not configured |

## Non-collapsed readiness truth

- YouTube is technically automation-capable but remains `APP_REVIEW_REQUIRED`, not ready.
- Instagram and Facebook are technically automation-capable but remain
  `ACCOUNT_SETUP_REQUIRED`; conditional app review/access gates are recorded separately.
- TikTok is not merely waiting for credentials or audit. The current autonomous internal product
  model is `PRODUCT_POLICY_BLOCKED`, and the adapter refuses a ready capability state.
- No surface has live-write authority in this task.

## Official references

- YouTube videos: <https://developers.google.com/youtube/v3/docs/videos>
- YouTube `videos.insert`: <https://developers.google.com/youtube/v3/docs/videos/insert>
- YouTube `videos.update`: <https://developers.google.com/youtube/v3/docs/videos/update>
- YouTube `videos.list`: <https://developers.google.com/youtube/v3/docs/videos/list>
- YouTube captions: <https://developers.google.com/youtube/v3/docs/captions>
- YouTube Shorts classification: <https://support.google.com/youtube/answer/15424877>
- YouTube multilingual audio: <https://support.google.com/youtube/answer/13338784>
- TikTok Direct Post: <https://developers.tiktok.com/doc/content-posting-api-reference-direct-post>
- TikTok creator info: <https://developers.tiktok.com/doc/content-posting-api-reference-query-creator-info>
- TikTok publish status: <https://developers.tiktok.com/doc/content-posting-api-reference-get-video-status>
- TikTok sharing guidelines: <https://developers.tiktok.com/doc/content-sharing-guidelines>
- Meta Instagram official collection: <https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api>
- Meta Instagram video container: <https://www.postman.com/meta/instagram/request/23987686-8d93f052-4c50-4cef-b23e-57732bf370f3>
- Meta Facebook Reels collection: <https://www.postman.com/meta/facebook/folder/simabyk/reels-publishing>
- Meta Facebook Reel finish: <https://www.postman.com/meta/facebook/request/juhnm3q/4-publish-reel>
