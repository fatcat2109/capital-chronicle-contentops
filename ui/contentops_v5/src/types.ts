// Capital Chronicle ContentOps V5 — local view-model types.
// All data is local fixture only. No runtime network, no credentials.

export type ThemeMode = 'light' | 'dark-evidence';

export type StatusKind = 'verified' | 'review' | 'blocked' | 'neutral';

export type ViewId =
  | 'command_center'
  | 'content_inventory'
  | 'writer_studio'
  | 'ai_writer_seo_lab'
  | 'draft_inspector'
  | 'platform_payload_preview'
  | 'manual_publish_metrics'
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

/**
 * AI Writer output contract. AI is UI-only and review-only: it is NEVER source
 * authority. publish_ready is the literal `false` so a publish-ready variant is
 * unrepresentable. All ids/metrics are synthetic local fixtures.
 */
export interface AiWriterOutput {
  variant_id: string;
  source_draft_id: string;
  source_artifact_id?: string;
  platform: string;
  audience_mode: string;
  style_mode: string;
  content_type: string;
  body: string;
  hook_type: string;
  hashtags: string[];
  seo_keywords: string[];
  title_candidates: string[];
  limitations_preserved: boolean;
  source_references_preserved: boolean;
  safety_notes: string[];
  not_public_postable_reason: string;
  editorial_score: number;
  seo_score: number;
  platform_fit_score: number;
  guardrail_status: StatusKind;
  human_review_required: boolean;
  publish_ready: false;
}

/** A grouped set of SEO keywords selectable in the SEO Lab. */
export interface SeoKeywordGroup {
  id: string;
  label: string;
  intent: string;
  keywords: string[];
  seo_score: number;
  status: StatusKind;
}

/** A single citation completeness check for the Draft Inspector. */
export interface CitationCheck {
  id: string;
  label: string;
  source_ref: string;
  status: StatusKind;
  detail: string;
}

/** A claim-risk classification item. */
export interface ClaimRiskItem {
  id: string;
  label: string;
  classification: string;
  severity: StatusKind;
  detail: string;
}

/** A limitation/caveat preservation check. */
export interface LimitationCheck {
  id: string;
  label: string;
  status: StatusKind;
  detail: string;
}

/** A no-signal / forbidden-language audit row. */
export interface NoSignalCheck {
  id: string;
  label: string;
  status: StatusKind;
  detail: string;
}

/** An artifact-backed eligibility check (Lane C readiness). */
export interface ArtifactEligibilityCheck {
  id: string;
  label: string;
  status: StatusKind;
  detail: string;
}

/** A draft inspection record aggregating all check families for one draft. */
export interface DraftInspection {
  id: string;
  draft_id: string;
  title: string;
  source_lineage: { id: string; label: string }[];
  citation_checks: CitationCheck[];
  limitation_checks: LimitationCheck[];
  claim_risk_items: ClaimRiskItem[];
  no_signal_checks: NoSignalCheck[];
  artifact_eligibility_checks: ArtifactEligibilityCheck[];
  approval_readiness: string;
  approval_readiness_status: StatusKind;
  human_review_required: boolean;
  publish_ready: false;
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

export interface AiWriterLab {
  source_draft_id: string;
  audience_modes: string[];
  style_modes: string[];
  keyword_groups: SeoKeywordGroup[];
  outputs: AiWriterOutput[];
}

/**
 * A single per-platform constraint check shown in the payload preview. Purely
 * descriptive: it reflects how the local fixture payload measures against a
 * platform's documented limit. It is NOT a live validation and never calls a
 * platform API.
 */
export interface PayloadConstraint {
  id: string;
  label: string;
  limit: string;
  actual: string;
  status: StatusKind;
  detail: string;
}

/**
 * A single field of the compiled local payload (e.g. body, title, hashtags).
 * Values are local fixture strings only.
 */
export interface PayloadField {
  id: string;
  label: string;
  value: string;
  mono?: boolean;
}

/**
 * Per-platform dry-run payload preview contract. This surface is dry-run only:
 * it shows the exact LOCAL fixture payload that WOULD be assembled for a
 * platform, with zero posting, scheduling, credential use, provider call, or
 * platform API behavior. `dispatchable` is the literal `false` so a
 * dispatchable preview is structurally unrepresentable. `live_status` and
 * `credential_status` are always locked/blocked by policy.
 */
export interface PlatformPayloadPreview {
  id: string;
  platform: string;
  platform_key: string;
  source_draft_id: string;
  format_label: string;
  fit_status: StatusKind;
  fit_summary: string;
  fields: PayloadField[];
  constraints: PayloadConstraint[];
  media_note: string;
  live_status: 'LIVE_DISABLED';
  credential_status: 'NO_CREDENTIAL_READ';
  provider_status: 'NO_PROVIDER_CALL';
  not_dispatchable_reason: string;
  dispatchable: false;
}

/**
 * A single operator checklist item that must be satisfied before a manual
 * (human, off-platform) post is considered done. Purely a recordkeeping aid;
 * checking items never triggers any posting, scheduling, or network behavior.
 */
export interface ManualPublishChecklistItem {
  id: string;
  label: string;
  status: StatusKind;
  detail: string;
}

/**
 * A manually-entered metrics snapshot for a manual publish record. Every value
 * is typed in by a human from what they observed on-platform. There is NO
 * metrics API, no provider call, and no fetch: `source` is the literal
 * 'MANUAL_ENTRY' so an automated/synced snapshot is structurally
 * unrepresentable. Counts are optional because not every platform exposes every
 * metric, and `click_count` only applies where a link is present.
 */
export interface MetricsSnapshot {
  id: string;
  captured_at: string;
  impressions?: number;
  likes?: number;
  comments?: number;
  shares?: number;
  saves?: number;
  click_count?: number;
  notes: string;
  source: 'MANUAL_ENTRY';
}

/**
 * Manual publish + metrics capture contract. This surface is the bridge from
 * dry-run payload preview to operator MANUAL posting recordkeeping. It is
 * manual-only: the operator posts off-platform by hand, then records the URL,
 * timestamp, and any metrics here. There is zero live posting, scheduling,
 * platform/provider API, credential read, or autonomous behavior.
 *
 * `can_post_live` is the literal `false` so a live-postable record is
 * structurally unrepresentable. `live_status` / `credential_status` /
 * `provider_status` / `scheduler_status` are always locked by policy. The
 * manual URL and timestamps are LOCAL fixture/mock strings, never fetched.
 */
export interface ManualPublishRecord {
  id: string;
  platform: string;
  platform_key: string;
  source_draft_id: string;
  payload_ref: string;
  payload_hash: string;
  approval_packet_ref: string;
  approval_packet_hash: string;
  /** Lifecycle bucket the record falls into for the status tabs. */
  stage: 'approved_for_manual' | 'blocked' | 'manually_posted' | 'metrics_entered';
  stage_label: string;
  stage_status: StatusKind;
  /** Mock/local manual post URL. Empty string when not yet posted. */
  manual_url: string;
  /** Local mock publish timestamp. Empty string when not yet posted. */
  published_at: string;
  checklist: ManualPublishChecklistItem[];
  metrics: MetricsSnapshot[];
  audit_state: string;
  audit_status: StatusKind;
  caveat: string;
  blocked_reason: string;
  allowed_operator_action?: string;
  evidence_refs?: string[];
  public_postable?: false;
  live_status: 'MANUAL_ONLY';
  platform_api_status: 'NO_PLATFORM_API';
  credential_status: 'NO_CREDENTIAL_READ';
  scheduler_status: 'NO_SCHEDULER';
  autonomous_status: 'NO_AUTONOMOUS_POSTING';
  metrics_status: 'METRICS_MANUAL_ENTRY_ONLY';
  review_status: 'HUMAN_REVIEW_REQUIRED';
  can_post_live: false;
}

export interface CockpitQueueItem {
  item_id: string;
  platform: 'substack' | 'x' | 'telegram' | string;
  payload_class: string;
  payload_hash: string;
  payload_hash_short: string;
  review_status: string;
  allowed_operator_action: string;
  can_dispatch: false;
  public_postable: false;
  human_review_required: boolean;
  no_financial_advice: boolean;
  no_signal_language: boolean;
  evidence_refs: string[];
  limitations: string[];
  source_notes: string[];
}

export interface CockpitBlockedDispatchItem {
  blocker_id: string;
  status: 'BLOCKED';
  reason: string;
  required_future_gate: string;
  allowed_operator_action: 'hold';
  can_dispatch: false;
  public_postable: false;
  human_review_required: boolean;
}

export interface CockpitEvidenceEntry {
  stage: string;
  checksum: string;
}

export interface CockpitNoLiveProof {
  proof: string;
  is_local_only: boolean;
  network_performed: false;
  credential_read: false;
  env_read: false;
  dotenv_read: false;
  provider_api_called: false;
  llm_provider_api_called: false;
  platform_api_called: false;
  platform_dispatch_performed: false;
  live_post_performed: false;
  live_ready_state_created: false;
  scheduler_enabled: false;
  scraping_performed: false;
  autonomous_replies_or_dms: false;
  public_ready_content_generated: false;
  token_logged: false;
  raw_request_persisted: false;
  raw_response_persisted: false;
  substack_api_called: false;
  telegram_api_called: false;
  x_api_called: false;
}

export interface CockpitReadModelPacket {
  task_label: string;
  model: string;
  model_version: string;
  cockpit_read_model_id: string;
  cockpit_read_model_checksum: string;
  source_baseline_commit: string;
  readiness_class: string;
  status: 'pass';
  live_dispatch_status: 'BLOCKED';
  can_dispatch: false;
  public_postable: false;
  manual_export_status: string;
  next_operator_action: string;
  local_governance_status: string;
  platform_statuses: Record<string, string>;
  platform_counts: Record<string, number>;
  operator_summary: {
    reviewable_now_count: number;
    blocked_live_dispatch_count: number;
    first_safe_action: string;
  };
  blocker_summary: {
    live_dispatch_status: 'BLOCKED';
    required_future_gates: string[];
    blocked_reasons: string[];
  };
  no_live_behavior_proof: CockpitNoLiveProof;
  action_counts: Record<string, number>;
  current_review_queue: CockpitQueueItem[];
  blocked_live_dispatch_queue: CockpitBlockedDispatchItem[];
  evidence_index: CockpitEvidenceEntry[];
}

export interface CockpitViewModel {
  packet: CockpitReadModelPacket;
  manual_export_queue: CockpitQueueItem[];
  x_preview_queue: CockpitQueueItem[];
  telegram_preview_queue: CockpitQueueItem[];
  blocked_live_dispatch_queue: CockpitBlockedDispatchItem[];
  evidence_index: CockpitEvidenceEntry[];
  safety_modes: string[];
  current_gate: string;
  accepted_baseline: string;
}

export interface ContentOpsViewModel {
  system_state: SystemState;
  cockpit: CockpitViewModel;
  content_items: ContentItem[];
  editorial_draft: EditorialDraft;
  ai_writer_lab: AiWriterLab;
  draft_inspections: DraftInspection[];
  platform_payload_previews: PlatformPayloadPreview[];
  manual_publish_records: ManualPublishRecord[];
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
