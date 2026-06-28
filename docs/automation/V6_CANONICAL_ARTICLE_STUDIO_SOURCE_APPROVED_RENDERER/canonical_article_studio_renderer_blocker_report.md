# V6 Canonical Article Studio Source Approved Renderer Blocker Report

The following active blockers prevent draft generation, publication, or dispatch operations:

- **article_copy_generation_blocked**: Locked by default dry-run configuration.
- **dispatch_blocked**: Locked by default dry-run configuration.
- **human_review_required**: Locked by default dry-run configuration.
- **jim_review_required**: Locked by default dry-run configuration.
- **publication_blocked**: Locked by default dry-run configuration.
- **real_source_pack_not_approved**: Locked by default dry-run configuration.
- **renderer_execution_blocked**: Locked by default dry-run configuration.
- **runtime_operator_approval_missing**: Locked by default dry-run configuration.
- **source_approval_hash_missing**: Locked by default dry-run configuration.

## Offline Safety Guarantees
- Raw sources and operators are strictly redacted.
- Live browser orchestration and network writes are disabled.
- Jim's signature is completely absent.