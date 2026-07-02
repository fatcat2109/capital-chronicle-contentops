# V6 Discord Supervised Live Preflight Runbook

This runbook guides the operator through verifying the supervised preflight checks for the future live pilot.

## Preflight Steps
1. **Verify inbox content**: Check if any operator source draft is present under `docs/automation/V6_DISCORD_SUPERVISED_LIVE_PREFLIGHT/inbox/`.
2. **Review normalized candidate**: Confirm safety check (`safety_scan = passed`) and validation fields.
3. **Inspect Request Envelope Preview**: Review `request_envelope_preview.json` to ensure the structure is correct and contains no secrets.
4. **Assert safety locks**: Verify `ready_for_dispatch` is `false` and dispatch control remains disabled.

## Safety & Stop Actions
* **Go Phrase validation**: Do not proceed to dispatch if the go phrase file does not exist or has mismatching content.
* **Kill Switch check**: The preflight verification packet requires `kill_switch_active: true`.
