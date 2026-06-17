# 0174UQ/UR/US Telegram Ledger-Backed Replay-Guarded Supervised Send Proof

Task: `TASK_CONTENTOPS_0174UQ_UR_US_TELEGRAM_LEDGER_BACKED_REPLAY_GUARDED_THIRD_SEND_GATE_BATCH_V0`

Model: `TELEGRAM_RUN_LEDGER_GUARDED_SUPERVISED_SEND_0174UQ_UR_US` version `0174UQ_UR_US_TELEGRAM_RUN_LEDGER_GUARDED_SUPERVISED_SEND_V1`

## Run summary

- Required baseline: `7c6a75f5047a0dad368db773f1fe73fbb426bacf`
- Start HEAD: `7c6a75f5047a0dad368db773f1fe73fbb426bacf`
- Final HEAD: `7c6a75f5047a0dad368db773f1fe73fbb426bacf`
- Origin HEAD: `7c6a75f5047a0dad368db773f1fe73fbb426bacf`
- Baseline matched: `True`
- Credential source: `operator_local_dotenv_file`
- Destination source: `operator_local_dotenv_test_channel`
- Destination binding checksum: `9bf41c5012402b2a`
- Fresh operator gate present: `True`
- Real sendMessage attempted: `yes`
- Real sendMessage succeeded: `yes`
- Live test sequence: `3` (third supervised live test)
- Send outcome class: `telegram_ledger_guarded_supervised_send_ok_redacted`
- Request budget used: `1` of `1`

## Replay guard

- Preflight outcome: `replay_guard_clear_for_new_operator_gate`
- Post-send outcome: `replay_guard_clear_for_new_operator_gate`
- Same payload under fresh gate: `False`
- Exact run replay key: `c9c8c8f9f9962db75f7fcfa9d1e3b7c50895f1abc1d864fd6a273659b2f23ff2`
- Stable payload replay key: `30fcc4f1063bca162e97051e8472d05aa4237776fc65dc1526ad198b2964aa49`

## Redacted provider outcome

- Provider status code class: `provider_code_success_class`
- Response status class: `provider_status_ok_class`
- Redacted message id class: `redacted_message_id_present_class`

## Checksums + ledger

- Request checksum: `4fd24a44889f20ac0cac4d7d05de6a6aac118e7b86d42a89e7cce890a8637136`
- Response checksum: `a7a01463497cb00c0468984027a458e1e85d8525a5869f2afef21307c79e843b`
- Response shape checksum: `d53d7160034bed19335e1f7aa9677eb0fa629594df4c92d26b086d6e7319cce5`
- Previous ledger entry checksum: `961624de5da82a8c8251e5fe8bfcc076194059dec142b2c59ba157f9ea9871cd`
- New ledger entry checksum: `87c35cc8a6d5d10a245d233a7b4fd9675f50c628b9c6fae81713fae939a68065`
- Old ledger manifest checksum: `260cdc315cf6cc5e2ff17a562432e19bde14eb1d22f5039c1ec784bf432b5738`
- New ledger manifest checksum: `7abee0871573e5f7608efe41045f9ea6840cf166c830465c2d08b49063670d83`
- Ledger entry count: `2`
- Appended: `yes`
- Evidence checksum: `49e0c3837fb1a63172f51bd9dc3472db8a6520eb6654632fc75a91a0e7d07dd2`

## Safety proofs

- Stores no token: `True`
- Stores no raw destination: `True`
- Stores no raw response: `True`
- Stores no raw URL: `True`
- Stores no headers: `True`
- Stores no cookies: `True`
- Stores no raw chat id: `True`
- No retry: `True`
- No scheduler: `True`
- No webhook: `True`
- No polling: `True`
- No getUpdates: `True`
- No autonomous reply: `True`
- No media/edit/delete: `True`
- No second send path: `True`

## Next recommended task

`TASK_CONTENTOPS_0174UT_UU_UV_TELEGRAM_OPERATOR_SUPERVISED_SEND_LEDGER_REPLAY_CONSOLE_AND_OUTCOME_RECONCILIATION_BATCH_V0`
