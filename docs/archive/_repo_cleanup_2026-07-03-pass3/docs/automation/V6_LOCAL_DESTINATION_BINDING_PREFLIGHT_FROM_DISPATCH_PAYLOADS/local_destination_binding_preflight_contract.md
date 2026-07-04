# V6 Local Destination Binding Preflight from Dispatch Payloads - Technical Contract

## Purpose

The local destination binding preflight contract consumes a valid local dispatch payload manifest, the prepared dispatch payload files, and an explicit operator destination binding to produce a verified preflight packet.

## Core Rules

1. **Local Non-Secret Destination Labels Only**: This contract strictly records local non-secret destination labels. It must not contain or persist credentials, tokens, webhooks, channel IDs, account IDs, or platform workspace identifiers.
2. **Not Live Dispatch Approval**: This contract does not approve live dispatching. Supervised dispatch gates remain separate.
3. **Not Publication Approval**: This contract does not authorize canonical article publication.
4. **No Platform API Calls**: This contract does not call Substack, Discord, or any platform APIs.
5. **No Credential/Permission Validation**: This contract does not validate credentials, active logins, active accounts, permissions, channel memberships, or API scopes.
6. **Future Supervised Dispatch Gates**: Future supervised dispatch execution modules remain separate and must independently revalidate exact file hashes, destination binding, official docs, credentials, permissions, and explicit operator approvals before performing dispatch.
7. **Banned States**:
    - `dispatch_execution_payload_created` must remain `false`.
    - `live_send_request_created` must remain `false`.
    - `approval_for_live_dispatch` must remain `false`.
    - `dispatch_allowed` must remain `false`.
    - `approval_for_publication` must remain `false`.
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
