# Review-Only Content Intent V5 Detail Binding Runbook

> [!IMPORTANT]
> This is a deterministic local-only Review-Only Content Intent UI Binding.
> It binds metadata-only fields to the V5 Writer Studio and does not compile publishable copy or edit parameters.

- **Task Label**: `TASK_CONTENTOPS_0175BM_REVIEW_ONLY_INTENT_PACKET_TO_V5_INTENT_DETAIL_BINDING_V0`
- **Source Precheck Hash**: `607f1ab0ab7b10ec10d2b4e0cb55154f0b20127c5ca3c6ce25c38dbeefeb3af6`
- **Intent Packet Hash**: `d2bf5de9b4a6cfc02270638efeff6715f70ad3cb2e80969df35af057fa343f99`
- **Safety Level**: `LOCAL_UI_BINDING_ONLY` (verified local-only, no APIs, keys, or networks accessed)

## UI Binding Architecture

The V5 Operator cockpit binds the Review-Only Content Intent Packet using a read-only TS representation:

1. **TypeScript Data**: [reviewOnlyContentIntentPacket.ts](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/ui/contentops_v5/src/data/reviewOnlyContentIntentPacket.ts) (auto-generated).
2. **Adapter Layer**: [reviewOnlyContentIntentAdapter.ts](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/ui/contentops_v5/src/data/reviewOnlyContentIntentAdapter.ts) maps and types properties.
3. **Cockpit View**: [WriterStudio.tsx](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/ui/contentops_v5/src/views/WriterStudio.tsx) renders the "Review-Only Content Intent" panel below the precheck panel.
4. **Inspector Selectors**: [selectors.ts](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/ui/contentops_v5/src/selectors.ts) exports `selectReviewOnlyIntentItem` and `selectReviewOnlyContentIntentPacket` to populate the Inspector Rail.

## Status Rendering Policy

| Status Value | Color Class | Rationale |
|---|---|---|
| `BLOCKED_OPERATOR_INTENT_INPUT_REQUIRED` | `text-status-blocked` (Red) | Represents active global blocking status |
| `REVIEW_ONLY_INTENT_PENDING_OPERATOR_INPUT` | `text-status-review` (Amber) | Awaiting operator inputs before next gate |
| `BLOCKED_BY_CONTENT_INTENT_GATE` | `text-status-blocked` (Red) | Precedent precheck gate blocking |
| `PENDING_OPERATOR_INPUT` | `text-status-review` (Amber) | Inputs are placeholders, not yet submitted |
| `False` / Locked Flags | `text-status-verified` (Green) | Confirmed inactive safety risk and truth protection |

## Verification Details

* **Exporter Python test**: `tests/test_export_v5_review_only_content_intent_packet.py` verifies byte-identity and correctness.
* **Frontend Tests**: Added `src/test/review_only_content_intent.test.tsx` ensuring panel rendering, packet inspecting, and item selector mapping function correctly. All 133 frontend tests passed.
* **Production Build**: Successfully compiled with `npm run build` (`tsc -b && vite build`).
