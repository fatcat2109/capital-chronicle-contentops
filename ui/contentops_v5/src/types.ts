// Capital Chronicle ContentOps V5 — local view-model types.
// All data is local fixture only. No runtime network, no credentials.

export type ThemeMode = 'light' | 'dark-evidence';

export type StatusKind = 'verified' | 'review' | 'blocked' | 'neutral';

export type ViewId =
  | 'command_center'
  | 'content_inventory'
  | 'writer_studio'
  | 'approval_queue'
  | 'evidence_vault';

export interface SystemMode {
  code: string;
  active: boolean;
}

export interface Blocker {
  id: string;
  label: string;
  detail: string;
  severity: StatusKind;
}

export interface ValidationPass {
  id: string;
  label: string;
  status: StatusKind;
  detail: string;
}

export interface SystemState {
  product_mode: string;
  modes: SystemMode[];
  verdict: string;
  verdict_status: StatusKind;
  baseline_ref: string;
  build_provenance: string;
  next_allowed_action: string;
  blockers: Blocker[];
  validation_passes: ValidationPass[];
  pipeline_health: { label: string; value: string; status: StatusKind }[];
  queue_summary: { label: string; count: number; status: StatusKind }[];
}

export interface ContentItem {
  id: string;
  title: string;
  lane: 'A_pre_alpha' | 'B_grounded_news' | 'C_artifact_backed';
  content_type: string;
  status: StatusKind;
  status_label: string;
  platform_fit: string[];
  citation_state: StatusKind;
  media_state: StatusKind;
  approval_state: string;
  owner: string;
  last_updated: string;
  evidence_id: string;
}

export interface SeoMetadata {
  keywords: string[];
  title_candidates: string[];
  hook_variants: string[];
  editorial_score: number;
  seo_score: number;
  platform_fit_score: number;
  readability: string;
}

export interface AiWriterOutput {
  variant_id: string;
  source_draft_id: string;
  platform: string;
  audience_mode: string;
  style_mode: string;
  content_type: string;
  guardrail_status: StatusKind;
  human_review_required: boolean;
  publish_ready: false;
  not_public_postable_reason: string;
  limitations_preserved: boolean;
  source_references_preserved: boolean;
}

export interface MediaAsset {
  id: string;
  name: string;
  kind: string;
  alt_text: string;
  rights_status: StatusKind;
  rights_label: string;
  platform_constraints: string[];
  selected: boolean;
}

export interface EditorialDraft {
  id: string;
  title: string;
  outline: string[];
  body_excerpt: string;
  platform_tabs: string[];
  citations: { id: string; label: string; status: StatusKind }[];
  limitation_note: string;
  claim_risks: { id: string; label: string; severity: StatusKind }[];
  guardrails: { id: string; label: string; status: StatusKind }[];
  seo: SeoMetadata;
  ai_outputs: AiWriterOutput[];
  media: MediaAsset[];
}

export interface DispatchGate {
  id: string;
  label: string;
  status: StatusKind;
  cleared: boolean;
  detail: string;
}

export interface ApprovalPacket {
  id: string;
  title: string;
  required_approver: string;
  draft_hash: string;
  payload_hash: string;
  approval_state: string;
  approval_status: StatusKind;
  revocation_state: string;
  redacted_audit_state: string;
  risk_state: StatusKind;
  evidence_sources: string[];
  comments: { author: string; note: string }[];
  gates: DispatchGate[];
  dispatch_enabled: false;
}

export interface EvidencePacket {
  id: string;
  task_label: string;
  result: StatusKind;
  result_label: string;
  commit_ref: string;
  timestamp: string;
  validation_matrix: ValidationPass[];
  forbidden_scope: { id: string; label: string; status: StatusKind }[];
  secret_scan: { label: string; status: StatusKind; detail: string };
  provenance_chips: string[];
  source_lineage: { id: string; label: string }[];
}

export interface AuditEvent {
  id: string;
  timestamp: string;
  actor: string;
  action: string;
  ref: string;
}

export interface PolicyBoundary {
  id: string;
  label: string;
  status: StatusKind;
  detail: string;
}

export interface InternalAlphaArtifactPlaceholder {
  id: string;
  artifact_type: string;
  intake_status: StatusKind;
  intake_label: string;
  reason_blocked: string;
}

export interface ContentOpsViewModel {
  system_state: SystemState;
  content_items: ContentItem[];
  editorial_draft: EditorialDraft;
  approval_packets: ApprovalPacket[];
  evidence_packets: EvidencePacket[];
  audit_events: AuditEvent[];
  policy_boundaries: PolicyBoundary[];
  internal_alpha_artifacts: InternalAlphaArtifactPlaceholder[];
}

export interface SelectableObject {
  kind: string;
  id: string;
  title: string;
  fields: { label: string; value: string; mono?: boolean; status?: StatusKind }[];
}
