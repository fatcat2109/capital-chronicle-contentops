# Next Task Recommendation

I recommend the following next implementation task to initiate the local intake pipeline for operator-provided canonical Substack articles.

## Recommended Task Details
- **Task Label**: `TASK_CONTENTOPS_V6_CANONICAL_ARTICLE_REVIEW_CANDIDATE_INTAKE_FROM_MARKDOWN_V0`
- **Goal**: Import operator-provided local Markdown drafts into the workspace as review candidates only.
- **Intended Modules**:
  - `live_contentops/canonical_article_intake_v6.py`
  - `tests/test_canonical_article_intake_v6.py`
- **Required Status Language / State Machine Constraints**:
  - `canonical_article_review_candidate_available = true`
  - `approved_canonical_article_available = false`
  - `human_review_required = true`
  - `publication_ready = false`
  - `dispatch_allowed = false`
- **Safety Boundaries**:
  - No transition to approved or public-ready states.
  - No live, LLM provider, browser automation, environment read, or network requests allowed.
- **Expected Outputs**:
  - Review-candidate packets containing parsed headers and text content staged on disk for subsequent human review, not public-ready or approved article records.
