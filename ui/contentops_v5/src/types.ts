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
  | 'manual_export_pilot_verification'
  | 'operator_review_queue'
  | 'manual_pilot_trail_reconciliation'
  | 'approval_queue'
  | 'evidence_vault'
  | 'preflight_bundle'
  | 'operator_runbook_index';

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
  fields: { label: string; value: string; mono?: boolean; status?: StatusKind }[];
  id: string;
  kind: string;
  title: string;
}

export interface LocalPreflightBundleSafetyFlags {
  autonomous_posting_allowed: boolean;
  browser_session_used: boolean;
  credential_hydrated: boolean;
  credential_values_accessed: boolean;
  current_truth_promoted: boolean;
  dispatch_ready: boolean;
  dm_or_reply_automation_allowed: boolean;
  dqr_cleared: boolean;
  env_read: boolean;
  ingestion_repo_mutated: boolean;
  live_read_allowed: boolean;
  live_write_allowed: boolean;
  local_only: boolean;
  network_performed: boolean;
  platform_api_called: boolean;
  provider_api_called: boolean;
  public_post_allowed: boolean;
  read_model_precheck_only: boolean;
  readiness_cleared: boolean;
  scheduler_enabled: boolean;
  scraping_performed: boolean;
  secret_output_allowed: boolean;
  ui_mutated: boolean;
}

export interface LocalPreflightBundlePlatformState {
  account_binding_status: string;
  approval_gate_status: string;
  blocked_reasons: string[];
  credential_mock_audit_status: string;
  credential_slot_status: string;
  dispatch_ready: boolean;
  endpoint_family: string;
  evidence_packet_status: string;
  hidden_or_absent_fields: string[];
  kill_switch_status: string;
  live_read_allowed: boolean;
  live_write_allowed: boolean;
  manual_export_status: string;
  missing_proofs: string[];
  platform_id: string;
  platform_role: string;
  preflight_simulation_status: string;
  primary_or_secondary_or_expansion: string;
  public_post_allowed: boolean;
  rate_budget_status: string;
  readiness_cleared: boolean;
  redaction_required_fields: string[];
  safe_display_fields: string[];
  v5_display_status: string;
}

export interface LocalPreflightBundleRoomBindingPrecheck {
  binding_status: string;
  disabled_affordances: string[];
  hidden_fields_count: number;
  missing_contracts: string[];
  no_live_action_affordances: boolean;
  redacted_fields_count: number;
  required_contracts: string[];
  room_id: string;
  safe_fields_count: number;
  safety_notes: string;
}

export interface LocalPreflightBundleSourceRef {
  artifact_family: string;
  consumed: boolean;
  credential_values_accessed: boolean;
  env_read: boolean;
  ingestion_mutated: boolean;
  live_capability_added: boolean;
  module_name: string;
  platform_api_called: boolean;
  source_hash_or_packet_hash: string;
  source_ref_id: string;
  source_status: string;
  task_family: string;
  ui_mutated: boolean;
}

export interface LocalPreflightBundleCandidateField {
  current_truth_policy: string;
  display_policy: string;
  evidence_ref: string;
  field_id: string;
  field_kind: string;
  field_name: string;
  forbidden_affordance_reason: string;
  room_id: string;
  sample_value_classification: string;
  source_family: string;
  source_ref_id: string;
  user_action_affordance: string;
}

export interface LocalPreflightBundlePacket {
  candidate_field_count: number;
  generated_at_epoch: number;
  global_blocked_reasons: string[];
  global_missing_proofs: string[];
  matrix_version: string;
  next_recommended_task?: string;
  packet_hash: string;
  packet_hash_algorithm: string;
  packet_id: string;
  platform_count: number;
  platform_states: LocalPreflightBundlePlatformState[];
  room_binding_prechecks: LocalPreflightBundleRoomBindingPrecheck[];
  room_count: number;
  safety_flags: LocalPreflightBundleSafetyFlags;
  source_baseline_commit: string;
  source_ref_count: number;
  source_refs: LocalPreflightBundleSourceRef[];
  task_label: string;
  u9_audit_entry_families: string[];
  u9_audit_entry_ids: string[];
  ui_binding_policy: string;
  v5_candidate_fields: LocalPreflightBundleCandidateField[];
}

export interface V5ManualExportPilotSafetyFlags {
  credential_hydrated: boolean;
  credential_values_accessed: boolean;
  dispatch_ready: boolean;
  dm_or_reply_automation_allowed: boolean;
  dotenv_loaded: boolean;
  env_read: boolean;
  ingestion_repo_mutated: boolean;
  local_only: boolean;
  manual_export_only: boolean;
  network_performed: boolean;
  pilot_verification_only: boolean;
  platform_api_called: boolean;
  posting_performed: boolean;
  provider_api_called: boolean;
  public_postable: boolean;
  readiness_cleared: boolean;
  scheduler_enabled: boolean;
  scraping_performed: boolean;
  secret_output_allowed: boolean;
  token_hash_or_prefix_suffix_output: boolean;
}

export interface V5ManualExportPlatformTarget {
  blocked_reason: string;
  dispatch_ready: false;
  manual_copy_block_id: string;
  manual_only: true;
  no_api: true;
  no_credentials: true;
  no_scheduler: true;
  not_live: true;
  not_public_postable_until_operator_action_outside_system: true;
  platform_label: string;
  public_postable: false;
  status: string;
  target_class: string;
  target_id: string;
}

export interface V5ManualCopyBlock {
  block_id: string;
  content_classification: string;
  copy_text: string;
  draft_only: true;
  manual_export_only: true;
  no_fake_live_market_data: true;
  no_raw_response_bodies: true;
  no_secrets: true;
  platform_target_id: string;
  title: string;
}

export interface V5ManualExportChecklistItem {
  detail: string;
  item_id: string;
  label: string;
  status: StatusKind;
}

export interface V5ReviewSignaturePlaceholder {
  cryptographic_signature: false;
  signature_value: string;
  signer_label: string;
  status: string;
  uses_secret_material: false;
}

export interface V5ManualEmptyPlaceholder {
  detail: string;
  status: string;
  value: string;
}

export interface V5DisabledLiveDispatchState {
  connect_account_enabled: false;
  live_dispatch_enabled: false;
  publish_enabled: false;
  reason: string;
  schedule_enabled: false;
  send_enabled: false;
  state_id: string;
  sync_platform_enabled: false;
  verify_credentials_enabled: false;
}

export interface V5PilotVerificationPacket {
  blocked_reasons: string[];
  checklist_items: V5ManualExportChecklistItem[];
  missing_proofs: string[];
  no_live_action_proof: string[];
  packet_hash: string;
  packet_hash_algorithm: string;
  redaction_proof: string[];
  status: string;
  u9_audit_references: string[];
  verification_id: string;
}

export interface V5ManualExportPilotVerificationPacket {
  contract_version: string;
  disabled_live_dispatch_state: V5DisabledLiveDispatchState;
  evidence_refs: string[];
  export_package_id: string;
  generated_at_epoch: number;
  manual_copy_blocks: V5ManualCopyBlock[];
  manual_metrics_placeholder: V5ManualEmptyPlaceholder;
  manual_publish_url_placeholder: V5ManualEmptyPlaceholder;
  next_recommended_task: string;
  operator_review_checklist: V5ManualExportChecklistItem[];
  packet_hash: string;
  packet_hash_algorithm: string;
  pilot_verification_packet: V5PilotVerificationPacket;
  pilot_verification_status: string;
  platform_targets: V5ManualExportPlatformTarget[];
  review_signature_placeholder: V5ReviewSignaturePlaceholder;
  safety_flags: V5ManualExportPilotSafetyFlags;
  source_baseline_commit: string;
  source_read_model_packet_hash: string;
  source_read_model_packet_id: string;
  task_label: string;
}

export interface V5ReviewItem {
  detail: string;
  item_id: string;
  label: string;
  local_only: boolean;
  manual_review_required: boolean;
  no_api: boolean;
  no_credentials: boolean;
  no_scheduler: boolean;
  not_dispatch_ready: boolean;
  not_public_postable: boolean;
  operator_action_outside_contentops_required: boolean;
  status: StatusKind | 'manual_review_required';
}

export interface V5TrailEntry {
  entry_id: string;
  entry_type: string;
  label: string;
  status: StatusKind;
  timestamp_placeholder: string;
}

export interface V5OperatorReviewQueueManualPilotTrailPacket {
  blocked_reasons: string[];
  contract_version: string;
  disabled_live_action_state: V5DisabledLiveDispatchState;
  item_status_summary: string;
  local_review_trail_entries: V5TrailEntry[];
  manual_publish_placeholders: V5ManualEmptyPlaceholder[];
  missing_proofs: string[];
  next_recommended_task: string;
  packet_hash: string;
  packet_hash_algorithm: string;
  queue_id: string;
  review_items: V5ReviewItem[];
  safety_flags: V5ManualExportPilotSafetyFlags;
  source_baseline_commit: string;
  source_manual_export_packet_hash: string;
  task_label: string;
}

export interface V5ReconciliationSafetyFlags {
  approval_mutation: boolean;
  credential_values_loaded: boolean;
  dispatch_ready: boolean;
  local_only: boolean;
  manual_only: boolean;
  network_performed: boolean;
  no_credentials: boolean;
  no_live_dispatch: boolean;
  no_platform_api: boolean;
  no_scheduler: boolean;
  public_postable: boolean;
}

export interface V5LifecycleStep {
  detail: string;
  label: string;
  status: StatusKind;
  step_id: string;
  timestamp_placeholder: string;
}

export interface V5PlaceholderField {
  detail: string;
  field_id: string;
  label: string;
  status: string;
  value: string;
}

export interface V5ManualPilotTrailReconciliationPacket {
  blocked_reasons: string[];
  contract_version: string;
  disabled_live_action_state: V5DisabledLiveDispatchState;
  lifecycle_steps: V5LifecycleStep[];
  missing_evidence: string[];
  next_recommended_task: string;
  packet_hash: string;
  packet_hash_algorithm: string;
  placeholder_fields: V5PlaceholderField[];
  reconciliation_id: string;
  reconciliation_status: string;
  safety_flags: V5ReconciliationSafetyFlags;
  source_baseline_commit: string;
  source_manual_export_packet_hash: string;
  source_operator_review_packet_hash: string;
  source_operator_review_queue_id: string;
  task_label: string;
}

export interface V5ReconciliationAuditSourcePacket {
  contract_version: string;
  packet_hash: string;
}

export interface V5ManualPilotTrailReconciliationAuditPacket {
  audit_id: string;
  audit_status: string;
  blocked_reason_results: { reasons: string[] };
  chain_links: {
    uy_to_uw_link: string;
    uz_to_uw_link: string;
    uz_to_uy_packet_hash: string;
    uz_to_uy_queue_id: string;
  };
  contract_version: string;
  contradiction_results: { contradictions_found: string[] };
  disabled_live_action_results: { passed: boolean };
  invariant_results: Record<string, boolean>;
  missing_evidence_results: { passed: boolean; required_missing: string[] };
  next_recommended_task: string;
  packet_hash: string;
  packet_hash_algorithm: string;
  placeholder_integrity_results: { passed: boolean };
  safety_flag_results: Record<string, boolean>;
  safety_flags: Record<string, boolean>;
  source_baseline_commit: string;
  source_packets: Record<string, V5ReconciliationAuditSourcePacket>;
  task_label: string;
}

export interface V5RunbookStep {
  step_id: string;
  view_id: string;
  source_packet: string;
  status: string;
  operator_meaning: string;
  what_human_can_do: string;
  what_system_cannot_do: string;
  blocked_reasons: string[];
  missing_evidence: string[];
  evidence_refs: string[];
  next_safe_step: string;
}

export interface V5OperatorRunbookIndexPacket {
  audit_status: string;
  contract_version: string;
  invariant_results: Record<string, boolean>;
  next_recommended_task: string;
  packet_hash: string;
  packet_hash_algorithm: string;
  runbook_id: string;
  runbook_steps: V5RunbookStep[];
  safety_flags: Record<string, boolean>;
  source_baseline_commit: string;
  task_label: string;
}
