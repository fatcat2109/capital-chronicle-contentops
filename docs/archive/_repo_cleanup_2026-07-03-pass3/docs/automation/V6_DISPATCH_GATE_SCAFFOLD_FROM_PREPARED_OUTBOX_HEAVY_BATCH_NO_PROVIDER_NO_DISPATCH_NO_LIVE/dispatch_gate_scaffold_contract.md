# V6 Dispatch Gate Scaffold Contract

## Purpose

Dispatch gate scaffold only. Validate prepared non-executable outbox records and emit local dispatch review records. This is not dispatch execution, provider execution, publication readiness, or live send.

## Input Eligibility

Outbox preparation bundle must use schema version 6.0.0 and task label TASK_CONTENTOPS_V6_OUTBOX_PREPARATION_GATE_FROM_EXACT_JIM_APPROVAL_INTAKE_HEAVY_BATCH_NO_PROVIDER_NO_DISPATCH_NO_LIVE_V0. Status must be prepared_for_future_dispatch_gate_only. Outbox records must exist and be non-empty. Future dispatch gate eligibility must be true. Blockers must be empty. Live-send-now, publication readiness, dispatch allowed, live-send allowed, provider, env, credential, network, browser, executable request artifact, public URL, metrics, and runtime flags must be false.

## Outbox Record Eligibility

Each record must be local_outbox_preparation_only and prepared_for_future_dispatch_gate_only. Payload body is not included. Payload body non-executable and payload hash bound are true. Destination binding and credential handle are required later and not present now. Dispatch, publication, live send, provider, env, credential, network, browser, executable request artifact, public URL, metrics, and runtime flags are false. Preview ID, payload hash, and platform are non-empty.

## Dispatch Review Record Rules

Mode must be dispatch_gate_scaffold_only. Review status must be ready_for_future_destination_binding_review_only. Destination binding later, credential handle later, payload hash revalidation later, and exact operator dispatch go later are required. Dispatch allowed, publication ready, live send allowed, provider, env, credential, network, browser, executable request artifact, public URL, metrics, and runtime flags remain false.

## Hard State

eligible_for_future_destination_binding_task may be true only when all review records validate and blockers are empty. eligible_for_future_dispatch_execution_task remains false. eligible_for_live_send_now, publication_ready, dispatch_allowed, and live_send_allowed are always false. Future dispatch execution task separate.

## Forbidden Content

Endpoint, webhook, token, channel, account, cookie, session, localStorage, browser profile, provider config, env value, credential value, public URL, metrics, fake metric, fake citation, financial advice, signal-service, live-send text, payload body, executable request artifact, HTTP method, path, header, body, curl, fetch, and request pattern text fail closed without echoing raw values.