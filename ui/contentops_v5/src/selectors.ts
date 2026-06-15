// Capital Chronicle ContentOps V5 — selection object builders.
// Single source of truth for inspector content + per-view default selection.
// Pure functions over local fixture data. No network, storage, or credentials.

import { viewModel } from './fixtures';
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
  MediaAsset,
  NoSignalCheck,
  SeoKeywordGroup,
  SelectableObject,
  SystemState,
  ValidationPass,
  ViewId,
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
  }
}
