# V6 Live Dispatch Official-Docs and Scope Preflight from Readiness - Technical Contract

## Purpose

The live dispatch official-docs/scope preflight contract consumes a valid live dispatch readiness preflight packet, an explicit operator official-docs/source declaration, and an explicit operator live-scope declaration to produce a verified live dispatch scope preflight packet.

## Core Rules

1. **Create Local Docs/Scope Preflight Packet Only**: This contract creates a local live dispatch scope preflight packet only.
2. **Not Live Dispatch Approval**: This contract does not authorize live dispatching.
3. **Not Publication Approval**: This contract does not authorize canonical article publication.
4. **No Official Docs Fetching**: This contract does not fetch official docs online or verify them via remote endpoints.
5. **No Platform API Calls**: This contract does not call Substack, Discord, or any platform APIs.
6. **No Credential/Permission/Scope Validation**: This contract does not validate credentials, accounts, workspaces, channels, permissions, or API scopes.
7. **No Request Artifacts**: This contract does not create endpoint, webhook, API, or browser request artifacts.
8. **Record Operator-Declared Readiness for Future Separate Gate Only**: This contract only records operator-declared official-docs and scope readiness for a future separately scoped live dispatch gate.
9. **Future Live Gates Requirements**: Future live dispatch modules must independently verify official docs, credentials, permissions, endpoint allowlists, account identity, payload hashes, destination binding, kill switch, request budget, timeout/retry policy, redacted audit fields, and exact operator approval before executing any live-send operations.
10. **Banned States**:
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
