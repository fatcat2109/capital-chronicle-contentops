# V6 Live Dispatch Credential and Allowlist Preflight from Scope - Technical Contract

## Purpose

The live dispatch credential and allowlist preflight contract consumes a valid live dispatch official-docs/scope preflight packet and an explicit operator endpoint allowlist declaration to produce a verified credential/allowlist preflight packet.

## Core Rules

1. **Create Local Credential/Allowlist Preflight Packet Only**: This contract creates a local credential/allowlist preflight packet only.
2. **Not Live Dispatch Approval**: This contract does not authorize live dispatching.
3. **Not Publication Approval**: This contract does not authorize canonical article publication.
4. **Env Presence Check Limits**: Env reading is limited to pure key membership presence-only checks for exact declared key names, only when explicitly enabled via `--check-env-presence`.
5. **Credential Leak Prevention**: Credential values, lengths, prefixes, suffixes, hashes, env lines, and raw env contents are strictly forbidden from output, logs, docs, and tests. No value retrieval (e.g. `.get()`, `__getitem__`) is allowed.
6. **No Platform API Calls**: This contract does not call Substack, Discord, or any platform APIs.
7. **No Credential/Permission Validation**: This contract does not validate credentials with providers.
8. **No Request Artifacts**: This contract does not create endpoint, webhook, API, or browser request artifacts.
9. **Future Live Gates Requirements**: Future live dispatch modules must independently verify account identity, permissions, official docs, endpoint allowlists, payload hashes, kill switches, budgets, timeout/retry policies, redacted audit fields, and exact operator approvals before executing live-send operations.
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
