# V6 Canonical Article Studio Editorial Refinement Queue Blocker Report

The following active blockers prevent refinement queue, draft generation, publication, or dispatch operations:

- **article_copy_generation_blocked**: Locked by default dry-run configuration.
- **dispatch_blocked**: Locked by default dry-run configuration.
- **editorial_review_required**: Locked by default dry-run configuration.
- **human_review_required**: Locked by default dry-run configuration.
- **jim_review_required**: Locked by default dry-run configuration.
- **publication_blocked**: Locked by default dry-run configuration.
- **refinement_execution_blocked**: Locked by default dry-run configuration.
- **rendered_draft_missing**: Locked by default dry-run configuration.
- **source_approved_renderer_blocked**: Locked by default dry-run configuration.

## Offline Safety Guarantees
- Raw sources and operators are strictly redacted.
- Live browser orchestration and network writes are disabled.
- Jim's signature is completely absent.