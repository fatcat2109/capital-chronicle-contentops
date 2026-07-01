# TASK_CONTENTOPS_0174YO_YP_YQ — V5 Existing Dashboard Integration Recon + Replan

## Scope

Mode: Browser QA + repo recon, read-only product/source recon.

Target corrected by product direction:

- Authoritative target: [ui/contentops_v5](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/ui/contentops_v5)
- Rejected target: [ui/institutional_operator_cockpit_v4](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/ui/institutional_operator_cockpit_v4)
- Rejected target: [cockpit_ui_shell.html](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/docs/automation/0174YL_YM_YN/cockpit_ui_shell.html)

## Repo Baseline

| Check | Result |
|---|---|
| Repo | `A:/Capital Chronicle/tools/cc-live-contentops` |
| Branch | `master` |
| HEAD | `d28cc111e9d65cf161513c1c0a504085ea0cf629` |
| origin/master | `d28cc111e9d65cf161513c1c0a504085ea0cf629` |
| Dirty tree | Pre-existing dirty/untracked files observed; no app/source edits made in this recon |

## Executive Decision

> [!IMPORTANT]
> V5 is authoritative cockpit surface. V4 is frozen fallback/safety reference only.
> The standalone generated static cockpit shell is data-contract/debug evidence only.

V5 already contains the correct institutional cockpit direction:

- Light institutional editorial theme by default.
- Dark evidence/forensic mode in Evidence Vault.
- Left navigation, main work surface, right inspector rail.
- Review-only posture throughout.
- No network, no credential, no provider/platform API, no scheduler.
- Existing fixture + selector architecture suitable for cockpit read model integration.

## Browser QA Evidence

Browser target served locally from [ui/contentops_v5](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/ui/contentops_v5):

- URL: `http://127.0.0.1:5175/`
- Viewport: `1440x900`
- Dev command: `npm run dev -- --host 127.0.0.1 --port 5175`

### Screenshots

![V5 Command Center](C:/Users/bullw/.gemini/antigravity-ide/brain/4613f36c-ae6a-4891-9653-ecf19e65b08d/command_center_default_1781789328735.png)

![V5 Platform Preview X](C:/Users/bullw/.gemini/antigravity-ide/brain/4613f36c-ae6a-4891-9653-ecf19e65b08d/platform_preview_x_1781789338333.png)

![V5 Platform Preview Telegram](C:/Users/bullw/.gemini/antigravity-ide/brain/4613f36c-ae6a-4891-9653-ecf19e65b08d/platform_preview_telegram_1781789343923.png)

![V5 Manual Publish](C:/Users/bullw/.gemini/antigravity-ide/brain/4613f36c-ae6a-4891-9653-ecf19e65b08d/manual_publish_default_1781789352160.png)

![V5 Evidence Vault Dark](C:/Users/bullw/.gemini/antigravity-ide/brain/4613f36c-ae6a-4891-9653-ecf19e65b08d/evidence_vault_dark_1781789381648.png)

Recording:

- `C:/Users/bullw/.gemini/antigravity-ide/brain/4613f36c-ae6a-4891-9653-ecf19e65b08d/v5_recon_1781789317155.webp`

## V5 Surface Findings

### Command Center

Source: [CommandCenter.tsx](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/ui/contentops_v5/src/views/CommandCenter.tsx)

Observed strengths:

- Correct top-level cockpit feel: decision spine + top blocker + pipeline health.
- Next operator action already surfaced via `system_state.next_allowed_action`.
- Blocked live dispatch clear through blocker and validation panels.
- Queue summary already present and routable to content inventory.
- Inspector selection model already handles verdict/blocker details.

Integration gap for 0174YF/YG/YH read model:

- Needs to replace synthetic `system_state` fixture with cockpit read model adapter output.
- Needs explicit sections for `reviewable_now`, `manual_export_queue`, X preview queue, Telegram preview queue, platform registry, blocker state, and evidence index.
- Needs payload hash bindings visible in first fold or inspector rail.

### Platform Payload Preview

Source: [PlatformPayloadPreview.tsx](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/ui/contentops_v5/src/views/PlatformPayloadPreview.tsx)

Observed strengths:

- Strong fit for dry-run chain reconciliation output.
- Tabs already support X and Telegram plus other platforms.
- Safety posture explicit: `dispatchable: false`, `LIVE_DISABLED`, `NO_CREDENTIAL_READ`, `NO_PROVIDER_CALL`, `NO_SCHEDULER`.
- Constraint and payload fields are inspectable.

Integration gap:

- Needs adapter from cockpit packet dry-run preview records into existing `platform_payload_previews` shape or evolved types.
- Needs payload hash and evidence references attached per preview.
- Needs chain reconciliation status and dry-run event references.

### Manual Publish / Metrics

Source data: [fixtures.ts](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/ui/contentops_v5/src/fixtures.ts#L584-L723)

Observed strengths:

- Already models manual publish records, payload refs, approval refs, hashes, manual-only status, no API/scheduler/credential state.
- Strong candidate for manual export review surface integration.
- Supports posted/metrics-entered/blocked states.

Integration gap:

- Needs source data from manual export review packet.
- Needs `manual_action_allowed` from cockpit read model surfaced exactly.
- Needs blocker reason, payload hash, evidence id, platform key normalized to cockpit contract.

### Approval Queue

Source: [ApprovalQueue.tsx](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/ui/contentops_v5/src/views/ApprovalQueue.tsx)

Observed strengths:

- Dispatch gate hierarchy already matches product intent.
- Locked dispatch control visible and disabled.
- Approval packet already includes draft hash, payload hash, evidence sources.

Integration gap:

- Needs cockpit read model to drive gate states and blockers.
- Needs future dispatch language retained as blocked, not hidden.

### Evidence Vault

Source: [EvidenceVault.tsx](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/ui/contentops_v5/src/views/EvidenceVault.tsx)

Observed strengths:

- Correct dark-evidence theme.
- Validation matrix, forbidden scope, provenance, audit trail already match evidence-bound requirement.
- Static guarantees are visible.

Integration gap:

- Needs cockpit evidence index and audit dry-run event records.
- Needs packet hashes and source lineage from [cockpit_read_model_packet.json](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/docs/automation/0174YF_YG_YH/cockpit_read_model_packet.json).

## Code Architecture Findings

### Data Source

V5 currently uses local fixture object:

- [fixtures.ts](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/ui/contentops_v5/src/fixtures.ts)

This is correct integration seam. Do not bolt standalone HTML into V5. Instead, add deterministic cockpit read model mapping into V5 fixture/view-model layer.

### Selection/Inspector Layer

V5 has pure selection builders:

- [selectors.ts](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/ui/contentops_v5/src/selectors.ts)

This is correct detail rail seam. New cockpit entities should get selector builders rather than ad-hoc rendering.

### Theme

V5 theme contract:

- [index.css](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/ui/contentops_v5/src/index.css)

Design should preserve:

- Light default CMS/editorial cockpit theme.
- Dark evidence mode only where forensic context requires it.
- Status-token semantics: verified/review/blocked.
- Existing Inter + JetBrains Mono bundled font posture.

## Static Shell Comparison

Rejected shell:

- [cockpit_ui_shell.html](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/docs/automation/0174YL_YM_YN/cockpit_ui_shell.html)

Why not product target:

- Standalone HTML artifact.
- Does not share V5 state/selection/navigation model.
- Visually diverges from existing light/dark dashboard direction.
- Useful as data-contract/debug evidence only.

V4 comparison:

- [ui/institutional_operator_cockpit_v4](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/ui/institutional_operator_cockpit_v4)

Why not product target:

- Frozen fallback/safety reference.
- Dark/graphite visual direction conflicts with corrected V5 target.
- Do not plan integration against V4.

## Precise Implementation Replan

### Goal

Integrate cockpit read model contract into V5 dashboard without changing safety posture.

### Proposed V5 Integration Components

#### 1. Cockpit read model adapter

Add V5-local adapter that consumes generated cockpit packet JSON and emits V5 `ContentOpsViewModel` compatible slices:

- `system_state`
- `content_items` or new `reviewable_now` collection
- `platform_payload_previews`
- `manual_publish_records`
- `approval_packets`
- `evidence_packets`
- `audit_events`
- `policy_boundaries`
- `internal_alpha_artifacts`

Preferred location:

- `ui/contentops_v5/src/data/cockpitReadModelAdapter.ts`

Adapter must be pure and local-only.

#### 2. Cockpit fixture source

Add checked-in cockpit packet fixture under V5 source or public fixture directory.

Preferred location options:

- `ui/contentops_v5/src/data/cockpitReadModelPacket.ts` for imported static JSON-like object.
- Or `ui/contentops_v5/src/fixtures/cockpit_read_model_packet.json` if Vite JSON import policy accepted.

Need avoid runtime fetch.

#### 3. Command Center mapping

Update [CommandCenter.tsx](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/ui/contentops_v5/src/views/CommandCenter.tsx) to render cockpit packet primary read model:

- Reviewable now.
- Blocked items.
- Platform status separation.
- Next safe operator action.
- Payload/evidence hash bindings.

Keep existing decision spine and blocker pattern.

#### 4. Platform Payload Preview mapping

Update [PlatformPayloadPreview.tsx](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/ui/contentops_v5/src/views/PlatformPayloadPreview.tsx) data model to show:

- X preview queue.
- Telegram preview queue.
- Dry-run reconciliation state.
- Payload hash per item.
- Evidence reference per item.
- `dispatchable: false` unchanged.

#### 5. Manual Publish / Metrics mapping

Use existing manual publish records shape from [fixtures.ts](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/ui/contentops_v5/src/fixtures.ts#L584-L723), but map from cockpit manual export review records.

Required labels:

- Manual action allowed.
- Awaiting manual export.
- Manual metrics entry only.
- No platform API.
- No scheduler.
- No credential read.

#### 6. Evidence Vault mapping

Update [EvidenceVault.tsx](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/ui/contentops_v5/src/views/EvidenceVault.tsx) backing data to include:

- Cockpit evidence index.
- Audit dry-run events.
- Payload hash lineage.
- Packet provenance.

Keep dark evidence mode.

#### 7. Types and tests

Update V5 types and tests to lock:

- No live dispatch affordance.
- No `fetch`, `XMLHttpRequest`, `WebSocket`, platform SDK, credential/env read.
- `dispatchable` never true.
- Cockpit adapter deterministic output.
- Reviewable/manual/export/blocked counts match packet.

Likely files:

- [types.ts](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/ui/contentops_v5/src/types.ts)
- [selectors.ts](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/ui/contentops_v5/src/selectors.ts)
- V5 test files under [ui/contentops_v5](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/ui/contentops_v5)

## Non-Goals / Guardrails

Do not:

- Integrate V4.
- Use standalone generated shell as UI target.
- Add API calls.
- Add credential/env reads.
- Add scheduler or live dispatch.
- Add approval/post/schedule buttons with enabled behavior.
- Call platform/provider APIs.
- Convert V5 into one-off static HTML.

## Verification Plan For Future Implementation

Automated:

```powershell
npm run test
npm run build
```

Repo-level static scans if existing tests support them:

```powershell
python -m pytest tests/test_*v5* tests/test_*cockpit* -q
```

Manual browser QA:

1. Start V5 dev server.
2. Capture Command Center at `1440x900` and `1920x1080`.
3. Capture Platform Payload Preview with X and Telegram tabs.
4. Capture Manual Publish / Metrics.
5. Capture Evidence Vault dark mode.
6. Verify no enabled live-post/schedule/approve dispatch action exists.
7. Verify next safe action and blockers match cockpit read model packet.

## Final Recommendation

Proceed with V5 integration plan. Treat 0174YF/YG/YH cockpit read model as data contract and 0174YL/YM/YN static shell as debug artifact only. V5 is product surface.
