# TASK_CONTENTOPS_0075_PRE_ALPHA_GENERAL_PROCESS_AND_GROUNDED_NEWS_MASTER_PLAN_DOCS_V0

## Task scope
Docs-only master plan establishing the pre-alpha ContentOps strategy: keep
artifact-backed content in the alpha wait-state, open a tiny manual pre-alpha
general/process content lane, and add a grounded-news/research-context lane that
relies on operator-supplied research briefs only. No runtime capability, no
generator, no provider/search/platform/credential/scheduler/publisher work.

## Files created/changed
- Created: docs/PRE_ALPHA_GENERAL_PROCESS_AND_GROUNDED_NEWS_MASTER_PLAN_AFTER_0075.md
- Created: docs/TASK_CONTENTOPS_0075_PRE_ALPHA_GENERAL_PROCESS_AND_GROUNDED_NEWS_MASTER_PLAN_DOCS_V0.md (this report)

## What remains disabled
Provider/LLM API calls; network/search; platform APIs; credentials/env reads;
scheduling; live posting; autonomous replies/DMs; browser automation/scraping;
public-postable synthetic content; real alpha artifact access; Capital Chronicle
core repo reads/writes. The artifact-backed lane (Lane B) remains BLOCKED. No code
was added; this task is docs-only.

## Two-lane + grounded-news summary
- Lane A (pre_alpha_general_process): real first-party general/process authorship,
  structurally barred from the artifact intake gate, manual review and posting.
- Lane B (future_artifact_backed): blocked until real approved alpha artifacts
  exist; resume path unchanged.
- Grounded-news lane: news is a hook not a signal; operator/Deep Research supplies
  cited sources outside the repo; repo never fetches.

## Validation run
- git status --short: only operator-owned `.gitignore` and the untracked
  project_sources_bundle_AFTER_0074/ folder (both out of scope); new 0075 docs.
- python -m pytest -q: full suite (expected green; docs-only change).
- python -m live_contentops.cli alpha-wait-state-summary: wait-state preserved.
- python -m live_contentops.cli ide-cli-document-bundle-summary: bundle intact,
  runtime_capability_added=false.
- Suspicious scan over changed docs: finance/forbidden terms appear only inside
  explicit forbidden-content lists (BENIGN_GUARDRAIL_TEXT).

## Final recommendation
Proceed with the manual pre-alpha lane and grounded-news research context, built
guardrails-first. Keep artifact-backed content blocked until real alpha artifacts
exist. Next step is the grounded research brief schema/template (still docs/schema
only, no network).

## Exact next task pointer
TASK_CONTENTOPS_0076_LOCAL_GROUNDED_RESEARCH_BRIEF_SCHEMA_TEMPLATE_V0
