# V6 Discord Endpoint Mapping Preflight Gate - Technical Contract

## Purpose

The Discord endpoint mapping preflight gate consumes a valid platform capability lane split packet and an operator Discord endpoint-mapping declaration to emit a deterministic Discord endpoint mapping preflight packet.

## Core Rules

1. **Create Local Discord Endpoint Mapping Preflight Packet Only**: This contract creates a local Discord endpoint mapping preflight packet only.
2. **Not Live Dispatch Approval**: This contract does not authorize live dispatching.
3. **Not Publication Approval**: This contract does not authorize canonical article publication.
4. **No Env or .env Reading**: This contract does not read environment variables, process env, or repo env/.env files.
5. **No Platform API or Webhook Calls**: This contract does not call Substack, Discord, or any platform APIs or webhooks.
6. **No Request Artifacts**: This contract does not create endpoint, webhook, API, or browser request artifacts.
7. **No Persistence of Sensitive Secrets**: This contract does not persist or store full webhook URLs, webhook tokens, channel IDs, account/workspace/app IDs, HTTP bodies, or public URLs.
8. **Discord Value Binding Preparation**: This contract only prepares a future label-only gate for Discord webhook value binding.
9. **Substack Fallback Restriction**: Substack remains routed to manual/browser fallback until official API publishing docs are verified in a future separate task.
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
