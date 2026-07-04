# V6 Credential Presence Membership Scaffold Contract

## Purpose

Credential presence membership scaffold only. This creates symbolic required env-key membership records for a later exact env membership check task. It is not credential hydration, credential presence checking now, account binding proof, destination binding proof, dispatch execution, publication readiness, or live send.

## Input Eligibility

Input must be schema version 6.0.0 and task label TASK_CONTENTOPS_V6_DESTINATION_BINDING_REVIEW_SCAFFOLD_FROM_DISPATCH_GATE_HEAVY_BATCH_NO_ENV_NO_CREDENTIAL_NO_PROVIDER_NO_DISPATCH_NO_LIVE_V0. Status must be ready_for_future_credential_presence_membership_only. Destination binding review records must exist and be non-empty. Future credential presence membership eligibility and human review must be true. Future dispatch execution, live send now, destination binding present, credential handle present, credential value read, env read, provider, network, browser, executable request artifact, endpoint URL, webhook URL, channel ID, account ID, token, payload body, public URL, metrics, publication ready, dispatch allowed, live send allowed, and runtime truth must be false. Blockers must be empty.

## Destination Binding Review Record Eligibility

Each record must be destination_binding_review_scaffold_only and ready_for_future_symbolic_destination_binding_only. Symbolic destination binding ID starts with symbolic_destination_binding_required_later_. Symbolic credential handle ID starts with symbolic_credential_handle_required_later_. Destination binding present, credential handle present, credential value read, env read, provider call, network call, browser session, executable request artifact, endpoint URL, webhook URL, channel ID, account ID, token, payload body, public URL, metrics, publication ready, dispatch allowed, live send allowed, and runtime truth remain false. Required later flags and human review must be true. Source dispatch review ID, source outbox ID, platform, approved payload preview ID, and approved payload hash must be non-empty.

## Membership Record Rules

Mode is credential_presence_membership_scaffold_only. Status is pending_future_env_membership_check. Required key name is symbolic only and allowlisted: DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, SUBSTACK_MANUAL_EXPORT_ONLY, X_MANUAL_EXPORT_ONLY, LINKEDIN_ORG_DEFERRED, TIKTOK_DEFERRED.

No env read, no .env read, no credential value read, no credential value stored, no credential value logged, and no credential presence check now. Endpoint URL, webhook URL, channel ID, account ID, token, payload body, destination binding present, credential handle present, public URL, metrics, publication ready, dispatch allowed, live send allowed, provider call, network call, browser session, executable request artifact, and runtime truth are always false.

## Platform Mapping

- discord maps to DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK.
- telegram maps to TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID as separate symbolic records.
- substack maps to SUBSTACK_MANUAL_EXPORT_ONLY.
- x_manual maps to X_MANUAL_EXPORT_ONLY.
- linkedin_org_deferred maps to LINKEDIN_ORG_DEFERRED.
- tiktok_deferred maps to TIKTOK_DEFERRED.
- Unknown platform fails closed with unsupported_platform_for_membership_scaffold.

## Forbidden Content

Endpoint, webhook, token, channel, account, cookie, session, localStorage, browser profile, provider config, env value, credential value, public URL, metrics, fake metric, fake citation, financial advice, signal-service, live-send text, payload body, executable request artifact, HTTP method, path, header, body, curl, fetch, requests, and browser instructions fail closed without echoing raw values.