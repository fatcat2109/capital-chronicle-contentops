# TASK_CONTENTOPS_0060_GROUNDED_RESEARCH_CONTEXT_AND_SEO_METADATA_CONTRACT_V0

## Objective
Build a local-only grounded research context contract and SEO/hashtag metadata pack v0 for future LLM/editorial/planning runs. Note: The previous task (0059) pointed to a narrow hashtag/SEO task. The operator has expanded this to a grounded-research + SEO metadata contract because future LLM/editorial/planning runs should receive grounded-search context when useful. This is recorded here as an explicit upgrade, not scope drift.

## Capabilities Implemented
- **Grounded Research Context**: Defined a deterministic local data structure (`live_contentops/grounded_research.py`) to manage source items, freshness windows, cost budgets, and citation requirements.
- **SEO/Hashtag Metadata Pack**: Defined `live_contentops/seo_metadata.py` to generate and guardrail search-intent targeting without integrating live platform APIs.
- **Cost Policy**: The `grounded_research.py` contract explicitly specifies searching once per content packet and caching.
- **Guardrails**:
  - Missing sources on current-event claims trigger block/warnings.
  - SEO metadata containing risky terms (e.g., "buy signal guaranteed") are caught and added to the `blockers` array.
  - Fixture outputs strictly yield `not_public_postable_reason`.

## Testing & Validation
- Tests verify current-event claims missing citations are explicitly flagged.
- Validated SEO blockers correctly trigger when financial advice keywords exist.
- Confirmed no live search API or browser automation imports were injected.

## Suspicious Scan
The final post-change scan for networking, credentials, search API integrations, platform APIs, and publishing engines remained clean. Matches mapped solely back to negative assertions and testing frameworks.

## Next Phase
`TASK_CONTENTOPS_0061_GROUNDED_LLM_PROMPT_INJECTION_AND_CITATION_GUARDRAIL_V0`
