# V6 Operator Supervised Dispatch Review Decision from Destination Preflight - Technical Contract

## Purpose

The operator supervised dispatch review decision contract consumes a valid local destination binding preflight packet and an operator supervised dispatch decision to produce a verified supervised dispatch approval-intent packet.

## Core Rules

1. **Record Operator Intent to Prepare Dispatch Execution Only**: This contract records the operator's local intent to allow the next local dispatch-execution preparation step.
2. **Not Live Dispatch Approval**: This contract does not authorize live dispatching.
3. **Not Publication Approval**: This contract does not authorize canonical article publication.
4. **No Platform API Calls**: This contract does not call Substack, Discord, or any platform APIs.
5. **No Credential/Permission Validation**: This contract does not validate credentials, accounts, workspaces, channels, permissions, or API scopes.
6. **Future Supervised Dispatch Preparation and Live Gates**: Future supervised dispatch preparation and live dispatch modules remain separate and must independently revalidate exact file hashes, destination labels, official docs, credentials, permissions, endpoint allowlists, payload hashes, and explicit operator approvals before performing dispatch execution or live-send operations.
7. **Banned States**:
    - `approval_for_live_dispatch` must remain `false`.
    - `dispatch_execution_payload_created` must remain `false`.
    - `live_send_request_created` must remain `false`.
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
