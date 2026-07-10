# Generic Evidence, Freshness, Visual, And Editorial Fabric V2

## Consumer Boundary

ContentOps consumes `CapitalChronicleContentEvidencePacketV2`. Production configuration supplies either `--capital-chronicle-root` or `--cc-evidence-packet`; production logic contains no machine-specific root.

The bridge reads documented current-state artifacts only: `MarketSnapshot`, `MarketHistory`, `DataQualityReport`, `InputStateManifest`, and `SourceHealth`. It does not crawl arbitrary files, read `.env`, call MT5, mutate the ingestion repo, or silently fall back to direct source fetchers.

Each numeric claim includes canonical/provider symbol, value and available bid/ask/mid/last, prior close and supported move, unit, interval/session, observation/release/ingestion/revision times, source health/authority, artifact reference, citation map, permission, and `llm_numeric_authority=false`.

## Producer Handoff

The ingestion repo does not yet emit this packet. A future ingestion task should produce the schema at `capital_chronicle_content_evidence_packet_v2.schema.json` from a manifest-pinned run, preserving DQR as blocking authority. It should add stable event/headline and official-document exports, explicit market provider symbols, revision timestamps, release-relative moves, source cadence, and claim-level public-use permissions.

## Freshness

`freshness_market_state_v2` computes event, headline, primary-source, market-observation, and database-ingest age against packet `as_of_utc`. Thresholds are configurable by cadence. Straight news, analysis, and explainer modes have different rules; market-sensitive stories require current/latest-session market state.

## Visual Research

`editorial_visual_research_v2` defines a provider-neutral interface. The Google implementation builds the current Gemini Interactions API request using `google_search` with `web_search` and `image_search`. It performs no call by default and reads no credential value.

Search results are candidate discovery only. Acceptance requires containing source page, owner, publication date, caption/context, rights status, dimensions, relevance, recency, duplicate/perceptual hash, and synthetic/manipulated/logo/avatar/thumbnail checks.

Composition normally requires three useful visuals, two evidence dimensions or modalities, a headline-supporting lead, and no more than two assets from one series. Chart metadata declares definition, units, frequency, sample window, transformation owner, calculation, annualization, and partial-period status.

## Editorial Roles

The ordered roles are assignment editor, evidence planner, reporter/writer, quantitative editor, visual editor, copy editor, platform editor, and adversarial final reviewer. The writer sees approved claims only and cannot self-certify. The final reviewer has no publication authority. Missing or malformed structured review blocks.

## Local Rehearsal

```powershell
python -m live_contentops.eight_platform_substack_first_pipeline_v1 `
  --run-id generic_fabric_v2_real_rehearsal_20260711 `
  --output-dir docs\automation\V6_GENERIC_EVIDENCE_FABRIC\generic_fabric_v2_real_rehearsal_20260711 `
  --prepare-generic-fabric `
  --capital-chronicle-root <INGESTION_REPO> `
  --generic-story-request tests\fixtures\generic_fabric\real_cc_wti_analysis_request_v2.json `
  --generic-as-of-utc 2026-07-11T02:00:00Z
```

Expected result: `PASS_GENERIC_FABRIC_FAIL_CLOSED_REHEARSAL`, `publication_eligible=false`, and `public_write_performed=false` while the current DQR/freshness blockers remain.

Fresh legacy oil/Fed preparation and publication are blocked by default. `--allow-legacy-topic-adapter` exists only for explicit regression or separately authorized compatibility work; it is not the generalized product route. Existing-run derivative reconciliation remains available for targeted repair.
