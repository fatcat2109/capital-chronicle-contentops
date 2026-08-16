# Platform Publication Contracts

Research date: `2026-08-16`

Scope: read-only official documentation research for the next publication-adapter task. This
document does not authorize or implement any upload, draft, schedule, metadata mutation, or
other platform write. `ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY` remains controlling.

Classification vocabulary:

- `API_CONFIRMED`
- `PRODUCT_UI_ONLY_OR_ACCOUNT_GATED`
- `NOT_EXPOSED_BY_VERIFIED_API`
- `UNRESOLVED`

## Core media compatibility

| Surface | Future adapter media contract | Duration contract relevant to this factory | API availability / prerequisites |
|---|---|---|---|
| YouTube normal video | MP4/H.264 progressive/yuv420p with AAC-LC 48 kHz is the official recommended path; standard desktop aspect is 16:9 and BT.709 is recommended for SDR. | Default accounts: up to 15 minutes; verified accounts may exceed 15 minutes; absolute upload ceiling is 12 hours or 256 GB, whichever is less. The factory's 5–45 minute longform stays inside the verified-account envelope. | `API_CONFIRMED`: `videos.insert` media upload with OAuth. Unverified API projects created after 2020-07-28 are private-only until audit. |
| YouTube Shorts | Same video-upload endpoint/media path; square or vertical uploads up to three minutes are categorized as Shorts for standard channels. Native 1080x1920 is compatible. | Product classification currently allows up to 3 minutes. This factory deliberately keeps its core Short at 30–60 seconds. | `API_CONFIRMED`: upload through `videos.insert`; no separate public "Shorts upload" endpoint/flag was found. Shorts classification is product behavior based on media. |
| TikTok | Content Posting API accepts MP4 (recommended), MOV, or WebM; H.264 is recommended; 23–60 fps; both dimensions 360–4096 px; maximum 4 GB. Native 1080x1920/30 fps is compatible. | API media transfer accepts up to 10 minutes, but the adapter must query `creator_info.max_video_post_duration_sec` because creator limits vary. | `API_CONFIRMED`: Direct Post requires an approved app, Direct Post configuration, `video.publish`, current creator-info UI/consent, and audit for non-private visibility. Upload-to-inbox uses `video.upload` and requires creator completion. Pull-from-URL requires verified domain/prefix ownership. |
| Instagram Reels | Official Meta collection: MP4/MOV; H.264/HEVC; AAC 48 kHz; 23–60 fps; 1920 horizontal max; 9:16 recommended; <=25 Mbps video; <=128 kbps audio; <=1 GB. Native 1080x1920 is compatible. | Official API collection states 3 seconds–15 minutes. | `API_CONFIRMED`: Instagram professional account; content-publish permission/access; create `REELS` container from public `video_url` or resumable upload, wait for `FINISHED`, then `media_publish`. Account/login variant determines token and permission set. |
| Instagram Story | Same Instagram video-container flow with `media_type=STORIES`; native 1080x1920 is the intended full-screen derivative. | `UNRESOLVED`: the verified API collection exposes Story containers but the API-specific maximum was not stated in the reviewed official reference. Official Meta product/ad guidance supports 60-second Story video, so the factory's <=60-second Short is conservative, but the future adapter must re-read the exact current endpoint limit. | `API_CONFIRMED` for publishing a Story container; `PRODUCT_UI_ONLY_OR_ACCOUNT_GATED` because Stories publishing is limited to Instagram Business accounts in the reviewed official collection. |
| Facebook Reels | Official Meta collection accepts many containers including MP4; minimum 540x960; exact 9:16; minimum 23 fps. Native 1080x1920/30 fps is compatible. | Official Reels Publishing API collection states 4–60 seconds. (Facebook product UI may allow other lengths; the adapter must follow the API contract.) | `API_CONFIRMED`: Page Reels flow initializes `/{page-id}/video_reels`, uploads to returned `rupload` URL, then finishes with `video_state`; requires a Page access token and Page permissions such as `pages_show_list`, `pages_read_engagement`, and `pages_manage_posts`. |

## Metadata, captions, audio, and readback

| Surface | Metadata | Timed captions | Alternate audio | Localized metadata | Status/readback |
|---|---|---|---|---|---|
| YouTube normal video | `API_CONFIRMED`: title, description, tags, category, default language, privacy, publish time, made-for-kids, synthetic-media flag. | `API_CONFIRMED`: `captions.insert` uploads a language-tagged track; `captions.list/download` support readback. Auto-sync API parameter is deprecated, so send timed files. | `PRODUCT_UI_ONLY_OR_ACCOUNT_GATED`: Studio supports creator-supplied multilingual audio for eligible creators. `NOT_EXPOSED_BY_VERIFIED_API`: no public Data API alternate-audio upload method was found. | `API_CONFIRMED`: `localizations` supports BCP-47 keyed title/description. | `API_CONFIRMED`: `videos.list` exposes upload/processing/privacy status and failure/rejection reasons. |
| YouTube Shorts | Same API metadata/caption/localization model as video upload. | `API_CONFIRMED` through the video caption resource. | Same classification as normal video: Studio feature exists and is eligibility-gated; no verified public API uploader. | `API_CONFIRMED` through video `localizations`. | `API_CONFIRMED` through video resource/status; verify eventual Shorts classification during readback. |
| TikTok | `API_CONFIRMED`: one post `title`/caption with hashtags/mentions, privacy and interaction settings, cover timestamp. | `NOT_EXPOSED_BY_VERIFIED_API`: no sidecar timed-caption upload field was found in Direct Post/Upload. Use burned captions where editorially approved. | `NOT_EXPOSED_BY_VERIFIED_API`. | `NOT_EXPOSED_BY_VERIFIED_API`: one caption/title is sent per post. | `API_CONFIRMED`: publish-status endpoint returns state such as `PUBLISH_COMPLETE` and failure reason; Display API video object can expose ID, URL, title/description, dimensions, duration, and metrics with the appropriate scopes. |
| Instagram Reels | `API_CONFIRMED`: one `caption`; options include feed sharing, cover/thumbnail-related fields where supported by the chosen login/API variant. | `NOT_EXPOSED_BY_VERIFIED_API`: no sidecar timed-caption parameter was found in the reviewed container contract. | `NOT_EXPOSED_BY_VERIFIED_API`. | `NOT_EXPOSED_BY_VERIFIED_API`: no locale-keyed metadata contract was found. Publish separate localized packages only if later product policy authorizes separate posts. | `API_CONFIRMED`: container `status_code/status` can be polled; published media ID is returned and `media_product_type` distinguishes a Reel. |
| Instagram Story | The reviewed API container uses media only; no ordinary post caption field was verified for Stories. | `NOT_EXPOSED_BY_VERIFIED_API`; use the approved burned-caption derivative when captions are required. | `NOT_EXPOSED_BY_VERIFIED_API`. | `NOT_EXPOSED_BY_VERIFIED_API`. | `API_CONFIRMED`: container status and returned published media ID; exact post-publication Story readback fields remain `UNRESOLVED` for the next adapter. |
| Facebook Reels | `API_CONFIRMED`: finish phase supports optional title and description plus `video_state`. | `NOT_EXPOSED_BY_VERIFIED_API` in the reviewed Reels flow. | `NOT_EXPOSED_BY_VERIFIED_API`. | `NOT_EXPOSED_BY_VERIFIED_API`. | `API_CONFIRMED`: the flow exposes a `video_id` and upload/status/publish phases; exact fields and reconciliation semantics must be rebound to the current Graph version during adapter implementation. |

## Consequences for the platform-neutral package

1. One native 1080x1920/30 fps <=60-second master is compatible with the verified core media
   envelope for YouTube Shorts, TikTok, Instagram Reels, Instagram Story, and Facebook Reels.
   No creatively different surface video is justified by current contracts.
2. Keep clean video, burned-caption video, SRT, VTT, localized audio, and localized metadata as
   separate first-class artifacts. YouTube can consume sidecars/localizations; the other
   reviewed APIs may require burned captions or one localized post/package per language.
3. Keep language audio independent from picture. YouTube's product supports alternate audio,
   but its verified public API does not expose upload in the reviewed contract. Future adapters
   must not invent that capability.
4. TikTok duration must be checked against current creator-info before upload. Instagram Story
   API duration and exact post-readback remain an explicit re-verification item.

## Official references

- YouTube recommended encoding: <https://support.google.com/youtube/answer/1722171>
- YouTube maximum upload duration/size and account verification: <https://support.google.com/youtube/answer/71673>
- YouTube `videos.insert`: <https://developers.google.com/youtube/v3/docs/videos/insert>
- YouTube video resource/status/localizations: <https://developers.google.com/youtube/v3/docs/videos>
- YouTube caption upload: <https://developers.google.com/youtube/v3/docs/captions/insert>
- YouTube three-minute Shorts classification: <https://support.google.com/youtube/answer/15424877>
- YouTube multilingual audio product/eligibility: <https://support.google.com/youtube/answer/13338784>
- TikTok Content Posting API start/prerequisites: <https://developers.tiktok.com/doc/content-posting-api-get-started>
- TikTok Direct Post contract: <https://developers.tiktok.com/doc/content-posting-api-reference-direct-post>
- TikTok media restrictions/transfer: <https://developers.tiktok.com/doc/content-posting-api-media-transfer-guide>
- TikTok creator duration capability: <https://developers.tiktok.com/doc/content-posting-api-reference-query-creator-info>
- TikTok publish status: <https://developers.tiktok.com/doc/content-posting-api-reference-get-video-status>
- Meta official Instagram API collection: <https://www.postman.com/meta/workspace/instagram/documentation/23987686-9386f468-7714-490f-9bfc-9442db5c8f00>
- Meta official Instagram video-container request (`REELS`/`STORIES`): <https://www.postman.com/meta/instagram/request/23987686-8d93f052-4c50-4cef-b23e-57732bf370f3>
- Meta official Instagram container-status request: <https://www.postman.com/meta/instagram/request/munmruq/get-ig-container-status>
- Meta official Facebook Reels Publishing collection: <https://www.postman.com/meta/facebook/folder/simabyk/reels-publishing>
- Meta official Facebook Reel finish fields: <https://www.postman.com/meta/facebook/request/juhnm3q/4-publish-reel>
