# V6 Platform Variant Input Contract Queue Blocker Report

The following active blockers prevent platform variant input queue, generation, or dispatch operations:

- **approved_canonical_article_missing**: Locked by default dry-run configuration.
- **destination_binding_missing**: Locked by default dry-run configuration.
- **dispatch_blocked**: Locked by default dry-run configuration.
- **exact_payload_approval_missing**: Locked by default dry-run configuration.
- **human_review_required**: Locked by default dry-run configuration.
- **jim_review_required**: Locked by default dry-run configuration.
- **platform_variant_generation_blocked**: Locked by default dry-run configuration.
- **publication_blocked**: Locked by default dry-run configuration.
- **seo_metadata_missing**: Locked by default dry-run configuration.

## Offline Safety Guarantees
- Raw sources and operators are strictly redacted.
- Platform API and webhook dispatches are disabled.
- Jim's review signature is completely absent.
