# Official TikTok Contract Refresh

Research date: `2026-08-17`

Only first-party TikTok for Developers documentation was used:

- <https://developers.tiktok.com/doc/content-posting-api-reference-upload-video>
- <https://developers.tiktok.com/doc/content-posting-api-reference-get-video-status>
- <https://developers.tiktok.com/doc/content-posting-api-media-transfer-guide>
- <https://developers.tiktok.com/doc/content-posting-api-get-started-upload-content>
- <https://developers.tiktok.com/doc/tiktok-api-v2-video-query>
- <https://developers.tiktok.com/doc/tiktok-api-scopes>
- <https://developers.tiktok.com/doc/add-a-sandbox>

## Confirmed canary contract

- Upload-to-TikTok draft initialization is
  `POST /v2/post/publish/inbox/video/init/` with `video.upload`.
- `FILE_UPLOAD` sends only `source_info`: source, actual byte size, validated chunk size, and
  validated total chunk count. No `post_info`, caption, privacy, duet, stitch, or comment fields
  belong in this draft init request.
- Initialization returns a `publish_id` and transient `upload_url`. The entire returned upload URL,
  including its query, is required for transfer. The implementation keeps it in memory only.
- Media transfer is sequential `PUT` with exact `Content-Type`, `Content-Length`, and
  `Content-Range`.
- Files below 5 MB upload whole. Each normal chunk is 5–64 MB; a final chunk may absorb trailing
  bytes up to 128 MB. Files above 64 MB require multiple chunks; maximum chunk count is 1000.
- The accepted 22,101,311-byte Short therefore uses exactly one 22,101,311-byte chunk.
- Current video restrictions allow MP4/H.264, 23–60 fps, dimensions 360–4096 pixels, duration up
  to 10 minutes for this API, and file size up to 4 GB. The accepted Short is within all bounds.
- Status readback is `POST /v2/post/publish/status/fetch/`, limited to 30 requests per minute per
  user access token. The canary uses a small bounded backoff and no tight polling.
- `PROCESSING_UPLOAD` is nonterminal. `SEND_TO_USER_INBOX` means TikTok sent the creator an inbox
  notification to complete the draft in TikTok's editing flow. It is the canary's success and stop
  condition.
- For Upload Content, `PUBLISH_COMPLETE` means the creator later used that editing flow and posted
  the media. It is unexpected and fail-closed during this canary.
- The status response's exact TikTok field spelling is `publicaly_available_post_id`. TikTok returns
  a `post_id` in that list only when a post is published for public viewership and has passed TikTok
  moderation. Therefore `PUBLISH_COMPLETE` alone is creator-finalization evidence, not public-post
  confirmation.
- A public post ID is not guaranteed at draft-delivery or creator-finalization time. `video.query`
  requires `video.list` and is not called by this canary.
- `video.upload` is the draft-sharing scope; `video.publish` is Direct Post and is forbidden here.
- Sandbox is a restricted test environment and does not establish Production or public-video
  approval. The canary carries Sandbox draft-delivery authority only.

## Implementation consequences

- No Direct Post endpoint exists in the executor.
- No `video.publish`, `video.query`, creator-finalization, or public-post operation exists in the
  executor.
- An ambiguous init is `UNKNOWN_WRITE` with no automatic retry.
- An ambiguous upload with a known `publish_id` transitions to status readback only; it cannot issue
  a second `PUT`.
- `SEND_TO_USER_INBOX` produces `DRAFT_DELIVERY_CONFIRMED`,
  `creator_finalization_required=true`, `creator_finalization_observed=false`, and
  `public_post_confirmed=false`.
- Unexpected `PUBLISH_COMPLETE` produces `creator_finalization_observed=true` while retaining the
  fail-closed `UNEXPECTED_PUBLISH_COMPLETE` classification. `public_post_confirmed=true` only when
  at least one actual ID is present in `publicaly_available_post_id`; no raw public ID is persisted.
