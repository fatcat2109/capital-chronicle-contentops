# V6 Exact Operator Approval Signature Verifier Scaffold Contract

## Purpose

Validate shape of future exact Jim approval declaration without granting approval, without outbox preparation, without dispatch, and without live send.

## Input Eligibility

Input operator approval ledger gate scaffold bundle must be schema version `6.0.0`, task label `TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_LEDGER_GATE_SCAFFOLD_FROM_PAYLOAD_HASH_PREP_HEAVY_BATCH_NO_APPROVAL_NO_SEND_V0`, contain declaration scaffold and ledger shell, have empty blockers, and keep all live, provider, env, credential, browser, network, executable request artifact, public URL, metrics, publication, dispatch, and runtime flags false.

Declaration scaffold exact phrase must be `NOT_APPROVED_IN_THIS_SCAFFOLD`. Ledger shell approval status must be not_approved, with all approval valid-for flags false.

## Future Declaration Template

Template approval mode is `exact_operator_approval_signature_verifier_scaffold_only`. Template scope is `future_payload_hash_approval_signature_shape_only`. Required exact phrase later is `JIM_APPROVES_PAYLOAD_HASHES_FOR_FUTURE_OUTBOX_PREP_ONLY`. Provided phrase now is `NOT_PROVIDED_IN_THIS_SCAFFOLD`.

Approved payload preview IDs, approved payload hashes, and approved platforms must be empty in this scaffold. Approval hash binding, payload hash revalidation, destination binding, credential handle, approval, publication, outbox, dispatch, live send, provider, env, credential value, network, browser, executable request artifact, public URL, and metrics requested flags must be false. Human review must be true. Revocation support must be true. Extra fields fail closed.

## Hard State

`approval_granted_now`, `eligible_for_future_outbox_preparation_task`, `eligible_for_live_send_now`, approval valid-for fields, provider calls, env reads, credential reads, network calls, browser sessions, executable request artifact creation, public URL creation, metrics creation, publication readiness, dispatch allowance, and runtime truth are always false in output.

## Forbidden Content

Endpoint, webhook, secret, channel, account, cookie, session, browser path, public URL, metrics, trading advice, financial advice, signal service, and live-send text fails closed without echoing raw value.