# CC-253: hosted article media keeps the fields its readers decide on

From the ContentOps V1 lane (Claude, Opus 5.5), 5 Nov 2026. Ops Product re-scoped the item and assigned it after the CC-248 readings (5 Nov).

## Cause

Since CC-186 (48d152a6, 4 Nov), `prepare_cloudinary_delivery_media` writes each hosted asset row from a fixed field list. That list has no `modality`, no photo rights fields and no alt text, although the step validates `modality` on its input.

- **The newsroom reader admits article media only by those fields.** It is `public_newsroom_articles_v1.py:499-513` in the consumer root, which reads `modality`, the rights fields, `alt_text`, and the caption from `source_provenance.caption` or `chart_title`. So every piece hosted since then was refused as NEWSROOM_MEDIA_TYPE_REFUSED: on 5 Nov, PPI, SEC, FOMC and CPI.
- **Generated post cards were hosted as article media.** `build_post_image_card` returns them with `post_card_binding`, and they went out with article_inclusion true.

## Change (`live_contentops/cloudinary_delivery_media_v1.py`)

- **Article assets:** each on-site article asset copies `ARTICLE_MEDIA_FIELDS` from its own input row, and only those the input row records.
  - The fields: `modality`, `rights_status`, `rights_evidence_sha256`, `license_url`, `source_page_url`, `alt_text`, `chart_title`, `underlying_source_rights_status` and `source_reuse_basis`.
  - The last two are the chart and data-card rights condition that CC-295's reader will apply.
- **Post cards:** a generated post card (`post_card_binding`, or `media_role: post_card`) is validated as before, then hosted with `media_role: delivery_only`, `article_inclusion: false`, `canonical_article_media: false` and `delivery_only: true`. The reader skips it, and it never enters the site.
- **Validation is unchanged.** Social fan-out picks a hosted row by its sha256, never by role, so no destination gets a different image.

## Tests

- **`tests/test_cloudinary_hosted_media_fields_cc253.py` (4 tests):**
  - a chart keeps its fields;
  - a photo keeps its rights binding;
  - a post card is hosted delivery-only;
  - a field the input lacks is never added.

  The first three fail on the old writer. A chart and a photo row now also pass `validate_delivery_media_object`; before, they failed it with `delivery_media_role_invalid`.
- **The hosting-step files:** `test_cloudinary_delivery_media_v1`, `test_post_image_policy_v1`, `test_post_visuals_v1`, `test_fact_card_design_cc245` and `test_media_manifest_authority_v1` pass.
- **The pipeline file:** in `test_eight_platform_substack_first_pipeline_v1`, 2 Instagram tests fail (`test_instagram_consumes_only_verified_delivery_manifest_media`, `test_instagram_fails_definite_no_write_without_verified_delivery_media`). They fail the same way on the unchanged live head 5e18ce51. They are new since CC-268's final run, and they belong to Codex Publisher.

## Backfill of the four refused pieces (`backfill_hosted_media_fields.py`)

The dry run is in `backfill/`. For each piece it holds the exact current manifest (`<run>.before.json`), the proposed one (`<run>.after.json`) and `backfill-summary.json`, with every row's basis and the fields it gains. Nothing is inferred:

| Piece | Row | Basis |
|---|---|---|
| PPI 223555673 | 3 charts, 1 photo | `INPUT_ROW`: `modality`, alt text, source page and rights fields from `run_context_v1.json` `media.assets` (same id and sha256) |
| SEC 223408612 | 2 `post-card-*` | `POST_CARD`: delivery-only |
| | `sec-si-roundtable-event-facts-20261109-cc245` | `NOT_IN_REVIEWED_VISUAL_DECISION`: no input row and not among the article's reviewed charts or photos, so delivery-only |
| | the article's chart | `INPUT_ROW`: its two chart rights fields |
| FOMC 223199520 | `post-card-*` | `POST_CARD` |
| | Warsh archive photo | `INPUT_ROW`: `modality`, rights, licence, source page, alt text |
| | 2 charts | `INPUT_ROW`: their two chart rights fields |
| CPI 223246940 | `post-card-*` | `POST_CARD` |
| | `cpi-annual-history-r3` | `NOT_IN_REVIEWED_VISUAL_DECISION`: the article's visual decision has no charts |
| | `delivery_only_editorial_card` | unchanged |

`--apply --expect backfill/backfill-summary.json` refuses unless each live manifest still hashes to the summary's `before_sha256`. It then writes exactly `after_sha256` in place and reads it back. Rollback writes `<run>.before.json` back.

## The reader on the proposed manifests (read-only, 03:13Z)

| Piece | Before CC-253 | With CC-253 |
|---|---|---|
| FOMC, CPI, SEC | NEWSROOM_MEDIA_TYPE_REFUSED | admitted, so the preview goes from 2 articles to 5 |
| PPI | NEWSROOM_MEDIA_TYPE_REFUSED | NEWSROOM_PUBLIC_CHART_SOURCE_REQUIRED |
| Southwest | NEWSROOM_UTC_CLOCK_REQUIRED | the same; CC-295 owns it |

PPI's next cause is in the reader's chart contract, not in the media rows. All three charts name their sources, but nested:

- the two September charts carry `source.source_id` (SOURCE_1) and `source.source_url` (bls.gov);
- the 24-month chart carries a `source_id` on each series (SOURCE_2, SOURCE_3) with series-level observations.

The reader's `chart_sources` reads only the top-level `source_ids`, `source_id`, `source_urls` and `source_url`, and only top-level observations. Reading the nested ones admits PPI with nothing invented. That is a reader change, and it fits CC-295.
