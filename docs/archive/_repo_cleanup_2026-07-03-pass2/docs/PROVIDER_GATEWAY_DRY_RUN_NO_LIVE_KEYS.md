# Provider Gateway Dry-Run (No Live Keys)

The deterministic local provider gateway (`cc-live-contentops/live_contentops/provider_gateway.py`) simulates standard provider responses without ever engaging real LLMs, APIs, or networks.

### Purpose
- Prepares the LLM integration layer natively within the control plane.
- Defines strictly offline responses asserting `[LOCAL PROVIDER DRY RUN ONLY]`.
- Forces explicit rejection of `provider_call_used = True` and secret values.

### Status of Real Providers
- OpenAI: `FUTURE_ONLY` (Disabled)
- Anthropic: `FUTURE_ONLY` (Disabled)
- Azure OpenAI: `FUTURE_ONLY` (Disabled)
- Local Model: `FUTURE_ONLY` (Disabled)
- Simulator: `SIMULATOR_ONLY` (Enabled)

### Integration
Downstream tasks cannot publish. The output explicitly requires `safe_for_publish = False`.
