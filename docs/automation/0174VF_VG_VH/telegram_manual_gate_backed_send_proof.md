# 0174VF/VG/VH Telegram Manual-Gate-Backed Send Proof

Task: `TASK_CONTENTOPS_0174VF_VG_VH_TELEGRAM_APPROVED_MANUAL_GATE_BACKED_FOURTH_SUPERVISED_SEND_RUNNER_BATCH_V0`

Model: `TELEGRAM_MANUAL_GATE_BACKED_SEND_RUNNER_0174VF_VG_VH` version `0174VF_VG_VH_TELEGRAM_MANUAL_GATE_BACKED_SEND_RUNNER_V1`

## Run summary

- Start HEAD: `6beaa7acbf3dd07df0846f4b73c87232f3154595`
- Final HEAD: `6beaa7acbf3dd07df0846f4b73c87232f3154595`
- Origin HEAD: `6beaa7acbf3dd07df0846f4b73c87232f3154595`
- Live test sequence: `4`
- Real send attempted: `False`
- Send succeeded: `False`
- Send outcome class: `telegram_manual_gate_backed_send_blocked_before_network`
- Blocked reasons: `['approved_payload_checksum_mismatch', 'one_request_object_not_built', 'operator_live_send_not_enabled']`
- Request budget used: `0` of `1`

## Manual gate revalidation

- Manual gate packet checksum: `e0fd313c5e42dda601e6654d0d2a3fb317e37270252ab679ee75aef92ca02561`
- Manual gate revalidated: `False`
- Operator approval outcome: `operator_approval_captured`
- Operator gate class: `operator_gate_present_class`
- Operator gate hash present: `True`
- Operator gate hash matches: `True`
- Approved payload checksum: `2c6964bf24fd43df276c3bd26b8ab10a026427d62543ad7767a62fd13aeeae73`
- Rebuilt send text checksum: `71a314c4be089b617efaf305630b44f21c9a7065bf8f951368bc5150a087d83d`
- Approved destination checksum: `a46373cdd3f2988097306044c92bfc25d0047c7a7a74ce43e1f6980ea0c9a9fc`
- Rebuilt destination checksum: `a46373cdd3f2988097306044c92bfc25d0047c7a7a74ce43e1f6980ea0c9a9fc`

## Replay and ledger

- Preflight replay outcome: `replay_guard_clear_for_new_operator_gate`
- Post replay outcome: `replay_guard_blocked_missing_or_invalid_evidence`
- Ledger count before: `2`
- Ledger count after: `2`
- Previous ledger entry checksum: `87c35cc8a6d5d10a245d233a7b4fd9675f50c628b9c6fae81713fae939a68065`
- New ledger entry checksum: `d8c18857274c062893c27203bb8e7e907f2c9817c48b9c46caa43bba95c2c88a`
- Old ledger manifest checksum: `7abee0871573e5f7608efe41045f9ea6840cf166c830465c2d08b49063670d83`
- New ledger manifest checksum: `7abee0871573e5f7608efe41045f9ea6840cf166c830465c2d08b49063670d83`

## Redacted response

- Provider status code class: `provider_code_unknown_class`
- Response status class: `provider_status_unknown_class`
- Redacted message id class: `redacted_message_id_absent_class`
- Response checksum: `None`
- Response shape checksum: `7ca492c7cb697acc4c691af2bacfd415001fb7967d216eafa9620d8251f45aef`

## Next recommended task

`TASK_CONTENTOPS_0174VI_VJ_VK_TELEGRAM_MANUAL_GATE_APPROVAL_FOR_EXACT_TEST4_PAYLOAD_BATCH_V0`
