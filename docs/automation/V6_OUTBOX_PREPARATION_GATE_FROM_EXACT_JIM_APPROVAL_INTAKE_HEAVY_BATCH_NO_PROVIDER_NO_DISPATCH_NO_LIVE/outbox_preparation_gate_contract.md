# V6 Outbox Preparation Gate Contract

## Purpose

Outbox preparation only. Build local non-executable outbox records from accepted exact Jim approval intake. This is not provider execution, dispatch, publication, or live send.

## Input Eligibility

Input exact Jim approval intake bundle must use schema version 6.0.0 and task label TASK_CONTENTOPS_V6_EXACT_JIM_APPROVAL_DECLARATION_INTAKE_GATE_HEAVY_BATCH_NO_PROVIDER_NO_LIVE_SEND_V0. Approval declaration status must be accepted_for_future_outbox_preparation_only. Validation result must be valid and declaration_supplied true. Approval granted now, approval_valid_for_payload_hashes_only, and eligible_for_future_outbox_preparation_task must be true. Approved preview IDs, hashes, and platforms must be non-empty. Blockers must be empty.

Live-send-now, publication readiness, dispatch allowed, live-send allowed, provider, env, credential, network, browser, executable request artifact, public URL, metrics, and runtime flags must be false. Human review must be true.

## Outbox Record Rules

Records are local non-executable only. Mode is local_outbox_preparation_only. Status is prepared_for_future_dispatch_gate_only. Payload body is not included in this task. Payload hash binding is true. Destination binding and credential handle are required later and not present now. Dispatch, publication, live send, provider, env, credential, network, browser, executable request artifact, public URL, metrics, and runtime flags are false.

Records may contain symbolic approved preview IDs, approved payload hashes, and platforms. Records must not contain endpoint, webhook, token, channel, account, cookie, session, localStorage, browser profile, provider config, env key value, credential value, public URL, metrics, financial advice, signal-service, fake metrics, fake citations, or live-send text.

## Output Hard State

eligible_for_future_dispatch_gate_task may be true only when accepted intake is valid and at least one non-executable outbox record has no blockers. eligible_for_live_send_now, publication_ready, dispatch_allowed, and live_send_allowed are always false. Future dispatch gate required.