// Capital Chronicle ContentOps V5 — selection object builders.
// Single source of truth for inspector content + per-view default selection.
// Pure functions over local fixture data. No network, storage, or credentials.

import { viewModel } from './fixtures';
import { preflightBundlePacket } from './data/preflightBundlePacket';
import { manualExportPilotVerificationPacket } from './data/manualExportPilotVerificationPacket';
import { operatorReviewQueuePacket } from './data/operatorReviewQueuePacket';
import { manualPilotTrailReconciliationPacket } from './data/manualPilotTrailReconciliationPacket';
import type {
  AiWriterOutput,
  ArtifactEligibilityCheck,
  Blocker,
  CitationCheck,
  ClaimRiskItem,
  ContentItem,
  DispatchGate,
  DraftInspection,
  LimitationCheck,
  ManualPublishChecklistItem,
  ManualPublishRecord,
  MediaAsset,
  MetricsSnapshot,
  NoSignalCheck,
  PayloadConstraint,
  PlatformPayloadPreview,
  SeoKeywordGroup,
  SelectableObject,
  SystemState,
  ValidationPass,
  ViewId,
  LocalPreflightBundlePacket,
  LocalPreflightBundlePlatformState,
  LocalPreflightBundleRoomBindingPrecheck,
  LocalPreflightBundleSourceRef,
  V5ManualCopyBlock,
  V5ManualExportChecklistItem,
  V5ManualExportPilotVerificationPacket,
  V5ManualExportPlatformTarget,
  V5ReviewItem,
  V5TrailEntry,
  V5OperatorReviewQueueManualPilotTrailPacket,
  V5ManualPilotTrailReconciliationPacket,
  V5LifecycleStep,
  V5PlaceholderField,
  V5ManualPilotTrailReconciliationAuditPacket,
} from './types';


export const LANE_LABEL: Record<string, string> = {
  A_pre_alpha: 'A · Pre-alpha',
  B_grounded_news: 'B · Grounded news',
  C_artifact_backed: 'C · Artifact-backed',
};

export function selectSystemVerdict(s: SystemState): SelectableObject {
  return {
    kind: 'system_verdict',
    id: s.baseline_ref,
    title: s.verdict,
    fields: [
      { label: 'Status', value: s.verdict, status: s.verdict_status },
      { label: 'Baseline', value: s.baseline_ref, mono: true },
      { label: 'Provenance', value: s.build_provenance, mono: true },
      { label: 'Next', value: s.next_allowed_action },
    ],
  };
}

export function selectBlocker(b: Blocker): SelectableObject {
  return {
    kind: 'blocker',
    id: b.id,
    title: b.label,
    fields: [
      { label: 'Severity', value: b.severity, status: b.severity },
      { label: 'ID', value: b.id, mono: true },
      { label: 'Detail', value: b.detail },
    ],
  };
}

export function selectContentItem(it: ContentItem): SelectableObject {
  return {
    kind: 'content_item',
    id: it.id,
    title: it.title,
    fields: [
      { label: 'Lane', value: LANE_LABEL[it.lane] },
      { label: 'Type', value: it.content_type, mono: true },
      { label: 'Status', value: it.status_label, status: it.status },
      { label: 'Approval', value: it.approval_state },
      { label: 'Platform', value: it.platform_fit.join(', ') || '—' },
      { label: 'Owner', value: it.owner },
      { label: 'Updated', value: it.last_updated, mono: true },
      { label: 'Evidence', value: it.evidence_id, mono: true },
    ],
  };
}

export function selectAiVariant(v: AiWriterOutput): SelectableObject {
  return {
    kind: 'ai_variant',
    id: v.variant_id,
    title: `${v.platform} · ${v.style_mode}`,
    fields: [
      { label: 'Platform', value: v.platform },
      { label: 'Audience', value: v.audience_mode },
      { label: 'Style', value: v.style_mode },
      { label: 'Hook', value: v.hook_type },
      { label: 'Editorial', value: String(v.editorial_score), mono: true },
      { label: 'SEO', value: String(v.seo_score), mono: true },
      { label: 'Platform fit', value: String(v.platform_fit_score), mono: true },
      { label: 'Keywords', value: v.seo_keywords.join(', ') || '—' },
      { label: 'Guardrail', value: v.guardrail_status, status: v.guardrail_status },
      {
        label: 'Review',
        value: v.human_review_required ? 'required' : 'no',
        status: 'review',
      },
      { label: 'Limitations', value: v.limitations_preserved ? 'preserved' : 'missing', status: v.limitations_preserved ? 'verified' : 'blocked' },
      { label: 'Sources', value: v.source_references_preserved ? 'preserved' : 'missing', status: v.source_references_preserved ? 'verified' : 'blocked' },
      { label: 'Postable', value: 'no', status: 'blocked' },
      { label: 'Publish', value: 'publish_ready: false', mono: true, status: 'blocked' },
      { label: 'Reason', value: v.not_public_postable_reason },
    ],
  };
}

export function selectSeoKeywordGroup(g: SeoKeywordGroup): SelectableObject {
  return {
    kind: 'seo_keyword_group',
    id: g.id,
    title: g.label,
    fields: [
      { label: 'Intent', value: g.intent },
      { label: 'SEO score', value: String(g.seo_score), mono: true },
      { label: 'Status', value: g.status, status: g.status },
      { label: 'Keywords', value: g.keywords.join(', ') || '—' },
      { label: 'Advisory', value: 'Advisory only · not a publish gate' },
    ],
  };
}

export function selectClaimRiskItem(c: ClaimRiskItem): SelectableObject {
  return {
    kind: 'claim_risk_item',
    id: c.id,
    title: c.label,
    fields: [
      { label: 'Class', value: c.classification },
      { label: 'Severity', value: c.severity, status: c.severity },
      { label: 'ID', value: c.id, mono: true },
      { label: 'Detail', value: c.detail },
    ],
  };
}

export function selectCitationCheck(c: CitationCheck): SelectableObject {
  return {
    kind: 'citation_check',
    id: c.id,
    title: c.label,
    fields: [
      { label: 'Source', value: c.source_ref, mono: true },
      { label: 'Status', value: c.status, status: c.status },
      { label: 'Detail', value: c.detail },
    ],
  };
}

export function selectLimitationCheck(c: LimitationCheck): SelectableObject {
  return {
    kind: 'limitation_check',
    id: c.id,
    title: c.label,
    fields: [
      { label: 'Status', value: c.status, status: c.status },
      { label: 'Detail', value: c.detail },
    ],
  };
}

export function selectNoSignalCheck(c: NoSignalCheck): SelectableObject {
  return {
    kind: 'no_signal_check',
    id: c.id,
    title: c.label,
    fields: [
      { label: 'Status', value: c.status, status: c.status },
      { label: 'Detail', value: c.detail },
    ],
  };
}

export function selectArtifactEligibility(
  c: ArtifactEligibilityCheck,
): SelectableObject {
  return {
    kind: 'artifact_eligibility_check',
    id: c.id,
    title: c.label,
    fields: [
      { label: 'Status', value: c.status, status: c.status },
      { label: 'Detail', value: c.detail },
    ],
  };
}

export function selectDraftInspection(d: DraftInspection): SelectableObject {
  return {
    kind: 'draft_inspection',
    id: d.id,
    title: d.title,
    fields: [
      { label: 'Draft', value: d.draft_id, mono: true },
      { label: 'Readiness', value: d.approval_readiness, status: d.approval_readiness_status },
      { label: 'Review', value: d.human_review_required ? 'required' : 'no', status: 'review' },
      { label: 'Citations', value: `${d.citation_checks.length} checks` },
      { label: 'Claim risks', value: `${d.claim_risk_items.length} items` },
      { label: 'No-signal', value: `${d.no_signal_checks.length} checks` },
      { label: 'Artifact', value: `${d.artifact_eligibility_checks.length} checks` },
      { label: 'Publish', value: 'publish_ready: false', mono: true, status: 'blocked' },
    ],
  };
}

export function selectMediaAsset(m: MediaAsset): SelectableObject {
  return {
    kind: 'media_asset',
    id: m.id,
    title: m.name,
    fields: [
      { label: 'Kind', value: m.kind, mono: true },
      { label: 'Alt text', value: m.alt_text },
      { label: 'Rights', value: m.rights_label, status: m.rights_status },
      { label: 'Selected', value: m.selected ? 'yes' : 'no' },
      { label: 'Constraints', value: m.platform_constraints.join(' · ') },
    ],
  };
}

export function selectDispatchGate(g: DispatchGate): SelectableObject {
  return {
    kind: 'dispatch_gate',
    id: g.id,
    title: g.label,
    fields: [
      { label: 'Status', value: g.status, status: g.status },
      { label: 'Cleared', value: g.cleared ? 'yes' : 'no', mono: true },
      { label: 'Gate', value: g.id, mono: true },
      { label: 'Reason', value: g.detail },
    ],
  };
}

export function selectValidation(
  v: ValidationPass,
  packetId: string,
): SelectableObject {
  return {
    kind: 'validation',
    id: v.id,
    title: v.label,
    fields: [
      { label: 'Status', value: v.status, status: v.status },
      { label: 'Detail', value: v.detail },
      { label: 'Packet', value: packetId, mono: true },
    ],
  };
}

export function selectPlatformPayloadPreview(
  p: PlatformPayloadPreview,
): SelectableObject {
  return {
    kind: 'platform_payload_preview',
    id: p.id,
    title: `${p.platform} · payload preview`,
    fields: [
      { label: 'Platform', value: p.platform },
      { label: 'Format', value: p.format_label },
      { label: 'Source', value: p.source_draft_id, mono: true },
      { label: 'Fit', value: p.fit_summary, status: p.fit_status },
      { label: 'Live', value: p.live_status, mono: true, status: 'blocked' },
      { label: 'Credential', value: p.credential_status, mono: true, status: 'blocked' },
      { label: 'Provider', value: p.provider_status, mono: true, status: 'blocked' },
      { label: 'Media', value: p.media_note },
      { label: 'Dispatch', value: 'dispatchable: false', mono: true, status: 'blocked' },
      { label: 'Reason', value: p.not_dispatchable_reason },
    ],
  };
}

export function selectPayloadConstraint(
  c: PayloadConstraint,
  platform: string,
): SelectableObject {
  return {
    kind: 'payload_constraint',
    id: c.id,
    title: c.label,
    fields: [
      { label: 'Platform', value: platform },
      { label: 'Limit', value: c.limit, mono: true },
      { label: 'Actual', value: c.actual, mono: true },
      { label: 'Status', value: c.status, status: c.status },
      { label: 'Detail', value: c.detail },
    ],
  };
}

export function selectManualPublishRecord(
  r: ManualPublishRecord,
): SelectableObject {
  const allowedAction =
    r.stage === 'blocked'
      ? 'None — blocked candidate'
      : 'Record manual post URL + timestamp (local draft only)';
  return {
    kind: 'manual_publish_record',
    id: r.id,
    title: `${r.platform} · manual publish`,
    fields: [
      { label: 'Platform', value: r.platform },
      { label: 'Stage', value: r.stage_label, status: r.stage_status },
      { label: 'Source', value: r.source_draft_id, mono: true },
      { label: 'Payload', value: r.payload_ref, mono: true },
      { label: 'Payload #', value: r.payload_hash, mono: true },
      { label: 'Approval', value: r.approval_packet_ref, mono: true },
      { label: 'Approval #', value: r.approval_packet_hash, mono: true },
      { label: 'Manual URL', value: r.manual_url || '(not posted)', mono: true },
      { label: 'Posted', value: r.published_at || '(not posted)', mono: true },
      { label: 'Metrics', value: `${r.metrics.length} snapshot(s)` },
      { label: 'Audit', value: r.audit_state, status: r.audit_status },
      { label: 'Allowed', value: allowedAction },
      { label: 'Blocked', value: r.blocked_reason || 'none' },
      { label: 'Live', value: r.live_status, mono: true, status: 'blocked' },
      { label: 'Platform API', value: r.platform_api_status, mono: true, status: 'blocked' },
      { label: 'Credential', value: r.credential_status, mono: true, status: 'blocked' },
      { label: 'Scheduler', value: r.scheduler_status, mono: true, status: 'blocked' },
      { label: 'Autonomous', value: r.autonomous_status, mono: true, status: 'blocked' },
      { label: 'Post live', value: 'can_post_live: false', mono: true, status: 'blocked' },
      { label: 'Caveat', value: r.caveat },
    ],
  };
}

export function selectMetricsSnapshot(
  m: MetricsSnapshot,
  platform: string,
): SelectableObject {
  const fields: SelectableObject['fields'] = [
    { label: 'Platform', value: platform },
    { label: 'Captured', value: m.captured_at, mono: true },
    { label: 'Source', value: m.source, mono: true, status: 'review' },
  ];
  const counts: { label: string; value?: number }[] = [
    { label: 'Impressions', value: m.impressions },
    { label: 'Likes', value: m.likes },
    { label: 'Comments', value: m.comments },
    { label: 'Shares', value: m.shares },
    { label: 'Saves', value: m.saves },
    { label: 'Clicks', value: m.click_count },
  ];
  for (const c of counts) {
    if (c.value !== undefined) {
      fields.push({ label: c.label, value: String(c.value), mono: true });
    }
  }
  fields.push({ label: 'Notes', value: m.notes });
  fields.push({ label: 'Entry', value: 'Manual entry only · no metrics API', status: 'blocked' });
  return {
    kind: 'metrics_snapshot',
    id: m.id,
    title: `Metrics · ${m.captured_at}`,
    fields,
  };
}

export function selectManualChecklistItem(
  c: ManualPublishChecklistItem,
  platform: string,
): SelectableObject {
  return {
    kind: 'manual_checklist_item',
    id: c.id,
    title: c.label,
    fields: [
      { label: 'Platform', value: platform },
      { label: 'Status', value: c.status, status: c.status },
      { label: 'Detail', value: c.detail },
    ],
  };
}

/** Highest-priority inventory row: first item awaiting review, else first row. */
export function defaultContentItem(items: ContentItem[]): ContentItem {
  return items.find((i) => i.status === 'review') ?? items[0];
}

/**
 * Default-selected object for each view. The inspector must never be empty on
 * first render, so every view resolves to a meaningful primary object.
 */
export function defaultSelectionFor(view: ViewId): SelectableObject {
  const vm = viewModel;
  switch (view) {
    case 'command_center':
      return selectSystemVerdict(vm.system_state);
    case 'content_inventory':
      return selectContentItem(defaultContentItem(vm.content_items));
    case 'writer_studio':
      return selectAiVariant(vm.editorial_draft.ai_outputs[0]);
    case 'ai_writer_seo_lab':
      return selectAiVariant(vm.ai_writer_lab.outputs[0]);
    case 'draft_inspector':
      return selectDraftInspection(vm.draft_inspections[0]);
    case 'platform_payload_preview':
      return selectPlatformPayloadPreview(vm.platform_payload_previews[0]);
    case 'manual_publish_metrics':
      return selectManualPublishRecord(vm.manual_publish_records[0]);
    case 'manual_export_pilot_verification':
      return selectManualExportPilotPacket(manualExportPilotVerificationPacket);
    case 'operator_review_queue':
      return selectOperatorReviewQueuePacket(operatorReviewQueuePacket);
    case 'manual_pilot_trail_reconciliation':
      return selectManualPilotTrailReconciliationPacket(manualPilotTrailReconciliationPacket);
    case 'approval_queue': {
      const p = vm.approval_packets[0];
      const gate =
        p.gates.find((g) => g.id === 'GATE-approval') ?? p.gates[0];
      return selectDispatchGate(gate);
    }
    case 'evidence_vault': {
      const p = vm.evidence_packets[0];
      return selectValidation(p.validation_matrix[0], p.id);
    }
    case 'preflight_bundle':
      return selectPreflightBundlePacket(preflightBundlePacket);
  }
}

export function selectPreflightBundlePacket(
  p: LocalPreflightBundlePacket,
): SelectableObject {
  return {
    kind: 'preflight_bundle_packet',
    id: p.packet_id,
    title: `Preflight Bundle · ${p.matrix_version}`,
    fields: [
      { label: 'Packet ID', value: p.packet_id, mono: true },
      { label: 'Matrix version', value: p.matrix_version, mono: true },
      { label: 'Packet Hash', value: p.packet_hash, mono: true },
      { label: 'Hash alg', value: p.packet_hash_algorithm, mono: true },
      { label: 'Baseline', value: p.source_baseline_commit, mono: true },
      { label: 'Platforms', value: String(p.platform_count) },
      { label: 'Rooms', value: String(p.room_count) },
      { label: 'Source refs', value: String(p.source_ref_count) },
      { label: 'Fields count', value: String(p.candidate_field_count) },
      { label: 'UI policy', value: p.ui_binding_policy, mono: true },
    ],
  };
}

export function selectPreflightPlatformState(
  p: LocalPreflightBundlePlatformState,
): SelectableObject {
  return {
    kind: 'preflight_platform_state',
    id: p.platform_id,
    title: `Platform · ${p.platform_id}`,
    fields: [
      { label: 'Platform ID', value: p.platform_id, mono: true },
      { label: 'Role', value: p.platform_role },
      { label: 'Category', value: p.primary_or_secondary_or_expansion },
      { label: 'Endpoint', value: p.endpoint_family, mono: true },
      { label: 'Binding', value: p.account_binding_status, status: p.account_binding_status === 'bound' ? 'verified' : 'review' },
      { label: 'Cred slot', value: p.credential_slot_status },
      { label: 'Cred audit', value: p.credential_mock_audit_status, status: p.credential_mock_audit_status === 'blocked' ? 'blocked' : 'review' },
      { label: 'Preflight', value: p.preflight_simulation_status, status: p.preflight_simulation_status === 'blocked' ? 'blocked' : 'review' },
      { label: 'Budget state', value: p.rate_budget_status, status: p.rate_budget_status === 'blocked' ? 'blocked' : 'review' },
      { label: 'Evidence st', value: p.evidence_packet_status, status: p.evidence_packet_status === 'blocked' ? 'blocked' : 'review' },
      { label: 'Approval gate', value: p.approval_gate_status, status: p.approval_gate_status === 'blocked' ? 'blocked' : 'review' },
      { label: 'Display st', value: p.v5_display_status },
      { label: 'Kill switch', value: p.kill_switch_status },
      { label: 'Live read', value: p.live_read_allowed ? 'allowed' : 'blocked', status: p.live_read_allowed ? 'verified' : 'blocked' },
      { label: 'Live write', value: p.live_write_allowed ? 'allowed' : 'blocked', status: p.live_write_allowed ? 'verified' : 'blocked' },
      { label: 'Public post', value: p.public_post_allowed ? 'allowed' : 'blocked', status: p.public_post_allowed ? 'verified' : 'blocked' },
      { label: 'Dispatch ok', value: p.dispatch_ready ? 'ready' : 'blocked', status: p.dispatch_ready ? 'verified' : 'blocked' },
      { label: 'Readiness ok', value: p.readiness_cleared ? 'cleared' : 'blocked', status: p.readiness_cleared ? 'verified' : 'blocked' },
      { label: 'Blocked by', value: p.blocked_reasons.join(', ') || 'none' },
      { label: 'Missing proofs', value: p.missing_proofs.join(', ') || 'none' },
    ],
  };
}

export function selectPreflightRoomPrecheck(
  r: LocalPreflightBundleRoomBindingPrecheck,
): SelectableObject {
  return {
    kind: 'preflight_room_precheck',
    id: r.room_id,
    title: `Room Binding · ${r.room_id}`,
    fields: [
      { label: 'Room ID', value: r.room_id, mono: true },
      { label: 'Bind status', value: r.binding_status, status: 'review' },
      { label: 'No live action', value: r.no_live_action_affordances ? 'verified' : 'failed', status: r.no_live_action_affordances ? 'verified' : 'blocked' },
      { label: 'Disabled acts', value: r.disabled_affordances.join(', ') || 'none' },
      { label: 'Safe fields', value: String(r.safe_fields_count) },
      { label: 'Redacted flds', value: String(r.redacted_fields_count) },
      { label: 'Hidden fields', value: String(r.hidden_fields_count) },
      { label: 'Req contracts', value: r.required_contracts.join(', ') || 'none' },
      { label: 'Miss contracts', value: r.missing_contracts.join(', ') || 'none' },
      { label: 'Safety notes', value: r.safety_notes },
    ],
  };
}

export function selectPreflightSourceRef(
  s: LocalPreflightBundleSourceRef,
): SelectableObject {
  return {
    kind: 'preflight_source_ref',
    id: s.source_ref_id,
    title: `Source Ref · ${s.source_ref_id}`,
    fields: [
      { label: 'Source ID', value: s.source_ref_id, mono: true },
      { label: 'Task family', value: s.task_family },
      { label: 'Art family', value: s.artifact_family },
      { label: 'Module name', value: s.module_name, mono: true },
      { label: 'Code hash', value: s.source_hash_or_packet_hash, mono: true },
      { label: 'Status', value: s.source_status, status: s.source_status === 'valid' ? 'verified' : 'blocked' },
      { label: 'Consumed', value: s.consumed ? 'true' : 'false', status: s.consumed ? 'verified' : 'neutral' },
      { label: 'Env read', value: s.env_read ? 'true' : 'false', status: s.env_read ? 'blocked' : 'verified' },
      { label: 'Cred access', value: s.credential_values_accessed ? 'true' : 'false', status: s.credential_values_accessed ? 'blocked' : 'verified' },
      { label: 'Platform API', value: s.platform_api_called ? 'true' : 'false', status: s.platform_api_called ? 'blocked' : 'verified' },
      { label: 'Live capability', value: s.live_capability_added ? 'true' : 'false', status: s.live_capability_added ? 'blocked' : 'verified' },
      { label: 'Ingestion mut', value: s.ingestion_mutated ? 'true' : 'false', status: s.ingestion_mutated ? 'blocked' : 'verified' },
      { label: 'UI mutated', value: s.ui_mutated ? 'true' : 'false', status: s.ui_mutated ? 'blocked' : 'verified' },
    ],
  };
}

export function selectManualExportPilotPacket(
  p: V5ManualExportPilotVerificationPacket,
): SelectableObject {
  return {
    kind: 'manual_export_pilot_packet',
    id: p.export_package_id,
    title: 'Manual Export / Pilot Verification',
    fields: [
      { label: 'Package ID', value: p.export_package_id, mono: true },
      { label: 'Status', value: p.pilot_verification_status, status: 'blocked' },
      { label: 'Source hash', value: p.source_read_model_packet_hash, mono: true },
      { label: 'Packet hash', value: p.packet_hash, mono: true },
      { label: 'Targets', value: String(p.platform_targets.length) },
      { label: 'Copy blocks', value: String(p.manual_copy_blocks.length) },
      { label: 'Manual only', value: p.safety_flags.manual_export_only ? 'verified' : 'failed', status: p.safety_flags.manual_export_only ? 'verified' : 'blocked' },
      { label: 'Platform API', value: p.safety_flags.platform_api_called ? 'called' : 'none', status: p.safety_flags.platform_api_called ? 'blocked' : 'verified' },
      { label: 'Credentials', value: p.safety_flags.credential_values_accessed ? 'accessed' : 'not loaded', status: p.safety_flags.credential_values_accessed ? 'blocked' : 'verified' },
      { label: 'Dispatch', value: p.safety_flags.dispatch_ready ? 'ready' : 'blocked', status: p.safety_flags.dispatch_ready ? 'verified' : 'blocked' },
    ],
  };
}

export function selectManualExportTarget(
  t: V5ManualExportPlatformTarget,
): SelectableObject {
  return {
    kind: 'manual_export_target',
    id: t.target_id,
    title: t.platform_label,
    fields: [
      { label: 'Target ID', value: t.target_id, mono: true },
      { label: 'Class', value: t.target_class },
      { label: 'Status', value: t.status, status: t.status === 'future_gate_blocked' ? 'blocked' : 'review' },
      { label: 'Blocked by', value: t.blocked_reason },
      { label: 'Manual only', value: t.manual_only ? 'true' : 'false', status: t.manual_only ? 'verified' : 'blocked' },
      { label: 'No API', value: t.no_api ? 'true' : 'false', status: t.no_api ? 'verified' : 'blocked' },
      { label: 'No creds', value: t.no_credentials ? 'true' : 'false', status: t.no_credentials ? 'verified' : 'blocked' },
      { label: 'Scheduler', value: t.no_scheduler ? 'disabled' : 'enabled', status: t.no_scheduler ? 'verified' : 'blocked' },
      { label: 'Dispatch', value: t.dispatch_ready ? 'ready' : 'blocked', status: t.dispatch_ready ? 'verified' : 'blocked' },
      { label: 'Public post', value: t.public_postable ? 'true' : 'false', status: t.public_postable ? 'verified' : 'blocked' },
    ],
  };
}

export function selectManualCopyBlock(
  b: V5ManualCopyBlock,
): SelectableObject {
  return {
    kind: 'manual_copy_block',
    id: b.block_id,
    title: b.title,
    fields: [
      { label: 'Block ID', value: b.block_id, mono: true },
      { label: 'Target', value: b.platform_target_id, mono: true },
      { label: 'Class', value: b.content_classification, mono: true },
      { label: 'Draft only', value: b.draft_only ? 'true' : 'false', status: b.draft_only ? 'verified' : 'blocked' },
      { label: 'Manual only', value: b.manual_export_only ? 'true' : 'false', status: b.manual_export_only ? 'verified' : 'blocked' },
      { label: 'No secrets', value: b.no_secrets ? 'true' : 'false', status: b.no_secrets ? 'verified' : 'blocked' },
      { label: 'No raw bodies', value: b.no_raw_response_bodies ? 'true' : 'false', status: b.no_raw_response_bodies ? 'verified' : 'blocked' },
      { label: 'Copy text', value: b.copy_text },
    ],
  };
}

export function selectManualExportChecklistItem(
  c: V5ManualExportChecklistItem,
): SelectableObject {
  return {
    kind: 'manual_export_checklist_item',
    id: c.item_id,
    title: c.label,
    fields: [
      { label: 'Status', value: c.status, status: c.status },
      { label: 'Detail', value: c.detail },
    ],
  };
}

export function selectOperatorReviewQueuePacket(
  p: V5OperatorReviewQueueManualPilotTrailPacket,
): SelectableObject {
  return {
    kind: 'operator_review_queue_packet',
    id: p.queue_id,
    title: 'Operator Review Queue & Manual Pilot Trail',
    fields: [
      { label: 'Queue ID', value: p.queue_id, mono: true },
      { label: 'Status', value: p.item_status_summary, status: 'review' },
      { label: 'Export hash', value: p.source_manual_export_packet_hash, mono: true },
      { label: 'Packet hash', value: p.packet_hash, mono: true },
      { label: 'Items count', value: String(p.review_items.length) },
      { label: 'Trail count', value: String(p.local_review_trail_entries.length) },
      { label: 'Local only', value: p.safety_flags.local_only ? 'verified' : 'failed', status: p.safety_flags.local_only ? 'verified' : 'blocked' },
      { label: 'Platform API', value: p.safety_flags.platform_api_called ? 'called' : 'none', status: p.safety_flags.platform_api_called ? 'blocked' : 'verified' },
      { label: 'Credentials', value: p.safety_flags.credential_values_accessed ? 'accessed' : 'not loaded', status: p.safety_flags.credential_values_accessed ? 'blocked' : 'verified' },
    ],
  };
}

export function selectReviewItem(
  i: V5ReviewItem,
): SelectableObject {
  return {
    kind: 'operator_review_item',
    id: i.item_id,
    title: i.label,
    fields: [
      { label: 'Item ID', value: i.item_id, mono: true },
      { label: 'Status', value: i.status, status: i.status === 'manual_review_required' ? 'review' : 'verified' },
      { label: 'Local only', value: i.local_only ? 'true' : 'false', status: i.local_only ? 'verified' : 'blocked' },
      { label: 'No API', value: i.no_api ? 'true' : 'false', status: i.no_api ? 'verified' : 'blocked' },
      { label: 'No creds', value: i.no_credentials ? 'true' : 'false', status: i.no_credentials ? 'verified' : 'blocked' },
      { label: 'Scheduler', value: i.no_scheduler ? 'disabled' : 'enabled', status: i.no_scheduler ? 'verified' : 'blocked' },
      { label: 'Dispatch', value: i.not_dispatch_ready ? 'blocked' : 'ready', status: i.not_dispatch_ready ? 'blocked' : 'verified' },
      { label: 'Postable', value: i.not_public_postable ? 'false' : 'true', status: i.not_public_postable ? 'blocked' : 'verified' },
      { label: 'Detail', value: i.detail },
    ],
  };
}

export function selectTrailEntry(
  e: V5TrailEntry,
): SelectableObject {
  return {
    kind: 'local_review_trail_entry',
    id: e.entry_id,
    title: e.label,
    fields: [
      { label: 'Entry ID', value: e.entry_id, mono: true },
      { label: 'Type', value: e.entry_type, mono: true },
      { label: 'Status', value: e.status, status: e.status },
      { label: 'Timestamp', value: e.timestamp_placeholder, mono: true },
      { label: 'Label', value: e.label },
    ],
  };
}

export function selectManualPilotTrailReconciliationPacket(
  p: V5ManualPilotTrailReconciliationPacket,
): SelectableObject {
  return {
    kind: 'manual_pilot_trail_reconciliation_packet',
    id: p.reconciliation_id,
    title: `Reconciliation · ${p.reconciliation_id.slice(0, 16)}...`,
    fields: [
      { label: 'Reconciliation ID', value: p.reconciliation_id, mono: true },
      { label: 'Contract Version', value: p.contract_version, mono: true },
      { label: 'Reconciliation Status', value: p.reconciliation_status, status: p.reconciliation_status === 'blocked_reconciliation_pending_evidence' ? 'blocked' : 'verified' },
      { label: 'Source Queue ID', value: p.source_operator_review_queue_id, mono: true },
      { label: 'Source Export Hash', value: p.source_manual_export_packet_hash, mono: true },
      { label: 'Source Review Hash', value: p.source_operator_review_packet_hash, mono: true },
      { label: 'Baseline Commit', value: p.source_baseline_commit, mono: true },
      { label: 'Task Label', value: p.task_label, mono: true },
      { label: 'Packet Hash', value: p.packet_hash, mono: true },
    ],
  };
}

export function selectLifecycleStep(
  s: V5LifecycleStep,
): SelectableObject {
  return {
    kind: 'reconciliation_lifecycle_step',
    id: s.step_id,
    title: s.label,
    fields: [
      { label: 'Step ID', value: s.step_id, mono: true },
      { label: 'Status', value: s.status, status: s.status },
      { label: 'Detail', value: s.detail },
      { label: 'Local Timestamp', value: s.timestamp_placeholder, mono: true },
    ],
  };
}

export function selectPlaceholderField(
  f: V5PlaceholderField,
): SelectableObject {
  return {
    kind: 'reconciliation_placeholder_field',
    id: f.field_id,
    title: f.label,
    fields: [
      { label: 'Field ID', value: f.field_id, mono: true },
      { label: 'Current Value', value: f.value === '' ? '(empty)' : f.value, mono: f.value !== '' },
      { label: 'Status', value: f.status, status: 'review' },
      { label: 'Verification Detail', value: f.detail },
    ],
  };
}

export function selectManualPilotTrailReconciliationAuditPacket(
  p: V5ManualPilotTrailReconciliationAuditPacket,
): SelectableObject {
  return {
    kind: 'manual_pilot_audit_packet',
    id: p.audit_id,
    title: `Manual Pilot Audit · ${p.contract_version}`,
    fields: [
      { label: 'Audit ID', value: p.audit_id, mono: true },
      { label: 'Audit Status', value: p.audit_status, status: p.audit_status === 'verified_blocked_manual_only' ? 'verified' : 'blocked' },
      { label: 'Contract Version', value: p.contract_version, mono: true },
      { label: 'Packet Hash', value: p.packet_hash, mono: true },
      { label: 'Hash Alg', value: p.packet_hash_algorithm, mono: true },
      { label: 'Baseline Commit', value: p.source_baseline_commit, mono: true },
      { label: 'Task Label', value: p.task_label, mono: true },
      { label: 'Next Task', value: p.next_recommended_task, mono: true },
    ],
  };
}

export function selectAuditInvariant(
  name: string,
  passed: boolean,
): SelectableObject {
  return {
    kind: 'audit_invariant',
    id: name,
    title: name.replace(/_/g, ' '),
    fields: [
      { label: 'Invariant ID', value: name, mono: true },
      { label: 'Verification', value: passed ? 'PASSED' : 'FAILED', status: passed ? 'verified' : 'blocked' },
      { label: 'Scope', value: 'local-only compliance check' },
    ],
  };
}

export function selectAuditContradiction(
  text: string,
  index: number,
): SelectableObject {
  return {
    kind: 'audit_contradiction',
    id: `contradiction-${index}`,
    title: `Contradiction #${index + 1}`,
    fields: [
      { label: 'Detail', value: text },
      { label: 'Severity', value: 'blocked', status: 'blocked' },
    ],
  };
}
