# V6 Destination Binding Proof Scaffold Operator Runbook No Value No Provider No Dispatch No Live

Local deterministic proof join only. Symbolic destination binding only. Symbolic credential handle only. No values. No env reads. No .env reads. No credential files. No provider. No network. No browser. No dispatch. No live send.

## Flow

1. Start with an accepted exact env-key membership gate bundle.
2. Confirm schema version and task label.
3. Confirm records use exact_env_key_membership_check_only.
4. Confirm key names are allowlisted.
5. Confirm membership was checked and the required key is present.
6. Emit symbolic destination binding proof records only.
7. Keep missing or unchecked records fail closed.
8. Keep future dispatch execution false.
9. Keep live send false.

## Required Later

- Future credential handle membership proof task separate.
- Future dispatch execution task separate.
- Exact operator dispatch go separate.
- Manual fallback and kill switch separate.

## Prohibited

- Credential hydration or value reads.
- Env value reads or env iteration.
- .env, secret stores, or browser state.
- Provider, network, browser, or API calls.
- Executable request artifacts.
- Endpoint, webhook, channel, account, token, payload body, public URL, or metrics.
- Publication, dispatch, or live send.