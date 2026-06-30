# V6 Exact Jim Approval Declaration Intake Gate Contract

## Purpose

Approval intake only. Validate explicit Jim approval declaration shape and exact payload hash binding for future outbox preparation only. No provider, no outbox execution, no dispatch, no live send.

## Input Verifier Scaffold Eligibility

Verifier scaffold bundle must use schema version 6.0.0 and source task TASK_CONTENTOPS_V6_EXACT_OPERATOR_APPROVAL_SIGNATURE_VERIFIER_SCAFFOLD_HEAVY_BATCH_NO_APPROVAL_NO_SEND_V0. Future exact approval eligibility must be true. Future outbox preparation eligibility, live-send-now, approval granted now, approval valid-for fields, provider, env, credential, network, browser, executable request artifact, public URL, metrics, publication, dispatch, and runtime flags must be false. Human review must be true. Blockers must be empty. Required phrase later must be JIM_APPROVES_PAYLOAD_HASHES_FOR_FUTURE_OUTBOX_PREP_ONLY. Phrase provided now must be NOT_PROVIDED_IN_THIS_SCAFFOLD.

## Jim Approval Declaration Rules

Mode must be exact_jim_approval_declaration_intake_only. Scope must be payload_hashes_for_future_outbox_preparation_only. Operator must be jim. Required phrase and provided phrase must both equal JIM_APPROVES_PAYLOAD_HASHES_FOR_FUTURE_OUTBOX_PREP_ONLY for accepted declaration. Payload preview IDs, payload hashes, and platforms must be non-empty. Approval hash binding must be true. Payload hashes revalidated now must be true. Revalidation report ID must be non-empty. Destination binding and credential handle must stay absent in this task. Expires-at string is required for accepted declaration.

Publication, outbox, dispatch, and live-send approval flags must remain false. Provider, env, credential value, network, browser, executable request artifact, public URL, and metrics requested flags must remain false. Extra fields fail closed.

## Output Hard State

Default, no-input, and rejected paths keep approval_granted_now false. Accepted explicit input may set approval_granted_now true and eligible_for_future_outbox_preparation_task true only after all validation passes. Accepted approval is only for future outbox preparation, not dispatch, publication, or live send. Eligible live-send-now, publication readiness, dispatch allowed, live-send allowed, provider, env, credential, network, browser, executable request artifact, public URL, metrics, and runtime flags are always false.

## Forbidden Text

Endpoint, webhook, secret, channel, account, cookie, session, browser path, public URL, metrics, trading advice, financial advice, signal service, and live-send text fails closed without echoing raw values.