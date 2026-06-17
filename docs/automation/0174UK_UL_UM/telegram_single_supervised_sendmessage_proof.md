# 0174UK/UL/UM Telegram Single Supervised sendMessage Proof

Task: `TASK_CONTENTOPS_0174UK_UL_UM_TELEGRAM_OPERATOR_OWNED_SINGLE_SUPERVISED_SENDMESSAGE_LIVE_GATE_BATCH_V0`

Model: `TELEGRAM_RUN_SINGLE_SUPERVISED_SENDMESSAGE_0174UK_UL_UM` version `0174UK_UL_UM_TELEGRAM_RUN_SINGLE_SUPERVISED_SENDMESSAGE_V1`

## Run summary

- Required baseline: `001fd2feb9edaa78348a48b592114e35cadf1a88`
- Start HEAD: `001fd2feb9edaa78348a48b592114e35cadf1a88`
- Final HEAD: `001fd2feb9edaa78348a48b592114e35cadf1a88`
- Origin HEAD: `001fd2feb9edaa78348a48b592114e35cadf1a88`
- Baseline matched: `True`
- Credential source: `operator_local_dotenv_file`
- Destination source: `operator_local_dotenv_test_channel`
- Destination binding checksum: `9bf41c5012402b2a`
- Destination present (redacted): `yes`
- Real sendMessage attempted: `yes`
- Real sendMessage succeeded: `yes`
- Send outcome class: `telegram_single_supervised_sendmessage_ok_redacted`
- Request budget used: `1` of `1`

## Redacted provider outcome

- Provider status code class: `provider_code_success_class`
- Response status class: `provider_status_ok_class`
- Redacted message id class: `redacted_message_id_present_class`

## Checksums

- Rendered payload checksum: `70ead27e3778418e45d0b08e4a70f280ca8324f2c115203fb40225718bca8755`
- Send text checksum: `ec2a7dbb25dd2e39ed4d09a646191f0e04e815ae2f3df3e040b5fffb32bf0a7d`
- Capability enforcer checksum: `7b4e00881032de9ecb0c9e0623065efb8dc5f67ba66a531e747c661db93802af`
- Request checksum: `d75d00120c333714825396e2579702b9faaaab6f31602b51c8242889a43469ad`
- Response checksum: `None`
- Evidence checksum: `fabd3eb9d6db888539066f3990757c29d3f5fa3484d57038783c86d8af2c97cf`

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
