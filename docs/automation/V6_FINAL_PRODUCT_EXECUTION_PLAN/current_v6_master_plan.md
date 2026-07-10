# ContentOps V6 Current Master Plan

Authority date: 2026-07-10

Current evidence run: `eight_platform_live_20260710_recovery1`

Canonical runner: `live_contentops.eight_platform_substack_first_pipeline_v1`

## 1. Product Identity And North Star

Capital Chronicle ContentOps V6 is an AI-native automated editorial production and supervised distribution operating system. Its job is to turn current market information into one grounded, publication-quality article and a fully auditable family of native platform derivatives.

The canonical loop is:

```text
current headline/CDP intake
-> LLM semantic clustering, deduplication, impact ranking, and idea selection
-> Capital Chronicle database/source support packet
-> tier-1 financial article
-> minimum three analytically relevant source-backed visuals
-> canonical Substack publication and public readback
-> platform-native derivative generation
-> deterministic media-manifest binding
-> platform-limit-aware root/reply threading
-> live dispatch through ContentOps adapters
-> public text/media/link readback
-> idempotent failed-destination repair
-> evidence, telemetry, and operator review
```

Substack is canonical. Telegram, X, Discord, LinkedIn, Meta, YouTube, TikTok, and future destinations are distribution surfaces and must point back to the canonical Substack URL. Manual action is recovery context, never the product north star.

## 2. Idea Selection

The LLM reads current CDP/headline inputs, clusters semantically similar events, removes duplicates, ranks likely macro and cross-asset impact, and explains why the selected idea is timely. Keyword scores may assist retrieval but cannot make the editorial decision.

Selection requires a grounded support gate: sufficient source material, numeric authority, and at least three useful visual roles. If the leading idea cannot support those requirements, ContentOps selects the next supportable high-impact idea.

The same topic cannot run within 24 hours unless a genuine hotspot materially changes the global-asset setup. Hotspots include FOMC, CPI/payrolls, supply interruption, geopolitical escalation, oil shock, sovereign or banking stress, liquidity shock, FX intervention, and major US technology, AI, or semiconductor events visibly moving markets. The exception and its evidence must be recorded.

## 3. Source And Numeric Authority

The Capital Chronicle database and source packet are the authority for numeric claims and context. Preferred primary sources include FRED, the Federal Reserve, Treasury, EIA, and other official datasets. Headlines establish timeliness; they do not independently authorize unsupported numbers.

Every numeric claim must trace to a source record or be clearly qualified. ContentOps does not invent values, interpolate unsupported observations, or turn a single data point into financial advice.

## 4. Editorial Acceptance

The canonical article must have a sharp headline and lede, explicit market mechanism, policy or geopolitical context, cross-asset implications, useful synthesis, clean SEO title/meta/slug/section structure, and a non-advice caveat. Generic filler, unsupported certainty, and synthetic trading recommendations fail the gate.

The article must contain at least three topic-specific analytical visuals spread through the body. Their required roles are:

1. Current signal or market state.
2. Policy mechanism or comparison.
3. Cross-asset, curve, or broader context.

Each visual requires a stable asset ID, local source path, SHA-256, MIME type, dimensions, source/provenance, chart title, caption, alt text, and article-section association.

## 5. Deterministic Media Authority

The generated media manifest is the only derivative-media authority. Platform adapters receive the exact approved media object; they do not scrape the public Substack DOM to pick an image.

For a chart role, ContentOps rejects publication avatars, logos, favicons, author images, social thumbnails, unapproved hashes, square branding assets, and images below the configured meaningful dimension threshold. Public readback must compare the visible output with the expected chart and record the media asset ID, hash, and visual verification result.

The current primary asset is `primary`, SHA-256 `b83584745931f60d976bde11b383ef3ca75c5cfed254c2c59af7a7513572a7af`.

## 6. Platform Delivery Contract

The machine-readable registry is `platform_delivery_contract_v1.json` beside this plan.

| Destination | Native product contract |
| --- | --- |
| Substack | Full canonical article, SEO metadata, three in-body visuals, public URL/readback. |
| Telegram | Meaningful text, approved media, canonical URL, message ID/readback. |
| X | Root with opening, chart, canonical URL; overflow in ordered replies. |
| Discord | Newsroom derivative and canonical URL; rich preview is verified but may use publication preview art. |
| LinkedIn | Analytical text, approved chart, canonical URL, permalink/readback. |
| Facebook Page | Native text, approved chart, canonical URL, post ID/readback. |
| Instagram Business | Approved chart/carousel, complete caption, canonical URL, media ID/readback. |
| Threads | Root with canonical URL and chart where possible; overflow in ordered replies. |
| YouTube | Community text + approved image + canonical URL. |
| TikTok | Configured native derivative or an explicit authenticated-session blocker. |

Platform family counts and expanded destination counts are reported separately. The current run covers ten destinations across the Substack canonical family and eight distribution families.

## 7. Overflow And Threading

Hard truncation and synthetic ellipses are forbidden. The variant compiler calculates the real platform limit, puts a strong opening, standalone thesis, canonical URL, and chart where supported in the root, then packs remaining complete sentences into ordered replies or comments. Evidence records every root/reply ID, URL, order, and parent relationship.

## 8. YouTube Surface Rule

The default article-distribution route is YouTube Community only. It requires non-empty editorial text, one approved image, a canonical Substack URL, the Capital Chronicle channel identity, a stable public post URL/ID, and readback.

Video, Shorts, slideshows, chart animations, and source-chart videos belong to a separate explicit non-default product mode. The default runner must not import or invoke them. The prior Short at `https://www.youtube.com/watch?v=FvasNsZ1F2U` is preserved as `WRONG_SURFACE_EXECUTION_NOT_ACCEPTED` and is not success evidence.

## 9. Browser And Execution Authority

The canonical profile is:

```text
A:\Capital Chronicle\operator-browser-profiles\contentops-social-main
```

It is a persistent Microsoft Edge profile. CDP port `9223` is the current verified attachment; port `9222` must be rejected when owned by Chrome, Antigravity, or an unknown profile. ContentOps may inspect non-secret session readiness but never persist cookies, tokens, localStorage, sessionStorage, or raw secret values.

All final writes originate from:

```text
live_contentops.eight_platform_substack_first_pipeline_v1
-> platform-native adapter
-> idempotency ledger
-> public URL/ID capture
-> strict public readback
-> run evidence
```

Browser inspection may diagnose or read back state. Ad hoc builder clicks are not production completion.

## 10. Idempotency, Resume, And Reconciliation

Canonical publication is guarded against re-entry. Derivative-only resume freezes Substack and already successful destinations. A destination is retried only after exact post reconciliation and only through its adapter.

Malformed published output is never silently counted as success. Repair order is edit, author reply/comment, then exactly one corrected replacement when the platform cannot repair in place. Old posts are preserved and related through `SUPERSEDED_*` evidence. Unknown write outcomes block automatic retries until read-only reconciliation resolves them.

## 11. Readback And Classification

There is no success from a click, upload response, API `200`, image count, or composer state. Success requires the correct account and platform surface, stable public URL/ID, visible approved text, expected media, visible canonical link, and matching public readback. Replies must be complete and ordered.

A destination fails when media is wrong, text is missing or hard-truncated, the canonical URL is absent, a reply chain is incomplete, public identity/URL/readback is missing, the wrong account/surface is used, or YouTube video substitutes for Community.

- `PASS`: canonical Substack and all required available destinations meet strict readback; a separately named external authentication blocker may remain visible in the expanded matrix.
- `PARTIAL`: canonical output exists but one or more required destination corrections hit a concrete external blocker.
- `BLOCKED`: canonical Substack publication/readback cannot be achieved.
- `FAIL`: a write occurred but public output violates payload, media, identity, or surface contract.

## 12. Current Live Evidence

The run `eight_platform_live_20260710_recovery1` is `PASS_SUBSTACK_FIRST_TEXT_IMAGE_DISTRIBUTION_V1` for the text/image distribution product, with TikTok explicitly blocked by canonical-profile authentication.

- Substack: `https://capitalchronicle.substack.com/p/effective-fed-funds-rate-holds-at`
- Telegram: `https://t.me/CapitalChronicle/61`
- X: `https://x.com/Capitalnicle/status/2075510632770875841`, six verified replies
- LinkedIn: `https://www.linkedin.com/feed/update/urn:li:activity:7481289145206644736/`
- Facebook: `https://www.facebook.com/1342369584748125/posts/1342374731414277`
- Instagram: `https://www.instagram.com/p/DanF4lxDmDs/`
- Threads: `https://www.threads.com/@official.capitalchronicle/post/Dam28KxnwGV`, three verified replies
- YouTube Community: `https://www.youtube.com/post/UgkxLF5TJ6zbW1-3_at3PdfBr8wlbkFbko60`
- Discord: message `1525069505905037414`
- TikTok: `BLOCKED_TIKTOK_CANONICAL_PROFILE_NOT_AUTHENTICATED`

Facebook and Instagram wrong-logo posts are preserved as `SUPERSEDED_WRONG_MEDIA`. LinkedIn replacement `7481311616265895936` is preserved as `SUPERSEDED_IMAGE_ONLY`. The accepted LinkedIn original was edited successfully.

Evidence authority: `docs/automation/EIGHT_PLATFORM_FULL_PIPELINE_V1/eight_platform_live_20260710_recovery1/`.

## 13. Product Direction

The canonical UI remains `ui/contentops_v5/`. The next route is to expose the strict platform matrix, reply chains, media-hash continuity, supersession relationships, and blockers in the V5 command center, then complete a TikTok authenticated-profile handoff and a fresh scheduled-run rehearsal. No new canonical article is part of the immediate handoff task.
