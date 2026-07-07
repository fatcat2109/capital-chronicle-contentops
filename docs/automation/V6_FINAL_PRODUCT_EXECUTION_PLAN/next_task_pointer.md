# V6 Next Task Pointer

Current task just completed: `TASK_CONTENTOPS_V6_LINKEDIN_NATIVE_IMAGE_AND_SUBSTACK_IN_BODY_VISUAL_PLACEMENT_REPAIR_V0`.

Result: scoped non-bypassed live repair run `v6_pipeline_d49f6e14a856` reached true `DISPATCH_COMPLETE` for `substack` and `linkedin` from verified remote HEAD `eb48f275990a286f40d3f73a40e1b00f4f7503cd`, with live provider enabled, live dispatch enabled, default 420s timeout, and no `CONTENTOPS_BYPASS_QUALITY_GATES` process or `.env` entry.

Public outputs:

- Substack public URL: `https://capitalchronicle.substack.com/p/crude-awakenings-how-spiking-oil-13c`
- Public/CDN image URL: `https://substackcdn.com/image/fetch/$s_!TkqE!,w_1200,h_675,c_fill,f_jpg,q_auto:good,fl_progressive:steep,g_auto/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F80bf06f3-6595-4146-aaa5-bc467d7c2a08_1725x1080.png`
- Substack visual markers: `2`
- Uploaded Substack visuals: `2`
- Public visual readback: `PASS` with `2` public images and order/placement proof
- LinkedIn activity id: `activity_9fbd4f4aa083`
- LinkedIn URL returned by adapter: `https://www.linkedin.com/feed/`
- LinkedIn media proof: `media_upload_status=uploaded`, `media_preview_detected=true`, selector `file_chooser:button[aria-label*='Add media']`, preview selector `div[role='dialog'] img[src*='media']`

Article quality evidence:

- Packet body word count: `2,009`
- Recomputed body/heading word estimate: `2,060`
- Sections: `8`
- Source-trail entries: `3`
- Citations: `6`
- Numeric evidence references: estimated `57`
- SEO metadata: slug candidate, dek, and meta description present
- Visual slots: `2` purposeful in-body slots
- Article validator: no failures

Media judgment evidence:

- Media audit status: `PASS`
- Source label: `FRED series DCOILWTICO; underlying source U.S. Energy Information Administration`
- Latest observation/time coverage: `2026-06-29` / end year `2026`
- Replacement notes: `search_candidate_rejected:media_provenance_weak_upload_host|media_time_coverage_unverified_for_current_topic`, `source_backed_chart_pack_selected`

Substack placement proof:

- Primary image previous heading: `A source-led Capital Chronicle briefing on WTI, recession-risk interpretation, yield curves, and evidence discipline`
- Primary image next heading: `The Macro Setup: Current Oil Evidence Before Narrative`
- Second image previous heading: `Market Implications Without Directional Noise`
- Second image next heading: `How to Read the Source Trail`
- `all_images_after_source_trail=false`

Per-platform repair status:

- Substack: `SUCCESS`
- LinkedIn: `SUCCESS`

Prior unaffected platform reconciliation:

- Prior full all-platform run `v6_pipeline_3c44a9855cc6` remains the reconciled evidence for X, Instagram, Facebook Page, Telegram, Threads, and Discord.
- The repair run was intentionally scoped to Substack + LinkedIn to avoid duplicating unaffected platform posts.

Remaining non-launch blockers / next hardening:

- Google image search remains blocked/empty in this environment; source-backed chart-pack fallback remains the reliable current path for oil topics.
- Provider-native drafts still need reliability hardening so deterministic repair is less frequently required.
- LinkedIn returns a feed URL plus native upload/preview proof; stable public permalink/readback still needs hardening or manual review.
- Manual screenshot/crop review remains recommended across public platform outputs before launch acceptance.

Recommended next task:

```text
TASK_CONTENTOPS_V6_PROVIDER_NATIVE_DRAFT_RELIABILITY_AND_PUBLIC_VISUAL_QA_V0
```

Purpose: harden provider-native article generation so deterministic source-backed repair is not the common path, then perform public screenshot/crop QA and LinkedIn permalink/readback hardening across final platform outputs.

Evidence to read before the next task:

- `docs/automation/V6_LINKEDIN_SUBSTACK_VISUAL_REPAIR/linkedin_substack_visual_repair_evidence_v0.json`
- `docs/automation/V6_PLATFORM_NATIVE_VARIANTS/latest_dispatch_audit.json`
- `docs/automation/V6_CANONICAL_SUBSTACK_ARTICLE/canonical_article_packet.json`
- `docs/automation/V6_PLATFORM_NATIVE_VARIANTS/platform_variant_packet.json`
