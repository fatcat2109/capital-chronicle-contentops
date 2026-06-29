# V6 Platform Capability Lane Split Gate - Technical Contract

## Purpose

The platform capability lane split gate consumes a valid official platform docs verification packet and an operator lane-split declaration to emit a deterministic platform capability lane split packet.

## Core Rules

1. **Create Local Capability Lane Split Packet Only**: This contract creates a local platform capability lane split packet only.
2. **Not Live Dispatch Approval**: This contract does not authorize live dispatching.
3. **Not Publication Approval**: This contract does not authorize canonical article publication.
4. **No Env or .env Reading**: This contract does not read environment variables, process env, or repo env/.env files.
5. **No Platform API Calls**: This contract does not call Substack, Discord, or any platform APIs.
6. **No Request Artifacts**: This contract does not create endpoint, webhook, API, or browser request artifacts.
7. **Discord Webhook Lane Advancement**: Discord may advance only to a future endpoint-mapping preflight step, not live execution.
8. **Substack Fallback Restriction**: Substack remains routed to manual/browser fallback until official API publishing docs are verified in a future separate task.
9. **Ineligibility on Unclear/Unsupported Platforms**: If any platform row is unclear/unsupported, `all_platforms_endpoint_mapping_ready` must be false.
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
