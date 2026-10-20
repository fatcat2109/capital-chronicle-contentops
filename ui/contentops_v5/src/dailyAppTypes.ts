export type OperatingMode =
  | 'AUTONOMOUS_DEFAULT'
  | 'SUPERVISED_OPERATOR_GATE'
  | 'SHADOW_ONLY'
  | 'KILL_SWITCH';

export type DailyView =
  | 'today'
  | 'queue'
  | 'published'
  | 'performance'
  | 'learning'
  | 'platforms'
  | 'incidents'
  | 'controls'
  | 'background_logs'
  | 'audit';

export interface HourlyAudit {
  schema_version: string;
  generated_at_utc: string | null;
  classification: string;
  classification_reasons?: string[];
  runtime?: Record<string, unknown>;
  browsers?: Record<string, unknown>;
  browser_interaction?: Record<string, unknown>;
  safety?: Record<string, unknown>;
  stderr_signal?: Record<string, unknown>;
  scheduled_task?: Record<string, unknown>;
  status?: string;
}

export interface HostPreflight {
  schema_version: string;
  status: string;
  observed_at_utc: string | null;
  freshness: string;
  age_seconds?: number | null;
  source: string;
  scheduler: {
    status: string;
    task_count: number | null;
    tasks: Array<Record<string, unknown>>;
  };
  process: {
    status: string;
    matching_process_count: number | null;
  };
  store: {
    status: string;
    integrity_check: string;
    foreign_key_violation_count: number;
    unknown_write_count: number;
  };
  edge: {
    status: string;
    cdp_port: number;
    profile: string;
    destination_identity_status: string;
  };
  publication: {
    state: string;
    public_write_performed: boolean | null;
  };
  blockers: string[];
}

export interface BackgroundLogTail {
  schema_version: string;
  stream: string;
  label: string;
  status: string;
  line_count: number;
  truncated: boolean;
  latest_timestamp_utc: string | null;
  content: string;
}

export type RuntimePrimaryState =
  | 'STOPPED' | 'STARTING' | 'RUNNING_IDLE' | 'INGESTING' | 'PREPARING'
  | 'RESEARCHING' | 'WRITING' | 'MEDIA_BUILDING' | 'PACKAGING'
  | 'PUBLISHING' | 'READING_BACK' | 'RECONCILING' | 'DEGRADED'
  | 'ACTION_REQUIRED';

export interface RuntimeActivityRow {
  activity_type: string;
  work_item_id: string | null;
  started_at_utc: string | null;
  completed_at_utc: string | null;
  duration_seconds: number | null;
  story_label: string | null;
  candidate_rank: number | null;
  candidate_count: number | null;
  grounding: string | null;
  research_result: string | null;
  result: string;
  exact_reason: string | null;
  canonical_public_url: string | null;
}

export interface RuntimeCockpit {
  schema_version: 'contentops.daily_app_runtime_cockpit.v1';
  primary_state: RuntimePrimaryState;
  supervisor_state: string;
  controller_health: string;
  publication_runtime_health: string;
  output_health?: string;
  operating_mode: OperatingMode;
  runtime_sha_short: string;
  local_timezone: string;
  current_time_utc: string;
  heartbeat_age_seconds: number | null;
  current_activity: null | {
    work_item_id: string;
    cycle_started_at_utc: string | null;
    stage_started_at_utc: string | null;
    current_stage: string;
    story_label: string | null;
    candidate_rank: number | null;
    candidate_count: number | null;
    grounding: string | null;
    destination: string | null;
    trigger: string | null;
    instrumentation_state: string;
  };
  timeline: Array<{ stage: string; label: string; state: 'completed' | 'current' | 'pending' }>;
  schedule: {
    idle_healthy: boolean;
    next_editorial_wake_utc: string | null;
    next_editorial_wake_reason: string;
    operator_trigger_pending: boolean;
    next_x_eligible_capture_utc: string | null;
    x_cadence_state: string;
  };
  last_completed_editorial: RuntimeActivityRow | null;
  intake: {
    lane_state: string;
    last_ingest_utc: string | null;
    latest_capture_at_utc: string | null;
    latest_capture_result: string;
    rows_last_iteration: number;
    newest_source_event_at_utc: string | null;
    newest_source_event_age_seconds: number | null;
    next_eligible_capture_utc?: string | null;
    cadence_state?: string;
    rolling_24h_unique_headlines: number | null;
  };
  safety: {
    active_public_write: boolean;
    pending_reconciliation_count: number;
    pending_readback_recovery_count: number;
    unknown_write_count: number;
    kill_switch_active: boolean;
    new_public_writes_blocked: boolean;
  };
  browser: {
    state: string;
    external_browser_activity_active: boolean;
    last_active_at_utc: string | null;
    last_reason: string | null;
    last_destination: string | null;
  };
  recent_activity: RuntimeActivityRow[];
}

export interface DailyAppSnapshot {
  editorial_execution_target?: {
    owner: string; model: string; reasoning_effort: string; target_status: string;
    deployed_state: string; public_write_authority: boolean;
    editorial_roles?: Record<string, { model: string; reasoning_effort: string }>;
    role_settings_state?: string;
  };
  schema_version: string;
  generated_at_utc: string;
  freshness: {
    state: string;
    source_last_updated_at_utc: string | null;
    source_age_seconds: number | null;
    fresh_threshold_seconds: number;
    provenance: string;
  };
  runtime: {
    app_identity: string;
    operating_mode: OperatingMode;
    mode_state_version: number;
    mode_updated_at_utc: string;
    mode_control_source: string;
    kill_switch_active: boolean;
    controller_health: string;
    latest_heartbeat_at_utc: string | null;
    production_epoch_start_utc: string | null;
    last_tick_state: string;
    last_tick_at_utc: string | null;
    next_wake_utc: string | null;
    next_editorial_window: Record<string, unknown> | null;
    operator_cycle_trigger: Record<string, unknown> | null;
    active_editorial_cycle_window_id: string | null;
    headline_freshness: string;
    headline_ingestion: {
      lane_state: string;
      last_ingest_utc: string | null;
      rows_last_iteration: number;
      next_eligible_capture_utc?: string | null;
      cadence_state?: string;
    };
    browser_automation?: {
      state: string;
      last_active_browser_interaction_at_utc: string | null;
      last_reason: string | null;
      last_destination?: string | null;
    };
    rolling_24h_unique_headlines: number | null;
    capital_chronicle_read_model: string;
    provider_invocation_count: number;
    prompt_tokens: number;
    completion_tokens: number;
    cost_metadata: string;
    operator_cockpit?: RuntimeCockpit;
  };
  today: {
    current_cycle: null | Record<string, unknown>;
    pending_lifecycle_recovery_count: number;
    immediate_incident_count: number;
    published_today_count: number;
    published_corpus_count: number;
    daily_target_band: number[];
    newsroom_production_day_id?: string;
    build_qualified_floor?: number;
    final_published_target_min?: number;
    final_published_target_max?: number;
    qualified_articles_today?: number;
    published_articles_today?: number;
    remaining_build_deficit?: number;
    production_day_state?: string;
    hard_external_block_reason?: string | null;
    routine_opportunities_used?: number;
    routine_opportunities_remaining?: number;
    latest_editorial_classification?: string;
    latest_article_update_mode?: string;
    latest_cc_matched_store_count?: number | null;
    latest_prior_related_article_title?: string | null;
    latest_prior_related_article_identity?: string | null;
    latest_material_delta_status?: string;
    latest_decision_reason?: string;
    latest_stage_stopped?: string;
    report_bridge?: ReportWorkspaceData;
  };
  queue: {
    items: Array<Record<string, unknown>>;
    upcoming_editorial_windows: Array<Record<string, unknown>>;
    material_event_wake_state: string;
    pending_material_event_count?: number;
    active_or_held_work_count: number;
    pending_readback_count: number;
    due_performance_observation_count: number;
  };
  published: {
    objects: Array<Record<string, unknown>>;
    real_publication_count: number;
    controlled_no_public_write_count: number;
    unknown_write_count: number;
    pending_readback_count: number;
    empty_reason: string | null;
  };
  performance: {
    observations: Array<Record<string, unknown>>;
    collector_capabilities?: Array<Record<string, unknown>>;
    scheduled_observation_count?: number;
    collected_observation_count?: number;
    real_observation_count: number;
    empty_reason: string | null;
    empty_detail: string | null;
  };
  learning: {
    active_policy: Record<string, unknown> | null;
    policy_history: Array<Record<string, unknown>>;
    empty_reason: string | null;
    configured_default: Record<string, unknown> | null;
  };
  platforms: { destinations: Array<Record<string, unknown>> };
  incidents: {
    items: Array<Record<string, unknown>>;
    active_count: number;
    empty_reason: string | null;
  };
  hourly_audit?: HourlyAudit;
  host_preflight?: HostPreflight;
  automation?: {
    configured_intent: Record<string, unknown>;
    observed_host_state: Record<string, unknown>;
    observation_timestamp_utc: string | null;
    freshness: string;
    age_seconds?: number;
  };
  controls: {
    current_mode: OperatingMode;
    state_version: number;
    updated_at_utc: string;
    control_source: string;
    allowed_modes: OperatingMode[];
    write_endpoint: string;
    run_now_endpoint: string;
    run_now_allowed: boolean;
    run_now_mode_consequence: string;
    shutdown_endpoint?: string;
    shutdown_allowed?: boolean;
    shutdown_blockers?: string[];
    background_logs_endpoint?: string;
    background_log_streams?: Array<{ stream: string; label: string }>;
    hourly_audit_endpoint?: string;
    semantics: Record<OperatingMode, string>;
    unsafe_controls_available: boolean;
  };
  authority: Record<string, unknown>;
  audit: {
    work_item_count: number;
    transition_event_count: number;
    artifact_reference_count: number;
    review_record_count: number;
    recent_events: Array<Record<string, unknown>>;
    state_counts: Record<string, number>;
    provenance: string;
  };
}

export type LoadState =
  | { kind: 'loading'; snapshot: null; error: null }
  | { kind: 'online'; snapshot: DailyAppSnapshot; error: null }
  | { kind: 'offline'; snapshot: DailyAppSnapshot | null; error: string };


export interface ResearchPackage {
  brief_id: string; article_identity: string; stage: string; source_revision_current: boolean;
  package_revision?: string; editorial_kind?: string;
  article: NonNullable<ReportWorkspaceData['article']>;
  validation: { status: string; semantic_editorial_review: string; blockers: string[] };
  previews: Record<string, Record<string, unknown>>;
  media_assets: Array<{ asset_id: string; caption: string; preview_data_url?: string; alt_text?: string; sha256: string }>;
  review?: { state: string; latest_review_id: string | null; rationale?: string | null; history: Array<{ review_id: string; reviewed_at: string; decision: string; rationale: string; package_revision: string }> };
  supporting_claims?: Array<{ item_id: string; proposition: string; context_kind: string; source_url: string; published_at_utc: string | null; known_at_utc: string; rights_state: string; text_sha256: string; source_capture_sha256: string; permission_sha256: string }>;
  counterevidence?: Array<{ kind?: string; relation?: string; text: string; editorial_inference?: string; source_item_ids?: string[]; external_counterevidence_observed: boolean }>;
  missing_current_inputs?: string[];
}

export interface EvolvingStory {
  story_identity: string; update_chain_identity: string; brief_id: string; title: string; families: string[];
  disposition: string; reason: string; reader_question: string; follow_up_value: string;
  changed_source_count: number; brief_changed: boolean; work_required: boolean; missing_inputs: string[];
  publication_state: string; confirmation_state: string;
  epistemic_states?: Array<{ item_id: string; state: string; context_kind: string; scope: string }>;
  current_review?: ResearchPackage['review'];
  prior_package: null | { article_identity: string; title: string; full_text: string; stage: string };
  package_history: Array<{ article_identity: string; title: string; full_text?: string; package_sequence: number; stage: string }>;
  evidence_delta: Array<{ item_id: string; state: string; material: boolean; before: null | { proposition: string; source_url: string; rights_state: string }; after: null | { proposition: string; source_url: string; rights_state: string } }>;
  main_history: Array<{ report_id: string; report_version: number; change_kind: string; status: string; withdrawal_only?: boolean; withdrawn?: boolean; known_at_cutoff_utc: string; changed_claims: Array<{ claim_id: string; before: null | { text: string; producer_layer: string }; after: null | { text: string; producer_layer: string } }> }>;
  published_prior?: null | { previous_title: string; previous_canonical_url: string; previous_full_text: string; previous_published_at_utc: string };
  canonical_memory_article_count?: number;
}

export interface ReportWorkspaceData {
  media_assets?: Array<{ asset_id: string; path: string; sha256: string; caption: string; alt_text?: string; preview_data_url?: string; reuse_state?: string }>;
  native_article_reviews?: Array<{ article_identity: string; decision: string; rationale: string; package_revision: string; publication_authority: boolean }>;
  foundation_library?: {
    stories?: EvolvingStory[];
    publication_memory?: { observed_at_utc: string; article_count: number; source: string };
    research_revision: string; observed_at_utc: string;
    desk?: { decisions: Record<string, number>; useful_research_packages: number; missing_current_input_coordinates: string[]; kind_counts: Record<string, number>; affected_work: Array<{ brief_id: string; reason: string }> };
    counts: { independent_items: number; independent_documents?: number; useful_families: number; briefs: number; fresh_provider_drafts: number; qualified: number; published: number; editor_authored_packages?: number; native_previews?: number; media?: number };
    input_composition?: { independent_research_items: number; evidence_complete_briefs: number; main_editorial_reports: number; main_unchanged_reports: number; main_history_only_reports: number; owner: string; routine_window_count: number; model_execution_state: string };
    packages?: ResearchPackage[];
    families: Array<{ family: string; useful_items: number; briefs: number; missing_inputs: string[] }>;
    items: Array<{ item_id: string; family: string; assets: string[]; horizons: string[]; proposition: string; context_kind: string; source_url: string; source_identity: string; rights_state: string; permission_sha256: string; source_capture_sha256: string; originality: string; known_at_utc: string; published_at_utc: string | null; source_modified_at_utc?: string | null; next_editorial_question: string; correction_of?: string | null }>;
    briefs: Array<{ brief_id: string; title: string; families: string[]; stage: string; source_item_ids: string[]; audience_value: string; mechanism: string; competing_explanation: string; scenarios: string[]; falsifiers: string[]; missing_inputs: string[]; next_question: string; facts: Array<{ item_id: string; text: string; source_url: string; text_sha256: string }> }>;
    gaps: Array<{ state: string }>; next_operation: string;
    main_reports?: Array<{ report_id: string; report_version: number; asset_ids: string[]; families: string[]; status: string; change_kind: string; withdrawn: boolean; originality: string; next_editorial_question: string; context_kind: string; changed_claim_ids: string[]; limitations?: string[]; horizons: Array<{ horizon: string; trading_sessions: number; outlook: string }>; public_claims: Array<{ claim_id: string; producer_layer: string; text: string; freshness_state: string; exact_or_proxy: string; basis_risk?: string | null; evidence?: Array<{ evidence_id: string; source_url: string; observation_time_utc: string | null; known_at_utc: string | null; retrieval_time_utc: string | null; freshness_state: string; pit_state: string; exact_or_proxy: string; rights_state: string }> }> }>;
    report_admissions_and_noops?: Record<string, number>;
  } | null;
  source_inventory?: { independent_items: number; main_origin_recirculated_items: number; scope: string };
  freshness?: { report_age_at_last_scan_seconds: number | null; claims: string[]; current_market_refresh_verified: boolean; scope: string };
  independent_results?: Array<{ classification: string; model_execution_state: string; article_identity: string; article: ReportWorkspaceData['article']; previews: ReportWorkspaceData['previews']; evidence?: Array<{ source_id: string; url: string; publisher: string; published_at_utc: string }>; media_assets?: Array<{ asset_id: string; caption: string; path: string; sha256: string; underlying_source_rights_status: string; preview_data_url?: string; alt_text?: string }> }>;
  conversion?: { independent_drafts: number; main_drafts: number; fresh_provider_drafts: number; controlled_drafts: number };
  next_operation?: string;
  latest_attempt?: { classification: string; model_execution_state?: string; exact_next_blocker?: string } | null;
  feed?: { producer_commit: string; observed_at_utc: string; configured_bundle_count: number; new_events: number; coverage: string; events: Array<{ report_id: string; report_version: number; state: string; blockers?: string[] }>; gaps: Array<{ state: string }> } | null;
  report_age_at_last_scan_seconds?: number | null;
  opportunities?: Array<{ opportunity_id: string; classification: string; exact_next_blocker?: string; report_candidates: Array<{ report_id: string; report_version: number; state: string }> }>;
  headline_export?: { source_rows_scanned: number; eligible_rows: number; missing_rows: number; coverage: string; observed_at_utc: string; independent_items?: number; main_origin_recirculated_items?: number; gaps?: Array<{ state: string }> } | null;
  report_history?: Array<{ report_id: string; report_version: number; status: string; change_kind?: string }>;
  schema_version: string;
  state: string;
  report_events_received: number;
  latest_report: null | {
    report_id: string;
    report_version: number;
    source_report_sha256?: string;
    known_at_cutoff_utc?: string;
    change_kind?: string;
    claims?: Array<{ claim_id: string; text: string; producer_layer: string; basis_risk?: string; evidence: Array<{ evidence_id: string; source_url: string; pit_state?: string; rights_state?: string }> }>;
    missing_claims?: string[];
    horizon_blocks?: Array<{ horizon: string; trading_sessions: number; outlook: string }>;
    withdrawal_only?: boolean;
    materiality_rationale?: string;
    producer_binding?: { producer_commit?: string; producer_pull_request?: string };
    contract_revision?: string;
  };
  latest_editorial_input?: Record<string, unknown> | null;
  latest_simple_result?: { classification?: string; model_execution_state?: string; draft_count?: number; preview_count?: number; claim_lineage?: Array<Record<string, unknown>> } | null;
  article: null | { title: string; dek: string; substack_body_markdown: string };
  previews: Array<{ destination: string; preview_id: string; article_identity: string; payload: Record<string, unknown>; claim_lineage: Array<Record<string, unknown>> }>;
  history: Array<{ report_version: number; state: string; article_identity: string; preview_ids: string[]; superseded_by_version: number }>;
  workspaces?: ReportWorkspaceData[];
  named_blocker: string | null;
  public_write_performed: boolean;
}
