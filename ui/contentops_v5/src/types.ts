// Capital Chronicle ContentOps V5 â€” local view-model types.
// All data is local fixture only. No runtime network, no credentials.

export type ThemeMode = 'light' | 'dark-evidence';

export type StatusKind = 'verified' | 'review' | 'blocked' | 'neutral';

export type ViewId =
  | 'command_center'
  | 'content_inventory'
  | 'jim_daily_run'
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
  | 'operator_runbook_index'
  | 'final_product_readiness'
  | 'v6_command_center'
  | 'canonical_package_review'
  | 'dual_lane_core_v0_shadow';

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



export interface V6CommandCenterRoom {
  room_id: string;
  label: string;
  status: StatusKind;
  detail: string;
}
export interface V6CommandCenterCriterion {
  step_id: string;
  label: string;
  status: StatusKind;
  live_action_required: boolean;
}
export interface V6CommandCenterMetricRow {
  metric_id: string;
  source_mode: string;
  status: StatusKind;
  detail: string;
  api_or_scrape_used: boolean;
}
export interface V6CommandCenterRedTeamCase {
  case_id: string;
  expected: string;
  result: StatusKind;
}
export interface V6OperatorFlowStage {
  stage_id: string;
  label: string;
  status: StatusKind;
  summary: string;
  evidence_ref: string;
}
export interface V6PlatformUniverseRow {
  platform_id: string;
  platform: string;
  role: string;
  posture: string;
  status: StatusKind;
  manual_action: string;
  variant_key: string;
  payload_hash: string;
  copy_mode: string;
  media_fit: string;
  audit_evidence_mode: string;
  dispatch_gate: 'manual_review_only' | 'blocked_deferred' | 'blocked_live_scope_required';
}
export interface V6NewsImageCandidate {
  candidate_id: string;
  source_class: 'news_current_event';
  title: string;
  search_query: string;
  source_url_metadata: string;
  image_url_metadata: string;
  metadata_hash: string;
  selected_for_platforms: string[];
  license_notes: string;
  relevance_notes: string;
  public_fetch_performed: false;
  download_performed: false;
  rights_status: StatusKind;
}
export interface V6InternalChartCandidate {
  chart_id: string;
  source_class: 'capital_chronicle_internal_report';
  title: string;
  source_report: string;
  format: string;
  media_hash: string;
  selected_for_platforms: string[];
  fit_notes: string;
  alt_text: string;
  external_image_needed: false;
  rights_status: StatusKind;
}
export interface V6OperatorApprovalDecisionPacket {
  decision_packet_id: string;
  platform_id: string;
  platform: string;
  source_variant_key: string;
  payload_hash: string;
  decision: 'approve' | 'hold' | 'reject';
  decision_status: StatusKind;
  operator_evidence_mode: 'operator_supplied_fixture';
  operator_reference: string;
  rationale: string;
  next_required_action: string;
  decision_packet_hash: string;
  approval_recorded: boolean;
  dispatch_permission_granted: boolean;
  live_write_allowed: boolean;
  public_url_fetch_made: boolean;
  provider_or_api_call_made: boolean;
  browser_or_cdp_used: boolean;
}
export interface V6OperatorApprovalDecisionIntakeLaneModel {
  intake_status: StatusKind;
  intake_summary: string;
  evidence_policy: string;
  decision_packets: V6OperatorApprovalDecisionPacket[];
  forbidden_actions: string[];
}
export type V6LocalOutboxReadinessState =
  | 'approved_manual_ready'
  | 'held_for_revision'
  | 'rejected_blocked'
  | 'blocked_no_decision'
  | 'blocked_live_scope_required';
export interface V6LocalOutboxReadinessRow {
  row_id: string;
  platform_id: string;
  platform: string;
  source_variant_key: string;
  payload_hash: string;
  decision?: V6OperatorApprovalDecisionPacket['decision'];
  decision_packet_id?: string;
  decision_packet_hash?: string;
  readiness_state: V6LocalOutboxReadinessState;
  readiness_status: StatusKind;
  manual_next_action: string;
  outbox_entry_created: boolean;
  outbox_dispatchable: boolean;
  dispatch_allowed_now: boolean;
  live_write_allowed_now: boolean;
  scheduler_or_retry_wired: boolean;
  public_url_fetch_made: boolean;
  provider_or_api_call_made: boolean;
  browser_or_cdp_used: boolean;
  approval_ledger_live_write_made: boolean;
}
export interface V6LocalOutboxReadinessLaneModel {
  lane_status: StatusKind;
  reconciliation_summary: string;
  safety_policy: string;
  counts: Record<V6LocalOutboxReadinessState | 'total' | 'dispatchable', number>;
  readiness_rows: V6LocalOutboxReadinessRow[];
  blocked_actions: string[];
}
export interface V6OperatorBridgeStatusRow {
  bridge_id: string;
  platform_id: 'discord' | 'telegram';
  platform: 'Discord' | 'Telegram';
  source_evidence: string;
  operator_surface: string;
  bridge_state: 'dry_run_proven_no_send' | 'checkpoint_manual_only';
  status: StatusKind;
  payload_hash: string;
  manual_handoff: string;
  redacted_status: string;
  message_send_attempted: boolean;
  platform_api_called: boolean;
  webhook_or_bot_token_read: boolean;
  browser_or_cdp_used: boolean;
  public_url_fetch_made: boolean;
  scheduler_or_retry_wired: boolean;
  live_approval_ledger_written: boolean;
}
export interface V6OperatorBridgeLaneModel {
  lane_status: StatusKind;
  lane_summary: string;
  evidence_policy: string;
  bridge_rows: V6OperatorBridgeStatusRow[];
  blocked_actions: string[];
}
export interface V6ManualDeferredDistributionRow {
  lane_id: string;
  platform_id: 'facebook' | 'threads' | 'instagram' | 'tiktok' | 'generic_manual';
  platform: string;
  readiness_state: 'manual_handoff_only' | 'blocked_deferred' | 'fallback_manual_only';
  status: StatusKind;
  payload_hash: string;
  source_variant_key: string;
  blocker_summary: string;
  manual_handoff: string;
  media_requirement: string;
  audit_evidence_mode: string;
  live_write_allowed: boolean;
  platform_api_called: boolean;
  browser_or_cdp_used: boolean;
  public_url_fetch_made: boolean;
  media_download_or_upload_performed: boolean;
  scheduler_or_retry_wired: boolean;
  credential_or_env_read: boolean;
  approval_ledger_live_write_made: boolean;
}
export interface V6ManualDeferredDistributionLaneModel {
  lane_status: StatusKind;
  lane_summary: string;
  evidence_policy: string;
  rows: V6ManualDeferredDistributionRow[];
  blocked_actions: string[];
}
export interface V6MediaLaneModel {
  news_topic_id: string;
  news_policy: string;
  news_candidates: V6NewsImageCandidate[];
  internal_report_id: string;
  internal_policy: string;
  internal_chart_candidates: V6InternalChartCandidate[];
  forbidden_actions: string[];
}
export interface V6ManualAuditRow {
  row_id: string;
  platform: string;
  source_variant_key: string;
  payload_hash: string;
  approval_recorded: boolean;
  decision_packet_id?: string;
  decision?: V6OperatorApprovalDecisionPacket['decision'];
  public_url_status: 'operator_supplied_only' | 'not_applicable_until_manual_post';
  metrics_status: 'operator_supplied_only' | 'not_applicable_until_manual_post';
  evidence_mode: string;
  live_dispatch_performed: boolean;
  status: StatusKind;
}
export interface V6ManualAuditLaneModel {
  approval_status: StatusKind;
  approval_summary: string;
  dispatch_status: StatusKind;
  dispatch_summary: string;
  audit_summary: string;
  audit_rows: V6ManualAuditRow[];
  locked_actions: string[];
}
export interface V6FinalOperatorActionStripRow {
  action_id: string;
  label: string;
  source_lanes: string[];
  status: StatusKind;
  next_action: string;
  evidence_summary: string;
  payload_refs: string[];
  operator_owned: boolean;
  live_write_allowed: boolean;
  dispatch_allowed: boolean;
  platform_api_allowed: boolean;
  browser_or_cdp_allowed: boolean;
  public_url_fetch_allowed: boolean;
  media_download_or_upload_allowed: boolean;
  scheduler_or_retry_allowed: boolean;
  credential_or_env_read_allowed: boolean;
  approval_ledger_live_write_allowed: boolean;
}
export interface V6FinalOperatorActionStripLaneModel {
  strip_status: StatusKind;
  strip_summary: string;
  evidence_policy: string;
  rows: V6FinalOperatorActionStripRow[];
  blocked_actions: string[];
  terminal_next_task: string;
}
export interface V6FinalOperatorProductFlowModel {
  packet_id: string;
  packet_hash: string;
  builder_version: string;
  task_label: string;
  source_classes: string[];
  flow_stages: V6OperatorFlowStage[];
  platform_universe: V6PlatformUniverseRow[];
  media_lane: V6MediaLaneModel;
  operator_decision_intake_lane: V6OperatorApprovalDecisionIntakeLaneModel;
  local_outbox_readiness_lane: V6LocalOutboxReadinessLaneModel;
  operator_bridge_lane: V6OperatorBridgeLaneModel;
  manual_deferred_distribution_lane: V6ManualDeferredDistributionLaneModel;
  manual_audit_lane: V6ManualAuditLaneModel;
  final_operator_action_strip_lane: V6FinalOperatorActionStripLaneModel;
}
export interface V6CommandCenterModel {
  packet_id: string;
  task_label: string;
  release_status: string;
  final_verdict: string;
  packet_hash: string;
  north_star_loop: string[];
  rooms: V6CommandCenterRoom[];
  acceptance_criteria: V6CommandCenterCriterion[];
  metrics_matrix: V6CommandCenterMetricRow[];
  red_team_cases: V6CommandCenterRedTeamCase[];
  release_evidence_paths: string[];
  manual_remains_fallback: boolean;
  dispatch_allowed_now: boolean;
  live_write_allowed_now: boolean;
  deferred_until_post_final: string[];
  final_operator_product_flow: V6FinalOperatorProductFlowModel;
  publication_registry_audit: {
    task_label: string;
    status: StatusKind;
    detail: string;
    row_count: number;
    duplicate_natural_key_count: number;
    browser_or_cdp_probe_performed: boolean;
    public_url_fetch_made: boolean;
    x_api_used: boolean;
  };
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

export interface V6OperatorApprovalQueueItem {
  queue_item_id: string;
  platform: string;
  variant_id: string;
  preview_id: string;
  preview_hash: string;
  approval_status: string;
  live_dispatch_allowed: false;
  exact_preview_text_excerpt: string;
  required_operator_action: string;
}

export interface V6OperatorEvidenceVaultItem {
  evidence_id: string;
  evidence_type: string;
  source_file_path: string;
  source_packet_id: string;
  source_hash_or_preview_hash: string;
  display_status: string;
  caveats: string[];
  safety_flags: Record<string, boolean>;
}

export interface V6OperatorApprovalEvidencePacket {
  packet_id: string;
  source_article_packet_id: string;
  source_article_packet_hash: string;
  sample_scope: 'sample_fixture_only';
  runtime_proof: false;
  provider_call_made: false;
  network_call_made: false;
  live_send_performed: false;
  browser_session_used: false;
  raw_secret_values_serialized: false;
  env_lines_serialized: false;
  approval_queue_items: V6OperatorApprovalQueueItem[];
  evidence_vault_items: V6OperatorEvidenceVaultItem[];
  discord_outbox_card: {
    packet_id: string;
    outbox_id: string;
    approved_payload_hash: string;
    operator_approval_status: string;
    live_send_allowed: false;
    live_send_performed: false;
    sample_key_presence: {
      evidence_scope: 'sample_fixture_only';
      runtime_proof: false;
    };
  };
  live_pilot_status_card: {
    result_class: string;
    display_status: string;
    live_send_attempted: false;
    live_send_succeeded: false;
    blockers: string[];
  };
}

export interface JimDailyRunIdea {
  idea_id: string;
  title: string;
  lane: 'A_pre_alpha' | 'B_grounded_news' | 'C_artifact_backed';
  source_type: string;
  status: 'REVIEW_REQUIRED' | 'BLOCKED';
  allowed_transformations: string[];
  forbidden_transformations: string[];
  blockers: string[];
  next_allowed_manual_step: string;
}

export interface JimDailyRunSafetyFlags {
  local_only: boolean;
  fixture_only: boolean;
  jim_final_review_required: boolean;
  manual_export_only: boolean;
  public_postable: boolean;
  publish_ready: boolean;
  dispatch_ready: boolean;
  provider_api_called: boolean;
  network_called: boolean;
  browser_or_cdp_used: boolean;
  credential_or_env_read: boolean;
  platform_dispatch_performed: boolean;
  scheduler_enabled: boolean;
  public_url_verified: boolean;
}

export interface JimDailyContentRunPacket {
  task_label: string;
  contract_version: string;
  run_id: string;
  operator_id: string;
  run_status: string;
  surface_label: string;
  operator_summary: string;
  lane_counts: Record<string, number>;
  ideas: JimDailyRunIdea[];
  platform_preview_targets: string[];
  manual_export_state: string;
  next_allowed_action: string;
  forbidden_actions: string[];
  safety_flags: JimDailyRunSafetyFlags;
  packet_hash: string;
  packet_hash_algorithm: string;
}

export interface LocalCanonicalDraftPreviewReviewPacket {
  article_working_headline: string;
  canonical_draft_created: boolean;
  draft_generation_method: string;
  draft_preview_sections: readonly { section_title: string; section_body: string }[];
  draft_preview_status: string;
  draft_review_status: string;
  enabled_publish_send_dispatch_approve_controls: false;
  final_article_approved: false;
  final_operator_approval_required: boolean;
  live_action_allowed: false;
  llm_provider_call_made: false;
  network_call_made: false;
  platform_api_used: false;
  public_url_verification_performed: false;
  ready_for_auto_publish: false;
  ready_for_dispatch: false;
  ready_for_llm_drafting: false;
  ready_for_provider_drafting: false;
  operator_review_questions: readonly string[];
  packet_kind: string;
  separate_final_approval_task_required: boolean;
  separate_platform_variant_task_required: boolean;
  separate_publish_authorization_required: boolean;
  source_draft_authorization_packet_id: string;
  source_pack_intake_packet_id: string;
  task_label: string;
  working_title: string;
}

export interface PlatformVariantApprovalTarget {
  adapter_class: string;
  approval_required: boolean;
  approved: false;
  blocked_reason: string;
  credential_handle_status: string;
  destination_binding_status: string;
  dispatchable: false;
  exact_preview_text: string;
  no_metrics_claim: boolean;
  no_public_url_claim: boolean;
  payload_hash: string;
  platform_id: string;
  source_variant_key: string;
}

export interface PlatformVariantApprovalPacketPreviewPacket {
  actual_operator_approval_recorded: false;
  approval_ledger_entry_created: false;
  approval_packet_preview_created: boolean;
  approval_packet_preview_status: string;
  approval_record_created: false;
  approval_signature_present: false;
  approval_signature_required: boolean;
  approval_targets: Readonly<Record<string, PlatformVariantApprovalTarget>>;
  browser_session_used: false;
  credential_read_made: false;
  dispatch_outbox_ready: false;
  enabled_publish_send_dispatch_approve_controls: false;
  env_value_read_made: false;
  exact_payload_hash: string;
  exact_payload_hashes_created: boolean;
  exact_platform_payload_previews_created: boolean;
  final_article_approved: false;
  forbidden_financial_advice_or_signal_wording_present: false;
  live_action_allowed: false;
  live_publish_performed_by_contentops: false;
  llm_provider_call_made: false;
  network_call_made: false;
  outbox_entry_created: false;
  packet_kind: string;
  platform_api_used: false;
  platform_payloads_approved: false;
  platform_variant_final_review_status: string;
  platform_variant_final_review_to_approval_packet_preview_packet_id: string;
  provider_call_made: false;
  public_url_fetch_made: false;
  public_url_verification_performed: false;
  ready_for_auto_publish: false;
  ready_for_dispatch: false;
  source_final_review_packet_id: string;
  source_local_draft_preview_packet_id: string;
  task_label: string;
}

export interface CanonicalDraftFinalReviewVariantPreviewPacket {
  approval_record_created: false;
  browser_session_used: false;
  canonical_draft_final_review_status: string;
  canonical_draft_final_review_to_platform_variant_preview_packet_id: string;
  credential_read_made: false;
  enabled_publish_send_dispatch_approve_controls: false;
  env_value_read_made: false;
  exact_payload_hash: string;
  final_article_approved: false;
  forbidden_financial_advice_or_signal_wording_present: false;
  live_action_allowed: false;
  live_publish_performed_by_contentops: false;
  llm_provider_call_made: false;
  network_call_made: false;
  operator_final_approval_required: boolean;
  outbox_entry_created: false;
  packet_kind: string;
  platform_api_used: false;
  platform_payloads_approved: false;
  platform_variant_preview_status: string;
  platform_variants_are_preview_only: boolean;
  platform_variants_created: boolean;
  preview_variants: Readonly<Record<string, { readonly title: string; readonly body: string; readonly status: string }>>;
  provider_call_made: false;
  public_url_fetch_made: false;
  public_url_verification_performed: false;
  ready_for_auto_publish: false;
  ready_for_dispatch: false;
  source_draft_authorization_packet_hash: string;
  source_draft_review_packet_id: string;
  source_exact_payload_hash: string;
  source_local_draft_preview_packet_id: string;
  source_next_article_brief_packet_hash: string;
  source_pack_intake_packet_hash: string;
  task_label: string;
}

export interface JimDispatchOutboxDryRunEntry {
  adapter_class: string;
  approval_required: boolean;
  approved: boolean;
  blocked_reason?: string;
  credential_handle_status: string;
  deferred_reason?: string;
  destination_binding_status: string;
  dispatchable: boolean;
  dry_run_entry_id: string;
  dry_run_payload_hash: string;
  dry_run_payload_text: string;
  executable: boolean;
  no_metrics_claim: boolean;
  no_network_request_made: boolean;
  no_public_url_claim: boolean;
  no_secret_material_present: boolean;
  platform_id: string;
  request_body_hash_preview: string;
  request_method_preview: string;
  request_url_preview_status: string;
  source_approval_payload_hash: string;
  source_approval_target_key: string;
}

export interface JimDispatchOutboxDryRunPacket {
  actual_operator_approval_recorded: boolean;
  approval_ledger_entry_created: boolean;
  approval_record_created: boolean;
  approval_signature_present: boolean;
  approval_signature_required: boolean;
  browser_session_used: boolean;
  credential_read_made: boolean;
  dispatch_attempted: boolean;
  dispatch_outbox_dry_run_packet_id: string;
  dispatch_outbox_dry_run_status: string;
  dispatch_outbox_ready: boolean;
  dispatch_request_count: number;
  dry_run_entries: Readonly<Record<string, JimDispatchOutboxDryRunEntry>>;
  dry_run_entries_created: boolean;
  dry_run_outbox_package_created: boolean;
  enabled_publish_send_dispatch_approve_controls: boolean;
  env_value_read_made: boolean;
  exact_payload_hash: string;
  exact_payload_hashes_preserved: boolean;
  executable_outbox_entry_created: boolean;
  final_article_approved: boolean;
  forbidden_financial_advice_or_signal_wording_present: boolean;
  kill_switch_active: boolean;
  kill_switch_required: boolean;
  live_action_allowed: boolean;
  live_publish_performed_by_contentops: boolean;
  llm_provider_call_made: boolean;
  network_call_made: boolean;
  packet_kind: string;
  platform_api_request_count: number;
  platform_api_used: boolean;
  platform_payloads_approved: boolean;
  provider_call_made: boolean;
  public_url_fetch_made: boolean;
  public_url_verification_performed: boolean;
  ready_for_auto_publish: boolean;
  ready_for_dispatch: boolean;
  real_outbox_entry_created: boolean;
  retry_enabled: boolean;
  scheduler_enabled: boolean;
  source_approval_preview_exact_payload_hash: string;
  source_approval_preview_packet_id: string;
  source_draft_review_packet_id: string;
  source_final_review_hash: string;
  source_final_review_packet_id: string;
  source_local_draft_hash: string;
  source_local_draft_preview_packet_id: string;
  task_label: string;
  webhook_request_count: number;
}


export interface JimOperatorPreflightChecklist {
  check_id: string;
  label: string;
  status: string;
}

export interface JimManualDispatchFallbackStep {
  step_id: string;
  action: string;
  target: string;
}

export interface JimDryRunReplayStep {
  replay_id: string;
  action: string;
  status: string;
}

export interface JimRollbackAndStopCondition {
  condition_id: string;
  event: string;
  action: string;
}

export interface JimFailureModeMatrix {
  failure_mode: string;
  impact: string;
  recovery_action: string;
}

export interface JimEvidenceCollectionChecklist {
  item_id: string;
  label: string;
  status: string;
}

export interface JimDispatchOutboxOperatorRecoveryPacket {
  packet_kind: string;
  operator_recovery_status: string;
  recovery_runbook_created: boolean;
  manual_fallback_plan_created: boolean;
  rollback_plan_created: boolean;
  dry_run_replay_plan_created: boolean;
  failure_mode_matrix_created: boolean;
  evidence_collection_checklist_created: boolean;
  dispatch_preflight_checklist_created: boolean;
  executable_outbox_entry_created: boolean;
  real_outbox_entry_created: boolean;
  dispatch_outbox_ready: boolean;
  dispatch_attempted: boolean;
  dispatch_request_count: number;
  webhook_request_count: number;
  platform_api_request_count: number;
  scheduler_enabled: boolean;
  retry_enabled: boolean;
  kill_switch_required: boolean;
  kill_switch_active: boolean;
  actual_operator_approval_recorded: boolean;
  approval_ledger_entry_created: boolean;
  approval_record_created: boolean;
  approval_signature_present: boolean;
  approval_signature_required: boolean;
  platform_payloads_approved: boolean;
  final_article_approved: boolean;
  ready_for_auto_publish: boolean;
  ready_for_dispatch: boolean;
  live_action_allowed: boolean;
  public_url_verification_performed: boolean;
  llm_provider_call_made: boolean;
  provider_call_made: boolean;
  platform_api_used: boolean;
  network_call_made: boolean;
  public_url_fetch_made: boolean;
  env_value_read_made: boolean;
  credential_read_made: boolean;
  browser_session_used: boolean;
  live_publish_performed_by_contentops: boolean;
  enabled_publish_send_dispatch_approve_controls: boolean;
  forbidden_financial_advice_or_signal_wording_present: boolean;
  dispatch_outbox_operator_recovery_packet_id: string;
  exact_payload_hash: string;
  source_dispatch_outbox_dry_run_packet_id: string;
  source_dispatch_outbox_dry_run_exact_hash: string;
  source_approval_preview_packet_id: string;
  source_approval_preview_exact_hash: string;
  source_final_review_packet_id: string;
  source_final_review_hash: string;
  operator_preflight_checklist: JimOperatorPreflightChecklist[];
  manual_dispatch_fallback_steps: JimManualDispatchFallbackStep[];
  dry_run_replay_steps: JimDryRunReplayStep[];
  rollback_and_stop_conditions: JimRollbackAndStopCondition[];
  failure_mode_matrix: JimFailureModeMatrix[];
  evidence_collection_checklist: JimEvidenceCollectionChecklist[];
  platform_specific_recovery_notes: Record<string, string>;
  blocked_until_explicit_live_scope: boolean;
  task_label: string;
}

export interface JimContentIntent {
  intent_id: string;
  source_idea_id: string;
  title: string;
  content_lane: 'A_pre_alpha' | 'B_grounded_news' | 'C_artifact_backed';
  audience_mode: string;
  draft_objective: string;
  status: 'READY_FOR_JIM_REVIEW' | 'BLOCKED';
  source_requirement: string;
  claim_risk: string;
  forbidden_language_clear: boolean;
  blockers: string[];
  next_manual_step: string;
  final_public_copy_created: false;
  public_postable: false;
}

export interface JimPlatformPreviewPlaceholder {
  preview_id: string;
  platform: 'Substack' | 'X' | 'LinkedIn' | 'Telegram';
  source_intent_id: string;
  preview_shape: string;
  preview_status: 'PREVIEW_PLACEHOLDER_READY_FOR_JIM_REVIEW' | 'BLOCKED_WAITING_FOR_INPUTS';
  preview_text_excerpt: string;
  constraints: string[];
  missing_inputs: string[];
  approval_preconditions: string[];
  manual_export_ready: false;
  dispatch_ready: false;
  public_postable: false;
}

export interface JimVariantPreviewBundleSafetyFlags {
  local_only: boolean;
  fixture_only: boolean;
  jim_final_review_required: boolean;
  content_intent_created: boolean;
  platform_preview_placeholders_created: boolean;
  final_public_copy_created: boolean;
  llm_provider_called: boolean;
  provider_api_called: boolean;
  network_called: boolean;
  browser_or_cdp_used: boolean;
  credential_or_env_read: boolean;
  platform_api_called: boolean;
  platform_dispatch_performed: boolean;
  scheduler_enabled: boolean;
  public_url_verified: boolean;
  public_postable: boolean;
  publish_ready: boolean;
  dispatch_ready: boolean;
}

export interface JimVariantPreviewBundle {
  task_label: string;
  contract_version: string;
  bundle_id: string;
  source_run_id: string;
  operator_id: string;
  bundle_status: string;
  content_intents: JimContentIntent[];
  platform_targets: string[];
  platform_previews: JimPlatformPreviewPlaceholder[];
  intent_count: number;
  platform_preview_count: number;
  blocked_intent_count: number;
  manual_export_state: string;
  next_allowed_action: string;
  forbidden_actions: string[];
  safety_flags: JimVariantPreviewBundleSafetyFlags;
  packet_hash: string;
  packet_hash_algorithm: string;
}


export interface JimManualExportPacket {
  export_packet_id: string;
  source_intent_id: string;
  source_preview_id: string;
  platform: 'Substack' | 'X' | 'LinkedIn' | 'Telegram';
  title: string;
  manual_export_status: 'READY_FOR_MANUAL_COPY_AFTER_JIM_APPROVAL' | 'BLOCKED_WAITING_FOR_INPUTS';
  markdown_body: string;
  manual_export_checklist: string[];
  missing_inputs: string[];
  blocked_reasons: string[];
  requires_jim_final_approval: boolean;
  manual_copy_allowed_after_approval: boolean;
  final_public_copy_created: false;
  public_postable: false;
  dispatch_ready: false;
  public_url_verified: false;
  safety_flags: JimManualExportWorkbenchSafetyFlags;
  markdown_hash: string;
  export_hash: string;
}

export interface JimApprovalRecordPreview {
  approval_record_id: string;
  source_export_packet_id: string;
  source_export_hash: string;
  operator_id: string;
  approval_channel: string;
  approval_status: string;
  approval_text_redacted: string;
  valid_for_dispatch: false;
  public_postable: false;
  dispatch_ready: false;
  blocked_reasons: string[];
  safety_flags: JimManualExportWorkbenchSafetyFlags;
  approval_record_hash: string;
}

export interface JimManualExportWorkbenchSafetyFlags extends JimVariantPreviewBundleSafetyFlags {
  manual_export_only: boolean;
  jim_final_approval_required: boolean;
  approval_record_preview_created: boolean;
  approval_valid_for_dispatch: boolean;
}

export interface JimManualExportApprovalWorkbench {
  task_label: string;
  contract_version: string;
  workbench_id: string;
  source_bundle_id: string;
  operator_id: string;
  workbench_status: string;
  export_packet_count: number;
  ready_export_packet_count: number;
  blocked_export_packet_count: number;
  approval_record_preview_count: number;
  manual_export_packets: JimManualExportPacket[];
  approval_record_previews: JimApprovalRecordPreview[];
  operator_next_action: string;
  forbidden_actions: string[];
  safety_flags: JimManualExportWorkbenchSafetyFlags;
  workbench_hash: string;
  workbench_hash_algorithm: string;
}


export interface JimRedactedAuditMetricsSafetyFlags {
  local_only: boolean;
  operator_supplied_values_only: boolean;
  redacted_public_reference_only: boolean;
  jim_review_required: boolean;
  feedback_candidate_created: boolean;
  final_public_copy_created: boolean;
  llm_provider_called: boolean;
  provider_api_called: boolean;
  network_called: boolean;
  browser_or_cdp_used: boolean;
  credential_or_env_read: boolean;
  platform_api_called: boolean;
  platform_dispatch_performed: boolean;
  scheduler_enabled: boolean;
  scraping_performed: boolean;
  metrics_api_called: boolean;
  public_reference_verified: boolean;
  public_postable: boolean;
  publish_ready: boolean;
  dispatch_ready: boolean;
  baseline_promoted: boolean;
}

export interface JimManualPublishRecordPacket {
  audit_card_id: string;
  source_export_packet_id: string;
  source_export_hash: string;
  platform: 'Substack' | 'X' | 'LinkedIn' | 'Telegram';
  title: string;
  audit_status: string;
  operator_id: string;
  public_reference_redacted: string;
  operator_supplied_reference_only: boolean;
  public_reference_verified: false;
  network_checked: false;
  scraping_performed: false;
  captured_at_local: string;
  redaction_notes: string[];
  safety_flags: JimRedactedAuditMetricsSafetyFlags;
  audit_card_hash: string;
}

export interface JimMetricsImportPacket {
  metrics_packet_id: string;
  source_audit_card_id: string;
  source_audit_card_hash: string;
  platform: 'Substack' | 'X' | 'LinkedIn' | 'Telegram';
  metrics_status: string;
  operator_id: string;
  metrics_source: string;
  metrics_network_verified: false;
  metrics_api_called: false;
  metrics: Record<string, number>;
  normalized_engagement_total: number;
  quality_notes: string[];
  safety_flags: JimRedactedAuditMetricsSafetyFlags;
  metrics_packet_hash: string;
}

export interface JimFeedbackBacklogCandidate {
  candidate_id: string;
  source_audit_card_id: string;
  source_metrics_packet_id: string;
  platform: 'Substack' | 'X' | 'LinkedIn' | 'Telegram';
  title: string;
  candidate_status: string;
  recommendation: string;
  reason: string;
  requires_jim_review: boolean;
  baseline_promoted: false;
  safety_flags: JimRedactedAuditMetricsSafetyFlags;
  candidate_hash: string;
}

export interface JimRedactedAuditMetricsImportLoop {
  task_label: string;
  contract_version: string;
  loop_id: string;
  source_workbench_id: string;
  operator_id: string;
  loop_status: string;
  audit_card_count: number;
  metrics_packet_count: number;
  backlog_candidate_count: number;
  manual_publish_record_packets: JimManualPublishRecordPacket[];
  metrics_import_packets: JimMetricsImportPacket[];
  evidence_vault_cards: JimManualPublishRecordPacket[];
  feedback_backlog_candidates: JimFeedbackBacklogCandidate[];
  operator_next_action: string;
  forbidden_actions: string[];
  safety_flags: JimRedactedAuditMetricsSafetyFlags;
  loop_hash: string;
  loop_hash_algorithm: string;
}

export interface ContentOpsViewModel {
  system_state: SystemState;
  cockpit: CockpitViewModel;
  v6_command_center: V6CommandCenterModel;
  jim_daily_content_run: JimDailyContentRunPacket;
  local_canonical_draft_preview_review: LocalCanonicalDraftPreviewReviewPacket;
  canonical_draft_final_review_variant_preview: CanonicalDraftFinalReviewVariantPreviewPacket;
  platform_variant_approval_packet_preview: PlatformVariantApprovalPacketPreviewPacket;
  dispatch_outbox_dry_run: JimDispatchOutboxDryRunPacket;
  dispatch_outbox_operator_recovery: JimDispatchOutboxOperatorRecoveryPacket;
  jim_variant_preview_bundle: JimVariantPreviewBundle;
  jim_manual_export_workbench: JimManualExportApprovalWorkbench;
  jim_redacted_audit_metrics_loop: JimRedactedAuditMetricsImportLoop;
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
  v6_operator_approval_evidence: V6OperatorApprovalEvidencePacket;
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

export interface ArtifactIntakeSourceRef {
  system_id: string;
  relative_path: string;
  commit_sha: string;
}

export interface ArtifactIntakeCandidate {
  candidate_id: string;
  artifact_family: string;
  local_artifact_ref: string;
  source_system: string;
  lineage_ref: string;
  freshness_status: string;
  dqr_status: string;
  readiness_status: string;
  missing_or_degraded_labels: string[];
  citation_refs: string[];
  limitation_notes: string[];
  public_postable: boolean;
  dispatch_ready: boolean;
  review_required: boolean;
  blocked_reasons: string[];
}

export interface ArtifactIntakeValidationCheck {
  check_id: string;
  description: string;
  passed: boolean;
}

export interface ArtifactIntakeDecision {
  decision_id: string;
  candidate_id: string;
  verdict: string;
  review_required: boolean;
  blocked_reasons: string[];
}

export interface LaneCArtifactIntakeValidationPacket {
  task_label: string;
  matrix_version: string;
  source_baseline_commit: string;
  generated_at_epoch: number;
  artifact_candidate_count: number;
  validation_check_count: number;
  candidates: ArtifactIntakeCandidate[];
  validation_checks: ArtifactIntakeValidationCheck[];
  blocked_reasons: string[];
  missing_proofs: string[];
  safety_flags: Record<string, boolean>;
  local_only_classification: string;
  packet_hash: string;
  hash_algorithm: string;
  next_required_gate: string;
}

export interface LaneCConnectorFamily {
  connector_id: string;
  connector_family: string;
  current_status: string;
  allowed_path_pattern: string;
  required_file_kinds: string[];
  required_identity_fields: string[];
  required_hash_fields: string[];
  required_lineage_fields: string[];
  freshness_requirement: string;
  dqr_handling: string;
  readiness_handling: string;
  missing_degraded_proxy_label_handling: string;
  allowed_consumer_surfaces: string[];
  prohibited_effects: string[];
  next_required_gate: string;
}

export interface LaneCConnectorPathBoundary {
  allowed_path_pattern: string;
  symbolic_only: boolean;
  local_only: boolean;
}

export interface LaneCConnectorProofRequirement {
  connector_family: string;
  required_proofs: string[];
}

export interface LaneCConnectorReadinessDecision {
  connector_id: string;
  decision: string;
  blocked_reasons: string[];
}

export interface LaneCArtifactConnectorIndexPacket {
  task_label: string;
  matrix_version: string;
  source_baseline_commit: string;
  generated_at_epoch: number;
  connector_family_count: number;
  proof_requirement_count: number;
  connector_families: LaneCConnectorFamily[];
  path_boundaries: LaneCConnectorPathBoundary[];
  readiness_decisions: LaneCConnectorReadinessDecision[];
  blocked_reasons: string[];
  missing_proofs: string[];
  safety_flags: Record<string, boolean>;
  local_only_classification: string;
  packet_hash: string;
  hash_algorithm: string;
  next_required_gate: string;
}
