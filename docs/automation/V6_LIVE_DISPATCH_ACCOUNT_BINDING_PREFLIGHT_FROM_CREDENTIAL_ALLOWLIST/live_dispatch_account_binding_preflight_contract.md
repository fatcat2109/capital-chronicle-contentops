# V6 Live Dispatch Account Binding Preflight from Credential/Allowlist - Technical Contract

## Purpose

The live dispatch account binding preflight contract consumes a valid credential/allowlist preflight packet and an explicit operator account-binding declaration to produce a verified account-binding preflight packet.

## Core Rules

1. **Create Local Account-Binding Preflight Packet Only**: This contract creates a local account-binding preflight packet only.
2. **Not Live Dispatch Approval**: This contract does not authorize live dispatching.
3. **Not Publication Approval**: This contract does not authorize canonical article publication.
4. **No Env or .env Reading**: This contract does not read environment variables, process env, or repo env/.env files.
5. **No Platform API Calls**: This contract does not call Substack, Discord, or any platform APIs.
6. **No Platform Verification**: This contract does not validate credentials, accounts, workspaces, channels, permissions, or scopes with providers.
7. **No Request Artifacts**: This contract does not create endpoint, webhook, API, or browser request artifacts.
8. **Future Live Gates Requirements**: Future live dispatch modules must independently verify account identity, permissions, official docs, endpoint allowlists, payload hashes, kill switches, budgets, timeout/retry policies, redacted audit fields, and exact operator approvals before executing live-send operations.
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
