# Next Task Recommendation

I recommend the following next task to begin unblocking the dry-run V6 loop contract sequence by staging real canonical Substack articles.

## Recommended Task details
- **Task Label**: `TASK_CONTENTOPS_V6_SUBSTACK_ARTICLE_REAL_INTAKE_AND_IMPORT_V0`
- **Goal**: Transition from blocked dry-run canonical article validation checks to a real import path that parses and stages actual long-form Markdown drafts from a local source folder.
- **Intended Modules**:
  - `live_contentops/canonical_article_real_intake_v6.py`
  - `tests/test_canonical_article_real_intake_v6.py`
- **Validation Plan**:
  - Run pytest unit tests verifying that real imported articles parse headings, SEO title/description constraints, and update the status of the `approved_canonical_article_available` matrix row.
- **Expected Evidence Packet**:
  - Validation passes on real imported Markdown files.
  - Active draft text loaded into `canonical_article_studio_editor_shell`.
  - Matrix status transition to `approved_canonical_article_available = true`.
