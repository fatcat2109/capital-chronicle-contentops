# V6 Live Dispatch Readiness Preflight from Execution Payloads - Technical Contract

## Purpose

The live dispatch readiness preflight contract consumes a valid local dispatch execution payload manifest, execution-preparation payloads, and an operator live dispatch readiness declaration to produce a verified readiness preflight packet.

## Core Rules

1. **Create Local Readiness Preflight Packet Only**: This contract creates a local readiness preflight packet only.
2. **Not Live Dispatch Approval**: This contract does not authorize live dispatching.
3. **Not Publication Approval**: This contract does not authorize canonical article publication.
4. **No Platform API Calls**: This contract does not call Substack, Discord, or any platform APIs.
5. **No Credential/Permission Validation**: This contract does not validate credentials, accounts, workspaces, channels, permissions, or API scopes.
6. **No Request Artifacts**: This contract does not create endpoint, webhook, API, or browser request artifacts.
7. **Mark Readiness for Future Separate Gate Only**: This contract only marks readiness for a future separately scoped live dispatch gate.
8. **Future Live Gates Requirements**: Future live dispatch modules must independently revalidate exact official documents, credentials, permissions, endpoint allowlists, payload hashes, destination binding, account identity, kill switch state, and explicit operator approval before executing any live-send operations.
9. **Banned States**:
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
10. **Reject and Defer Fail Closed**: Reject or defer decisions fail closed by emitting clear blockers (`declaration_rejected_or_deferred_reject` / `declaration_rejected_or_deferred_defer`), setting `live_dispatch_readiness_preflight_available=false`, `eligible_for_future_live_dispatch_gate=false`, and `live_dispatch_readiness_preflight_approved=false`.
11. **Notes Requirement**: The declaration `notes` field is required, must be present, and must be a string (empty string is permitted). Missing or non-str notes must block.

