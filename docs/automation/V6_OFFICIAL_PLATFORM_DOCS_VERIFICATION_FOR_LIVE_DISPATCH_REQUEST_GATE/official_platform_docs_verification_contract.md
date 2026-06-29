# V6 Official Platform Docs Verification Gate - Technical Contract

## Purpose

The official platform documentation verification gate consumes a valid local live dispatch request package gate packet, an explicit operator official-docs verification declaration, and a manual docs source summary JSON to emit a verified official platform docs verification packet.

## Core Rules

1. **Create Local Official-Docs Verification Packet Only**: This contract creates a local official-docs verification packet only.
2. **Not Live Dispatch Approval**: This contract does not authorize live dispatching.
3. **Not Publication Approval**: This contract does not authorize canonical article publication.
4. **No Env or .env Reading**: This contract does not read environment variables, process env, or repo env/.env files.
5. **No Platform API Calls**: This contract does not call Substack, Discord, or any platform APIs.
6. **No Platform Verification**: This contract does not validate credentials, accounts, workspaces, channels, permissions, or scopes with providers.
7. **No Request Artifacts**: This contract does not create endpoint, webhook, API, or browser request artifacts.
8. **Future Mapping and Execution Requirements**: Future endpoint mapping and live execution tasks must independently verify account identity, permissions, exact endpoint allowlists, payload hashes, kill switches, request budgets, timeout/retry policies, redacted audit fields, and exact operator approval before executing any live-send operations.
9. **Substack Support Truth Gate**: Substack live API publishing must not be classified as official API supported unless a current official Substack documentation source can be verified from official Substack domains. If unverified, Substack must be set to `unclear_requires_operator_decision` or `unsupported_by_official_docs`, and `live_write_allowed_later` must be false.
10. **Discord Developer Webhook Resource requirement**: Discord support remains supported under `official_webhook_supported_for_required_action` only if backed by official Discord Developer Webhook Resource documentation.
11. **Ineligibility on Unclear/Unsupported Platforms**: If any required platform row is `unsupported_by_official_docs` or `unclear_requires_operator_decision`, the final output packet's `eligible_for_future_endpoint_mapping_gate` must be false.
12. **Banned States**:
    - `live_send_request_created` must remain `false`.
    - `approval_for_live_dispatch` must remain `false`.
    - `dispatch_allowed` must remain `false`.
    - `approval_for_publication` must remain `false`.
    - `platform_variant_generation_allowed` must remain `false`.
    - `outbox_creation_allowed` must remain `false`.
    - `publication_ready` must remain `false`.
    - `approved_canonical_article_available` must remain `false`.
    - `generated_citations_allowed` must remain `false`.
    - `citations_verified` must remain `false`.
    - `public_url` must remain `null`.
    - `public_metrics` must remain `null`.
    - `review_only` must remain `true`.
    - `human_review_required` must remain `true`.
    - `kill_switch_active` must remain `true`.
    - `runtime_truth` must remain `false`.
