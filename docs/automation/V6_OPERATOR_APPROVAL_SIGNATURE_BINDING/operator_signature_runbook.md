# Operator Signature Binding Runbook

Jim, use this lane only to bind manual approval intent to payload hash `4bcbbf4eeab1bdfa2f3f94b4dbb042877c67efdb515f7feecaac5ffa3a2e71ff`.

## Steps

- [ ] Open `operator_signature_template.json` in `docs/automation/V6_OPERATOR_APPROVAL_SIGNATURE_BINDING/`.
- [ ] Replace `PLACEHOLDER_OPERATOR_ID` with your operator ID.
- [ ] Set `approval_decision` to `APPROVED` only after reviewing exact payload preview.
- [ ] Enter `signed_at` in ISO-8601 format.
- [ ] Keep `valid_for_dispatch=false`.
- [ ] Keep `revoked=false` unless intentionally withdrawing approval intent.
- [ ] Save signed file as local review artifact and re-run validation.

## Hard Stops

> [!IMPORTANT]
> This lane does not make dispatch valid. Dispatch remains blocked until destination binding, approval ledger, outbox creation, supervised dispatch readiness, and kill-switch review all pass.

> [!WARNING]
> Do not add secrets, webhook URLs, cookies, session material, env values, or local machine paths to signature artifact fields.
