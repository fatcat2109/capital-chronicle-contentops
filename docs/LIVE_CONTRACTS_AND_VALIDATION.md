# Live Contracts and Validation

The `cc-live-contentops` sidecar uses explicit data contracts to enforce safety boundaries between authoring, control, and delivery planes.

**Current Status:** All contracts are purely local. No live API, network, or provider integration is active.

### Safety Guarantees
- `human_approval_required` is enforced by validation.
- Live flags (e.g. `network_used`) are rejected if set to true.
- Secret-like fields (e.g. `api_key`) are blocked by the validator.
