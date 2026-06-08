# TASK_CONTENTOPS_0076_LOCAL_GROUNDED_RESEARCH_BRIEF_SCHEMA_TEMPLATE_V0

## Task scope
Build the local-only schema/template foundation for the Grounded News / Research
Context Lane documented in 0075/0075A. Deterministic, repo-local validation of
operator-supplied grounded research briefs. No network/search/provider/LLM/
platform/credential access, no content generator, no public-ready output.

## Files created/changed
- Created: schemas/grounded_research_brief.schema.json
- Created: live_contentops/grounded_research_brief.py (validator; no external calls)
- Created: fixtures/grounded_research_briefs/valid_minimal_grounded_news_context.json
- Created: fixtures/grounded_research_briefs/invalid_missing_source_url.json
- Created: fixtures/grounded_research_briefs/invalid_market_signal_claim.json
- Created: fixtures/grounded_research_briefs/invalid_artifact_backed_claim_without_artifact.json
- Created: tests/test_grounded_research_brief_schema.py
- Created: docs/GROUNDED_RESEARCH_BRIEF_SCHEMA_AFTER_0076.md
- Created: docs/TASK_CONTENTOPS_0076_LOCAL_GROUNDED_RESEARCH_BRIEF_SCHEMA_TEMPLATE_V0.md (this report)

## What it does
- Defines a JSON Schema (draft-07) contract for operator-supplied grounded
  research briefs.
- Provides a deterministic local validator that blocks unsafe/missing/unsupported
  research claims (forbidden market-action language, blocked claim types/risk,
  missing source URLs/dates, missing citations, implied Capital Chronicle alpha
  output, and any provider/search/platform/public-post/publish-ready flags).
- Ships one valid fixture and three invalid fixtures proving the guardrails.

## What remains disabled
Provider/LLM API calls; network/search; platform APIs; credentials/env reads;
scheduling; live posting; autonomous replies/DMs; browser automation/scraping;
public-postable synthetic content; real alpha artifact access; Capital Chronicle
core repo reads/writes. No fetcher and no content generator were added. The
validator only reads brief structures already on disk.

## Boundary statement
This is operator-supplied/manual research context only. The repo does not fetch
sources. The schema validates briefs; it does not generate final social copy. All
public posting remains manual by Jim. Artifact-backed Capital Chronicle content
remains blocked until real approved alpha artifacts exist.

## Validation run
- python -m pytest -q: full suite green.
- python -m pytest -q tests/test_grounded_research_brief_schema.py: 14 passed.
- alpha-wait-state-summary / ide-cli-document-bundle-summary: wait-state preserved,
  runtime_capability_added=false.
- Suspicious scan over changed files: finance/forbidden terms appear only inside
  forbidden-language guardrail lists, negative fixtures, and docs
  (BENIGN_GUARDRAIL_TEXT).

## Final recommendation
The grounded research brief contract is in place and enforced by tests. Proceed to
the LLM-assisted draft review packet (dry-run, review-only, still no generator and
no public copy).

## Next task
TASK_CONTENTOPS_0077_LLM_ASSISTED_DRAFT_REVIEW_PACKET_DRY_RUN_V0
