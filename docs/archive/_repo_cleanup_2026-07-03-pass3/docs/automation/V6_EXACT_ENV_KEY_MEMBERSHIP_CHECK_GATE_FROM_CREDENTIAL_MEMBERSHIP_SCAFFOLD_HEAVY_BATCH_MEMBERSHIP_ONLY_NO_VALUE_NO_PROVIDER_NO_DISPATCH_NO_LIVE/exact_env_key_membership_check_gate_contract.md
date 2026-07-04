# V6 Exact Env-Key Membership Check Gate Contract

## Purpose

Membership check only. Exact key names only. This gate may determine whether allowlisted environment key names are present. It is not credential hydration, not credential value read, not account binding proof, not destination binding proof, not dispatch execution, and not live send.

## Allowed Env Boundary

Allowed operation: exact key membership only, equivalent to key_name in os.environ. Allowed output: required key names and boolean present or missing only. Forbidden: values, lengths, prefixes, suffixes, hashes, digests, redacted fragments, env lines, .env paths, credential paths, endpoint, webhook, account, channel, token, payload body, public URL, metrics, provider call, network call, browser, dispatch, publish, or live send.

## Input Eligibility

Input schema version must be 6.0.0. Input task label must be TASK_CONTENTOPS_V6_CREDENTIAL_PRESENCE_MEMBERSHIP_SCAFFOLD_FROM_DESTINATION_BINDING_REVIEW_HEAVY_BATCH_NO_ENV_READ_NO_CREDENTIAL_VALUE_NO_PROVIDER_NO_DISPATCH_NO_LIVE_V0. Status must be ready_for_future_env_membership_check_only. Records must be non-empty. Future env membership check eligibility and human review must be true. Future dispatch execution and live send must be false. Credential presence performed and confirmed must be false. Credential value read, stored, and logged must be false. Env read, .env read, provider, network, browser, executable artifact, endpoint, webhook, channel, account, token, payload body, destination binding, credential handle, public URL, metrics, publication, dispatch, live, and runtime truth must be false. Blockers must be empty.

## Record Rules

Each membership record must be credential_presence_membership_scaffold_only and pending_future_env_membership_check. Required env key name must be allowlisted. Symbolic credential handle and destination binding IDs must use required-later prefixes. All no-value, no-provider, no-network, no-browser, no-dispatch, no-live flags remain false. Required-later and human-review flags remain true.

## Output Rules

Check mode is exact_env_key_membership_check_only. Check status is present_for_future_destination_binding_review_only, missing_required_key, or blocked_not_checked. Required key present and missing are complementary booleans. Credential presence check performed may be true only when the membership check runs. Credential presence confirmed equals the present boolean. Env membership checked may be true only when the exact membership check runs. Env read means value read and remains false.

All value-derived flags remain false: env iteration, value length, prefix, suffix, hash, digest, and redacted fragment. Provider, network, browser, executable artifact, endpoint, webhook, channel, account, token, payload body, destination, credential, public URL, metrics, publication, dispatch, live, and runtime flags remain false.

Eligible for future destination binding proof may be true only when an explicit check ran and every required key is present. Eligible for future dispatch execution remains false. Eligible for live send remains false.