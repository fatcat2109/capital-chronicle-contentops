# 0174UW/UX/UY Telegram Operator Cockpit Read Model + Next-Send Precheck

Task: `TASK_CONTENTOPS_0174UW_UX_UY_TELEGRAM_SUPERVISED_SEND_OPERATOR_COCKPIT_READ_MODEL_AND_NEXT_SEND_PRECHECK_BATCH_V0`

Model: `TELEGRAM_OPERATOR_COCKPIT_READ_MODEL_0174UW_UX_UY` version `0174UW_UX_UY_TELEGRAM_OPERATOR_COCKPIT_READ_MODEL_V1`

## Purpose

Deterministic, LOCAL, read-only backend data contract for a future operator cockpit UI. Summarizes ledger state, reconciliation, last send outcome, replay examples, and the single next allowed action before any future supervised send. No network, API, env, or credential read; never classifies anything as live-ready.

## Operational truth rail

- Current ledger count: `2`
- Last send sequence: `3`
- Last send succeeded: `True`
- Reconciliation status: `ledger_reconciliation_ok_count_incremented`
- Current ledger manifest checksum: `7abee0871573e5f7608efe41045f9ea6840cf166c830465c2d08b49063670d83`

## Replay guard panel

- Exact replay example: `blocked_exact_replay_do_not_send`
- Same payload, no gate: `requires_fresh_operator_gate`
- Same payload, fresh gate: `clear_for_manual_supervised_send_gate`
- New payload: `clear_for_manual_supervised_send_gate`
- Current next allowed action: `clear_for_manual_supervised_send_gate`

## Next-send precheck panel

- Candidate status: `no_candidate_selected`
- Precheck outcome class: `next_send_precheck_blocked_missing_candidate`
- Fresh gate required: `True`
- Ledger guard required: `True`
- Operator approval required: `True`
- Payload preview required: `True`
- Destination binding required: `True`
- Credential boundary required: `True`
- Blockers: `['precheck_blocker_missing_candidate']`

## Next-send precheck examples

- `exact_replay` -> `next_send_precheck_blocked_exact_replay` (action `blocked_exact_replay_do_not_send`)
- `same_payload_without_fresh_gate` -> `next_send_precheck_requires_fresh_operator_gate` (action `requires_fresh_operator_gate`)
- `same_payload_with_fresh_gate` -> `next_send_precheck_clear_for_manual_gate` (action `clear_for_manual_supervised_send_gate`)
- `new_payload` -> `next_send_precheck_clear_for_manual_gate` (action `clear_for_manual_supervised_send_gate`)

## Evidence chain panel

- Accepted send proof checksum: `e6ad3376d18cae85248739269f547b65638c2d4f632e40aff4c729eaf350feb3`
- Latest ledger proof checksum: `49e0c3837fb1a63172f51bd9dc3472db8a6520eb6654632fc75a91a0e7d07dd2`
- Replay console checksum: `43d15043bbe350acef9a15a8b3cd337987e279fd76bc32203bfb265d4600fb9d`
- Last response checksum: `a7a01463497cb00c0468984027a458e1e85d8525a5869f2afef21307c79e843b`
- Last request checksum: `4fd24a44889f20ac0cac4d7d05de6a6aac118e7b86d42a89e7cce890a8637136`

## Forbidden affordance panel

- No auto send: `True`
- No scheduler: `True`
- No retry loop: `True`
- No autonomous reply: `True`
- No webhook/polling: `True`
- No live-ready claim: `True`

## Safety proofs

- Network performed: `False`
- Telegram API called: `False`
- Credential read: `False`
- sendMessage executed: `False`
- Read-only cockpit: `True`
- Live ready: `False`
- Valid for live execution: `False`

## Cockpit read model checksum

`3268b95cae278bf761b7bcf6a1b904a960898fdd1491d32a8db1b987db409948`

## Next recommended task

`TASK_CONTENTOPS_0174UZ_VA_VB_TELEGRAM_SUPERVISED_SEND_OPERATOR_COCKPIT_HTML_RENDER_AND_MANUAL_GATE_HANDOFF_BATCH_V0`
