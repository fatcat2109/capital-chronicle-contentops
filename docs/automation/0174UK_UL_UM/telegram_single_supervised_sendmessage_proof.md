# 0174UK/UL/UM Telegram Single Supervised sendMessage Proof

Task: `TASK_CONTENTOPS_0174UK_UL_UM_TELEGRAM_OPERATOR_OWNED_SINGLE_SUPERVISED_SENDMESSAGE_LIVE_GATE_BATCH_V0`

Model: `TELEGRAM_RUN_SINGLE_SUPERVISED_SENDMESSAGE_0174UK_UL_UM` version `0174UK_UL_UM_TELEGRAM_RUN_SINGLE_SUPERVISED_SENDMESSAGE_V1`

## Run summary

- Required baseline: `001fd2feb9edaa78348a48b592114e35cadf1a88`
- Start HEAD: `db989e0f01c47e6a638715107d31f9b68f7fb8be`
- Final HEAD: `db989e0f01c47e6a638715107d31f9b68f7fb8be`
- Origin HEAD: `db989e0f01c47e6a638715107d31f9b68f7fb8be`
- Baseline matched: `False`
- Credential source: `operator_local_dotenv_file`
- Destination source: `operator_local_dotenv_test_channel`
- Destination binding checksum: `9bf41c5012402b2a`
- Destination present (redacted): `yes`
- Real sendMessage attempted: `yes`
- Real sendMessage succeeded: `yes`
- Live test sequence: `2` (second supervised live test)
- Send outcome class: `telegram_single_supervised_sendmessage_ok_redacted`
- Request budget used: `1` of `1`

## Redacted provider outcome

- Provider status code class: `provider_code_success_class`
- Response status class: `provider_status_ok_class`
- Redacted message id class: `redacted_message_id_present_class`

## Checksums

- Rendered payload checksum: `ea155bbad188206e27da40fef1ed3893209fbf08fa0b8cfb7d118803bc1e7224`
- Send text checksum: `81d5bea0acc1a3e7cc430c6dd1bac8aeb3cbba825d6b538be03a3d976998799e`
- Capability enforcer checksum: `7b4e00881032de9ecb0c9e0623065efb8dc5f67ba66a531e747c661db93802af`
- Request checksum: `3972200a751f6582da3b5f3262a0d9a476f6eda6d6d6a88d302dbb95d36200ff`
- Response checksum: `02fe90ae27a138941bbacb198487d2712cd5248e970d8f95dc8b978034d6752e`
- Evidence checksum: `e6ad3376d18cae85248739269f547b65638c2d4f632e40aff4c729eaf350feb3`

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

`TASK_CONTENTOPS_0174UN_UO_UP_TELEGRAM_OPERATOR_SUPERVISED_SEND_OUTCOME_LEDGER_AND_REPLAY_GUARD_BATCH_V0`
