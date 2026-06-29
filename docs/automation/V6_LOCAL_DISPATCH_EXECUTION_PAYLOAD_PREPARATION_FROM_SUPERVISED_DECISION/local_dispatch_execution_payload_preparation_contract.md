# V6 Local Dispatch Execution Payload Preparation from Supervised Decision - Technical Contract

## Purpose

The local dispatch execution payload preparation contract consumes a valid operator supervised dispatch review decision, a valid destination preflight packet, and exact prepared payload files to produce verified local execution-preparation payloads and manifests.

## Core Rules

1. **Create Local Dispatch Execution-Preparation Files Only**: This contract creates local dispatch execution-preparation files only.
2. **Not Live Dispatch Approval**: This contract does not authorize live dispatching.
3. **Not Publication Approval**: This contract does not authorize canonical article publication.
4. **No Platform API Calls**: This contract does not call Substack, Discord, or any platform APIs.
5. **No Credential/Permission Validation**: This contract does not validate credentials, accounts, workspaces, channels, permissions, or scopes.
6. **No Request Artifacts**: This contract does not create endpoint, webhook, API, or browser request artifacts.
7. **Future Live and Supervised Dispatch Gates**: Future live and supervised dispatch gates remain separate and must independently revalidate exact file hashes, destination labels, official docs, credentials, permissions, endpoint allowlists, payload hashes, and explicit operator approvals before performing dispatch execution or live-send operations.
8. **Banned States**:
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
