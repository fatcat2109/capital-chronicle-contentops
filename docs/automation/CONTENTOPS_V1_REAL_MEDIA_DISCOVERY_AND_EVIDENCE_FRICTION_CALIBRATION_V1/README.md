# V1 real media discovery and evidence-friction calibration

Status: `PASS`

Operating mode throughout: `KILL_SWITCH`

Public writes: `0`; publishing adapter calls: `0`; `UNKNOWN_WRITE`: `0`.

## Exact real-media proof

The provider-neutral broker generated four story-specific intents for a Strait of Hormuz
shipping explainer and queried both Wikimedia Commons and Openverse with multiple narrow
queries. The committed replay retained 54 resolved candidates, found 17 eligible candidates,
and selected two purposeful assets. The hero is a 2,830×1,880 public-domain documentary
photograph of a vessel passing a tanker after transiting the Strait. Delivery verification used
a 1,920×1,275 Wikimedia derivative of that exact resolved original after the provider
rate-limited original-byte delivery; it is not the 960px discovery thumbnail. A distinct
rights-cleared location photograph was also selected.

The candidate ledger preserves provider, intent, query, original source page, original asset,
creator, reuse basis, license URL where applicable, attribution, dimensions, original/source
hash, perceptual hash, documentary classification, rights status, validation blockers, and
ranking evidence. Unknown rights, invalid/low-resolution candidates, non-raster results, and
search-thumbnail delivery fail closed. One Commons infrastructure-intent request was boundedly
rate-limited; other Commons intents and all Openverse discovery still completed.

Inspectable render:

- `strait_of_hormuz_media_proof/strait_of_hormuz_contextual_article.html`
- `strait_of_hormuz_media_proof/strait_of_hormuz_contextual_article.png`
- `strait_of_hormuz_media_proof/visual_asset_discovery_v1.json`

## Exact newsroom replay

1. Opportunity 1 read 1,024 canonical sidecar rows; all were outside the 48-hour window, so it
   returned `ASSIGNMENT_RETURNED_NO_PUBLICATION` without model or publication calls. This is
   `DATA_NOT_AVAILABLE`, not ceremony.
2. A bounded canonical ingestion-only capture then added 221 deduplicated headlines. Opportunity
   2 accepted 212 current rows, exhausted 11 higher-ranked blocked candidates, and selected rank
   12 using a directly bound ordinary evidence packet. The duplicate claim-dossier requirement
   (`supported_claims_missing`) was removed as policy ceremony. The writer produced an unbound
   reference, so the factual source-binding gate correctly failed closed.
3. Opportunity 3 replayed a 12-candidate prepared state without assignment/routing model calls.
   It selected rank 7, used one ordinary writer call and zero mandatory semantic reviews, then
   rejected the resulting 23-word Reuters-attributed update as `INSUFFICIENT_READER_VALUE`.

The exact remaining blocker taxonomy is in `shadow_opportunity_taxonomy_v1.json`. Across ranked
attempts, unavailable public evidence is reported separately from factual/risk and binding
failures. Removed procedural requirements are recorded separately because they are no longer
active blockers. High-risk corroboration, numeric authority, source binding, fabricated-claim,
rights, reader-value, and write-safety gates were not weakened.

Current-story abstention render:

- `shadow_opportunity_3/current_story_rejected_render.html`
- `shadow_opportunity_3/current_story_rejected_render.png`

## Golden Product replay

The owner-accepted Treasury proof was regenerated with the repeated final conclusion removed.
The cleanup is deterministic and made zero mandatory semantic-review calls. The protected
`v1.0` source fixture was not mutated. The concise EIA proof remains a `CONCISE_UPDATE` regression
fixture only, not the normal article-length standard.
