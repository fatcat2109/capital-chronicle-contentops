# Platform Setup Requirements

Authority/research date: `2026-08-16`

This is a setup inventory, not credential authority and not publication authority. No credential
value was read, tested, logged or committed. The shadow implementation has no OAuth client and no
live network transport. Any future setup and canary require a new exact owner task.

## YouTube normal video and Shorts

Non-secret destination/configuration:

- `V2_YOUTUBE_CHANNEL_ID`
- expected public channel handle/name
- audited Google Cloud API project identity
- default video category, language and desired privacy/publication policy

Future secret variable names only:

- `V2_YOUTUBE_OAUTH_CLIENT_ID`
- `V2_YOUTUBE_OAUTH_CLIENT_SECRET`
- `V2_YOUTUBE_OAUTH_REFRESH_TOKEN`

OAuth scopes:

- `https://www.googleapis.com/auth/youtube.upload`
- `https://www.googleapis.com/auth/youtube.force-ssl` for metadata/caption management

Manual prerequisites/blockers:

- enable YouTube Data API v3 and configure OAuth consent;
- verify exact expected channel identity before any write;
- complete YouTube API Services audit for public/unlisted capability if the project is covered by
  the post-2020 unverified-project private restriction;
- confirm channel upload/feature eligibility and quota;
- creator-supplied alternate audio remains `ACCOUNT_GATED_STUDIO_CAPABILITY`; the reviewed public
  Data API exposes no alternate-audio upload method, and Studio automation is out of scope.

## TikTok

Non-secret destination/configuration:

- `V2_TIKTOK_CREATOR_USERNAME`
- expected public nickname/handle
- registered TikTok app/client identity
- verified media-host domain or URL prefix for `PULL_FROM_URL`

Future secret variable names only:

- `V2_TIKTOK_CLIENT_KEY`
- `V2_TIKTOK_CLIENT_SECRET`
- `V2_TIKTOK_USER_ACCESS_TOKEN`

OAuth scope: `video.publish`.

Manual prerequisites/blockers:

- app review/approval for Content Posting API and `video.publish`;
- audit for non-private visibility;
- current `creator_info/query` before every attempted post;
- show creator nickname/current privacy and interaction choices, allow editable preset metadata,
  enforce current duration capability, and obtain express user consent before transfer;
- official guidelines reject an internal utility used to upload content to accounts managed by the
  developer/team. Therefore the current owner model is
  `OFFICIAL_API_NOT_ELIGIBLE_FOR_THIS_INTERNAL_AUTOMATION_MODEL` and no credential/account setup
  can make the autonomous adapter ready without a compliant product-model change.

## Instagram Reels and Stories

Non-secret destination/configuration:

- `V2_INSTAGRAM_USER_ID`
- expected professional account username
- account type (`BUSINESS` required for Stories in the reviewed Facebook Login contract)
- `META_GRAPH_API_VERSION` selected and reverified during the future canary preflight
- verified public media host when using `video_url`

Future secret variable names only (exact login variant decides which are needed):

- `V2_INSTAGRAM_USER_ACCESS_TOKEN`
- `V2_META_PAGE_ACCESS_TOKEN`

Instagram Login scopes:

- `instagram_business_basic`
- `instagram_business_content_publish`

Facebook Login permissions/setup may include:

- `instagram_basic`
- `instagram_content_publish`
- `pages_read_engagement`
- linked Facebook Page and Instagram professional account

Manual prerequisites/blockers:

- choose Instagram Login or Facebook Login deliberately and use its matching endpoint/token model;
- Standard Access can serve professional accounts owned/managed and added in the App Dashboard;
  Advanced Access/app review is required for other professional accounts;
- verify Reel/Story publishing eligibility and exact account identity;
- verify the current Graph version and Story-specific duration/readback behavior immediately before
  the live canary;
- sidecar timed captions, localized metadata and alternate audio were not exposed in the reviewed
  container API. Separate localized posts require explicit destination-locale policy and a
  stream-copy localized mux, never a locale picture render.

## Facebook Page Reels

Non-secret destination/configuration:

- `V2_FACEBOOK_PAGE_ID`
- expected Page name/public identity
- `META_GRAPH_API_VERSION` selected and reverified during future canary preflight

Future secret variable name only:

- `V2_FACEBOOK_PAGE_ACCESS_TOKEN`

Required Page permissions in the reviewed official collection/setup path:

- `pages_show_list`
- `pages_read_engagement`
- `pages_manage_posts`

Manual prerequisites/blockers:

- obtain and verify Page task/management access;
- complete any required App Review/Advanced Access for the chosen Page ownership/use model;
- verify current Graph version, Page identity, permissions and Reels eligibility;
- the live canary must confirm `start -> upload -> status -> finish/PUBLISHED -> readback` with one
  exact owner-authorized Page and must retain `UNKNOWN_WRITE` stop/reconcile behavior.

## Shared live-canary prerequisites

- a new exact owner task granting one named provider/surface/destination and publication mode;
- credentials injected only through an approved runtime secret mechanism;
- exact non-secret destination identity readback before mutation;
- no V1 browser/profile reuse;
- no blind retry once a provider may have accepted a write;
- one controlled canary, processing observation, public-object readback and reconciliation before
  any unattended authority is considered.
