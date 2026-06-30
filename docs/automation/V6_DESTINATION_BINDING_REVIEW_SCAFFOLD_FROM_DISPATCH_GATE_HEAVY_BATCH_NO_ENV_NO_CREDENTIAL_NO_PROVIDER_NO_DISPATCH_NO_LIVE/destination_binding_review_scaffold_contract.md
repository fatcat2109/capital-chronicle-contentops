# V6 Destination Binding Review Scaffold Contract

## Purpose

Destination binding review scaffold only. This creates symbolic destination binding and symbolic credential handle placeholder requirements for a later credential presence membership task. It is not credential hydration, account binding proof, destination binding, dispatch execution, publication readiness, or live send.

## Input Eligibility

Dispatch gate scaffold bundle must use schema version 6.0.0 and task label TASK_CONTENTOPS_V6_DISPATCH_GATE_SCAFFOLD_FROM_PREPARED_OUTBOX_HEAVY_BATCH_NO_PROVIDER_NO_DISPATCH_NO_LIVE_V0. Status must be ready_for_future_destination_binding_review_only. Dispatch review records must exist and be non-empty. Destination binding later, credential handle later, payload hash revalidation later, exact operator dispatch go later, redacted audit later, manual fallback later, kill switch later, future destination binding task eligibility, and human review must be true. Future dispatch execution, live send now, publication ready, dispatch allowed, live send allowed, provider, env, credential value, network, browser, executable request artifact, public URL, metrics, and runtime flags must be false. Blockers must be empty.

## Dispatch Review Record Eligibility

Each dispatch review record must be dispatch_gate_scaffold_only and ready_for_future_destination_binding_review_only. Destination binding and credential handle must not be present. Destination binding later, credential handle later, payload hash revalidation later, exact operator dispatch go later, and human review are required. Dispatch, publication, live send, provider, env, credential value, network, browser, executable request artifact, public URL, metrics, and runtime flags remain false. Source outbox record ID, platform, approved payload preview ID, and approved payload hash must be non-empty.

## Destination Binding Review Record Rules

Mode must be destination_binding_review_scaffold_only. Review status must be ready_for_future_symbolic_destination_binding_only. Symbolic destination binding ID starts with symbolic_destination_binding_required_later_. Symbolic credential handle ID starts with symbolic_credential_handle_required_later_. Destination binding present, credential handle present, credential value read, env read, provider call, network call, browser session, executable request artifact, endpoint URL, webhook URL, channel ID, account ID, token, payload body, public URL, metrics, publication ready, dispatch allowed, live send allowed, and runtime truth are always false. Human review is always required.

## Hard State

eligible_for_future_credential_presence_membership_task may be true only when all destination binding review records validate and blockers are empty. eligible_for_future_dispatch_execution_task remains false. eligible_for_live_send_now is always false. This task does not read env, check credential presence, bind an account, bind a destination, dispatch, publish, or live send.

## Forbidden Content

Endpoint, webhook, token, channel, account, cookie, session, localStorage, browser profile, provider config, env value, credential value, public URL, metrics, fake metric, fake citation, financial advice, signal-service, live-send text, payload body, executable request artifact, HTTP method, path, header, body, curl, fetch, requests, and browser instructions fail closed without echoing raw values.
