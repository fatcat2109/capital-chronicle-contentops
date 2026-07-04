# Pre-Alpha Content Engine (After 0095)

Local-only, deterministic content production-readiness layer. It consumes safe
operator/fixture-supplied content **seeds** already on disk and builds **editorial
packets** containing **draft candidates** for future MANUAL review.

## Hard posture
* No network / provider / LLM / search / platform / credential access.
* No `.env` reads. No posting. No scheduling. No DMs/replies/scraping/metrics.
* No fake Capital Chronicle alpha output. No public-postable or publish-ready output.
* No financial advice / buy-sell-hold / position sizing / price targets / signal language.
* Every output pins: `public_postable=false`, `manual_publish_only=true`,
  `platform_publish_allowed_now=false`, `live_execution_allowed_now=false`,
  `review_required=true`, `forecast_readiness_claim_allowed=false`.

## Components
* `schemas/pre_alpha_content_seed.schema.json`
* `schemas/pre_alpha_draft_candidate.schema.json`
* `schemas/pre_alpha_editorial_packet.schema.json`
* `live_contentops/pre_alpha_content_engine.py`
* CLI: `python -m live_contentops.cli pre-alpha-content-engine-summary`

## Content types
`data_sufficiency`, `forecast_readiness`, `failure_forensics`, `build_in_public`,
`macro_education`, `product_update`, `market_note`.

## Content rules
Each draft candidate either references `source_artifact_ids` OR is marked
`is_general_process_content=true`. Artifact-backed content types
(`data_sufficiency`, `forecast_readiness`, `failure_forensics`) and
`content_source_type=artifact_backed` require source artifact IDs unless flagged
general/process. `artifact_backed` cannot also be general/process.

### market_note guardrails
* must be general/process (educational/general only),
* must display `freshness_label` and `limitations`,
* rejects buy/sell/hold/target/signal language,
* rejects unverified numeric market claims,
* must label proxy-only / missing / degraded data,
* never implies confident forecast readiness when data sufficiency is blocking.

### forecast readiness
A `forecast_readiness_claim_requested=true` seed is blocked unless explicitly
`forecast_readiness_supported_by_source=true`, has source artifact IDs, and is
not blocked by `data_sufficiency_status` (partial/insufficient/missing/proxy_only).

## Validator behavior
`validate_seed` / `validate_draft_candidate` return
`{valid, errors, warnings}` deterministically. `build_editorial_packet`
emits a packet with `guardrail_status="blocked"`, populated `blocked_reasons`,
and NO draft candidates when the seed fails. Safety flags are pinned regardless
of input.

## Guardrail reuse
Forbidden-language and alpha-implication scans are reused from
`live_contentops/grounded_research_brief.py`. A numeric-market-claim scan is
added locally.

## Next task
`TASK_CONTENTOPS_0096_PRE_ALPHA_LLM_PROMPT_PACK_AND_STYLE_PROFILE_V0`
