# TASK_CONTENTOPS_0077_LLM_ASSISTED_DRAFT_REVIEW_PACKET_DRY_RUN_V0

## Task scope
Build a local-only, deterministic, review-only draft review packet workflow for
pre-alpha general/process and grounded-news drafts written OUTSIDE the repo (by
operator / LLM-assisted / Deep Research context). The repo reviews drafts against
the 0076 grounded research brief contract, claim/citation requirements, and
forbidden-language guardrails. No generator, no public-ready copy, no external
calls.

## Files created/changed
- Created: schemas/draft_review_packet.schema.json
- Created: live_contentops/draft_review_packet.py (validator; no external calls)
- Created: fixtures/draft_review_packets/valid_review_only_grounded_news_draft.json
- Created: fixtures/draft_review_packets/invalid_publish_ready_true.json
- Created: fixtures/draft_review_packets/invalid_uncited_current_claim.json
- Created: fixtures/draft_review_packets/invalid_forbidden_signal_language.json
- Created: fixtures/draft_review_packets/invalid_artifact_backed_claim.json
- Created: tests/test_draft_review_packet.py
- Created: docs/DRAFT_REVIEW_PACKET_AFTER_0077.md
- Created: docs/TASK_CONTENTOPS_0077_LLM_ASSISTED_DRAFT_REVIEW_PACKET_DRY_RUN_V0.md (this report)

## What it does
- Defines a JSON Schema (draft-07) contract for review-only draft packets.
- Provides a deterministic local validator that blocks unsafe drafts: forbidden
  market-action/signal language in draft_text and claims, implied Capital
  Chronicle alpha output, missing citations for current/cited claims, citations
  referencing sources not declared from the linked validated brief, forbidden
  claim types, blocked risk levels, any public-post/publish-ready/artifact-backed/
  provider/search/platform flag, and a pass verdict that contradicts blocking
  issues.
- Reuses the 0076 guardrail scanners (forbidden language + alpha implication).
- Ships one valid fixture and four invalid fixtures proving the guardrails.

## What remains disabled
Provider/LLM API calls; network/search; platform APIs; credentials/env reads;
scheduling; live posting; autonomous replies/DMs; browser automation/scraping;
public-postable content; publish-ready content; content generator; auto-approval;
real alpha artifact access; Capital Chronicle core repo reads/writes.

## Boundary statement
This reviews drafts produced outside the repo. LLM assistance is allowed only
outside the repo as manually supplied text/context. The repo reviews
safety/citation/claim quality only; it does not generate final public copy. Jim
must manually rewrite, approve, and post. Artifact-backed Capital Chronicle
content remains blocked until real approved alpha artifacts exist.

## Validation run
- python -m pytest -q: 392 passed.
- python -m pytest -q tests/test_draft_review_packet.py: 18 passed.
- alpha-wait-state-summary / ide-cli-document-bundle-summary: wait-state preserved,
  runtime_capability_added=false.
- git diff --check: clean.
- Suspicious scan over changed files: finance/forbidden terms appear only inside
  guardrail lists, negative fixtures, and docs (BENIGN_GUARDRAIL_TEXT).

## Source-linkage validation
The valid fixture's current_factual_claim (clm_2) cites src_bls_cpi, which is
declared in source_references_used; removing that declaration makes the validator
emit claim_source_not_in_brief, proving source linkage is enforced.

## Final recommendation
The draft review packet contract is in place and enforced by tests. Proceed to the
manual publish and metrics capture guide (docs-only, no scraping/API).

## Next task
TASK_CONTENTOPS_0078_MANUAL_PUBLISH_AND_METRICS_CAPTURE_GUIDE_V0
