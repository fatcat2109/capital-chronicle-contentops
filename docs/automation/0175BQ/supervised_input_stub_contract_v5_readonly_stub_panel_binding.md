# 0175BQ — Supervised Input Stub Contract to V5 Readonly Stub Panel Binding

Task label: `TASK_CONTENTOPS_0175BQ_SUPERVISED_INPUT_STUB_CONTRACT_TO_V5_READONLY_STUB_PANEL_BINDING_V0`

Starting HEAD: `cdf8387397c738c72df444e492611aa5535ddc8d`

## Scope

Bind the 0175BP Supervised Operator Input Stub Contract into V5 Writer Studio as a static, readonly panel.

## Source Packet

- Source packet: `docs/automation/0175BP/operator_input_capture_precheck_to_supervised_input_stub_contract_packet.json`
- Source packet task: `TASK_CONTENTOPS_0175BP_OPERATOR_INPUT_CAPTURE_PRECHECK_TO_SUPERVISED_INPUT_STUB_CONTRACT_V0`
- Source packet hash: `cb0ce2665803ae05a5b407ad002f8277ea246b397c3193bd57b54a36b3a11dd4`

## Generated V5 Data

- Exporter: `tools/export_v5_supervised_input_stub_contract_packet.py`
- Static packet: `ui/contentops_v5/src/data/supervisedInputStubContractPacket.ts`
- Adapter: `ui/contentops_v5/src/data/supervisedInputStubContractAdapter.ts`

## V5 Binding

- Selectors: `ui/contentops_v5/src/selectors.ts`
- Panel: `ui/contentops_v5/src/views/WriterStudio.tsx`
- UI title: `Supervised Input Stub Contract`
- Inspector packet button ID: `btn-inspect-supervised-input-stub-contract`
- Stub item row ID prefix: `supervised-input-stub-row-`

## Readonly / No-Capture Guarantees

The panel displays packet metadata only:

- `current_value: null`
- `placeholder_value: PENDING_OPERATOR_INPUT`
- `capture_enabled_in_this_task: false`
- `editable_in_this_task: false`
- `generated_by_system: false`
- `persistence_enabled: false`
- `validation_enabled: false`
- `future_capture_modes_enabled_in_this_task: false`

No actual input capture, editable UI, persistence, draft eligibility, content generation, live/API/provider/platform behavior, or visual redesign is introduced.

## Stub Surface

The panel exposes:

- global stub status;
- packet/source hashes;
- blocked reasons;
- allowed next step;
- next recommended task;
- field policy cards;
- future capture modes declared only;
- seven stub items;
- forbidden current actions;
- disallowed outputs;
- safety and truth flags.

## Validation Commands

```powershell
python tools/export_v5_supervised_input_stub_contract_packet.py --check
python -m pytest -q tests/test_operator_input_capture_precheck_to_supervised_input_stub_contract.py tests/test_export_v5_supervised_input_stub_contract_packet.py
npm test
npm run build
git diff --check
git ls-files "***pycache***" "*.pyc"
```

## Next Recommended Task

`TASK_CONTENTOPS_0175BR_SUPERVISED_INPUT_STUB_TO_DRAFT_ELIGIBILITY_GATE_PRECHECK_V0`
