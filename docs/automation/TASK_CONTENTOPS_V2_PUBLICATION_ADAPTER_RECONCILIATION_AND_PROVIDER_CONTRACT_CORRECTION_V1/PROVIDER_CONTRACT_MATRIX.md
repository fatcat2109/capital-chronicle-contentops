# Provider Contract and Readiness Matrix

Research date: `2026-08-17`

| Surface | Canonical write plan | Readback/reconciliation | Current blocker |
|---|---|---|---|
| YouTube video | `videos.insert` with `snippet,status,localizations`; resumable media; timed caption insert | channel, title, privacy, upload/processing, localization and caption track | exact channel/project/OAuth readiness and applicable API audit/live-canary authority |
| YouTube Shorts | same `videos.insert`; no separate Shorts endpoint or flag | same video readback; product-level Shorts classification remains separate | same setup plus later product classification observation |
| TikTok | `video.upload`; inbox init; upload URL `PUT`; status fetch; Direct Post off | `SEND_TO_USER_INBOX` confirms draft delivery only; public ID absent; creator finalizes | Sandbox OAuth/open-id/scopes bootstrap historically proven; Production review plus secure readiness recheck and exact one-draft owner authority remain |
| Instagram Reel / Instagram Login | `graph.instagram.com`; Instagram User token; `instagram_business_basic` + `instagram_business_content_publish` | container status, media ID, owner, type/product, Reel caption/permalink | professional identity, app access, runtime Graph version and exact canary |
| Instagram Story / Facebook Login | `graph.facebook.com`; Page token; linked Page/pro account; `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement` | container status, media ID, owner, type/product; permalink is not required | linked business account, Page/app access, runtime Graph version and exact canary |
| Facebook Page Reel | separate Page identity preflight; Page token; `/{api_version}/me/video_reels` start/upload/status/finish | video ID, Page identity, title/description, processing/publishing phases and permalink | Page task/permission eligibility, runtime Graph version and exact canary |

## YouTube partial-update rule

The Data API treats `part` as the set of mutable resource parts included in an update. A
localization-only update therefore sends:

```text
PUT https://www.googleapis.com/youtube/v3/videos?part=localizations
body = {"id": "...", "localizations": {...}}
```

It does not send `snippet`; consequently it cannot accidentally omit required snippet fields or
erase unrelated snippet properties. Default language is established in the insert contract.

## TikTok draft/public boundary

- `DIRECT_POST_AUTONOMOUS_INTERNAL_MODEL`: `OFF / NONCANONICAL`; `video.publish` is not
  requested and no Direct Post endpoint is planned.
- `UPLOAD_TO_TIKTOK_DRAFT_WITH_CREATOR_FINALIZATION`:
  `PRODUCTION_REVIEW_REQUIRED`; the historical Sandbox credential proof does not establish
  Production approval.

`SEND_TO_USER_INBOX` means TikTok notified the creator to continue the native editing flow.
It is represented as `DRAFT_DELIVERED_TO_CREATOR`, with:

- `public_post_confirmed = false`;
- no provider public object ID;
- creator finalization required;
- no Direct Post creator-info/post-info contract;
- no `video.query` until a later public ID is observed.

OAuth/API `open_id` is the hard identity binding. The public handle `jimpham.cc` remains an
operator/browser-confirmed label and is not claimed as proven by `user.info.basic`.

## First-party references

- YouTube videos.insert:
  <https://developers.google.com/youtube/v3/docs/videos/insert>
- YouTube videos.update:
  <https://developers.google.com/youtube/v3/docs/videos/update>
- YouTube videos.list:
  <https://developers.google.com/youtube/v3/docs/videos/list>
- YouTube captions:
  <https://developers.google.com/youtube/v3/docs/captions>
- TikTok Upload API:
  <https://developers.tiktok.com/doc/content-posting-api-reference-upload-video>
- TikTok status:
  <https://developers.tiktok.com/doc/content-posting-api-reference-get-video-status>
- TikTok video.query:
  <https://developers.tiktok.com/doc/tiktok-api-v2-video-query>
- Meta Instagram official collection:
  <https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api>
- Meta Facebook Reels official collection:
  <https://www.postman.com/meta/facebook/documentation/r56bjfd/facebook-api>
