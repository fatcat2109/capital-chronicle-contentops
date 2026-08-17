# V2 Publication Adapter Reconciliation and Provider Contract Correction V1

Authority date: `2026-08-17`

## Result

`PASS_V2_PUBLICATION_ADAPTERS_RECONCILED_AND_PROVIDER_CONTRACTS_READY_FOR_EXACT_LIVE_CANARY_GATE`

This is the task ceiling. It does not grant provider, OAuth, credential, private/unlisted/draft,
public-write, browser, V1, scheduler, or unattended execution authority.

## Repository reconciliation

- freshly fetched task-start base:
  `origin/master@eda25731723a0d80130254fb68533fb42a9d9bee`;
- pre-commit refresh found the concurrent V1-only master commit
  `e29bd8dfd2217f684c2e9d3819cfeebe91b3da14`; the clean task branch was fast-forwarded to that
  current master before its V2 commit;
- new branch:
  `task/v2-publication-adapter-reconciliation-provider-contract-correction-v1`;
- historical donor:
  `task/v2-official-platform-publication-adapters-shadow-closed-loop-v1@18c16722ddf0fbdf1c42c8356de2f3245039f36a`;
- merge base: `74a3751b2cd28928c437b202dc7cbaac3669924d`;
- divergence at reconciliation start: fresh master nine commits ahead, donor one commit ahead;
- no donor merge, rebase, or cherry-pick;
- useful adapter/control-plane/test concepts were ported selectively;
- donor AGENTS, authority, status, handoff and generated CodeGraph bytes were not transplanted.

## Corrected contracts

- Non-secret destination identity now includes explicit `PUBLICATION` versus `DRAFT_DELIVERY`
  intent and Instagram login variant in deterministic attempt identity. TikTok draft delivery
  carries no `PUBLIC`, `PRIVATE` or `UNLISTED` mode.
- YouTube normal video and Shorts use `videos.insert`; insert binds title, description,
  category, default language, status and localizations. Localization-only mutation is
  `videos.update?part=localizations` with body `id + localizations` and no snippet.
- TikTok uses Upload-to-TikTok draft delivery with `video.upload`,
  `/v2/post/publish/inbox/video/init/`, provider upload-URL `PUT`, and status fetch.
  `SEND_TO_USER_INBOX` is draft delivery, requires creator finalization, and proves no public
  post. Optional `video.query` is guarded until a public video ID already exists.
  The Sandbox OAuth/open-id/scope bootstrap is accepted historical evidence; Production review is
  separate and remains `PRODUCTION_REVIEW_REQUIRED`. Direct Post and `video.publish` are off.
- Instagram destinations select exactly one contract:
  `INSTAGRAM_LOGIN` uses `graph.instagram.com`, an Instagram User access token, the
  `instagram_business_*` permission family, and no Facebook Page dependency;
  `FACEBOOK_LOGIN` uses `graph.facebook.com`, a Facebook Page access token, a linked Page /
  professional account, and the `instagram_basic`, `instagram_content_publish` and
  `pages_*` family. Graph version remains runtime configuration.
- Instagram Story reconciliation requires verified container/media/owner/surface fields but not
  a permalink.
- Facebook Page Reels keeps Page identity preflight separate from the Page-token principal and
  uses `/{api_version}/me/video_reels` for start and finish.
- YouTube alternate audio remains `ACCOUNT_GATED_STUDIO_CAPABILITY`; no unsupported Data API
  transport is claimed.

## Validation

- focused adapter + package + zero-rerender tests: `39 passed`;
- combined focused + CodeGraph contract command: `50 passed` (`39` adapter/package/
  zero-rerender plus `11` CodeGraph tests);
- Python lint: `All checks passed`;
- accepted-package six-surface shadow demo: `PASS_SHADOW_PUBLICATION_CLOSED_LOOP`;
- longform package:
  `pkg_33715fff75a0204cf430bbb763cb5ff9b6339e370b323c1d754aa6a91f24b4db`;
- Short package:
  `pkg_2dfe4af587fd8135d04bae456b8c5b30a1560be91232b34f520cf7f05a71c0b2`;
- six surface traces end in `READBACK_CONFIRMED`;
- TikTok trace includes `DRAFT_DELIVERED_TO_CREATOR`, no
  `PUBLISHED_UNCONFIRMED`, no public object ID and creator-finalization required;
- positive ambiguous-write proof blocks blind retry and resolves by readback;
- unresolved ambiguous-write proof blocks blind retry and remains `UNKNOWN_WRITE`;
- CodeGraph: regenerated at source HEAD
  `e29bd8dfd2217f684c2e9d3819cfeebe91b3da14`, `7072` nodes / `13284` edges;
  final check: `CODEGRAPH_CURRENT`.

## Safety receipt

- real provider calls/writes: 0;
- OAuth operations: 0;
- credential reads/writes: 0;
- private, unlisted or draft platform writes: 0;
- browser/CDP actions: 0;
- V1/runtime/store/publication mutations: 0;
- scheduler/task mutations: 0;
- Remotion or localized picture renders: 0;
- audio generation: 0;
- XHIGH/MAX/ULTRA calls: 0.

## Single exact next gate

`TASK_CONTENTOPS_V2_TIKTOK_UPLOAD_DRAFT_READINESS_AND_EXACT_OWNER_LIVE_CANARY_GATE_V1`

That future task must first run a non-secret identity/scope/readiness preflight through the
approved secure runtime boundary, then require exact owner authority for one Upload-to-TikTok
draft. Success at `SEND_TO_USER_INBOX` means draft delivery only; Jim must complete the TikTok
editing/finalization flow. Public readback is a later conditional step only after a public ID
exists. This gate is named but not started or authorized here.
