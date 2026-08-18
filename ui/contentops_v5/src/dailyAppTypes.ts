export type OperatingMode =
  | 'AUTONOMOUS_DEFAULT'
  | 'SUPERVISED_OPERATOR_GATE'
  | 'SHADOW_ONLY'
  | 'KILL_SWITCH';

export type DailyView =
  | 'today'
  | 'observation'
  | 'queue'
  | 'published'
  | 'performance'
  | 'learning'
  | 'platforms'
  | 'incidents'
  | 'controls'
  | 'background_logs'
  | 'audit';

export type ObservationLaneState =
  | 'LIVE_OBSERVATION'
  | 'SHADOW_READ_ONLY'
  | 'WAITING_FOR_REAL_OBJECT'
  | 'INSUFFICIENT_SAMPLE'
  | 'OPERATOR_SETUP_REQUIRED'
  | 'BLOCKED_OWNER_AUTHORITY'
  | 'DEGRADED'
  | 'UNAVAILABLE';

export interface ObservationLane {
  lane_contract_version: string;
  lane_id: string;
  group: 'V1' | 'V2' | 'CROSS_LANE';
  state: ObservationLaneState | string;
  data_source: string;
  authority_class: string;
  last_observed_at_utc: string | null;
  next_due_at_utc: string | null;
  sample_count: number | null;
  coverage: string | null;
  confidence: string | null;
  freshness: string | null;
  blocker: string | null;
  write_authority: string;
  notes: string | null;
  metrics: Record<string, unknown>;
}

export interface ObservationReadModel {
  schema_version: string;
  generated_at_utc: string;
  summary: {
    total_lanes: number;
    v1_lane_count: number;
    v2_lane_count: number;
    cross_lane_count: number;
    state_counts: Record<string, number>;
    v1_live_count: number;
    v2_shadow_count: number;
    blocked_count: number;
    insufficient_sample_count: number;
    operator_setup_required_count: number;
    zero_public_write_enforced: boolean;
  };
  v1_performance_windows: {
    '15m_early': number;
    '2h_intermediate': number;
    '24h_daily': number;
    '7d_long_tail': number;
  };
  v2_packages_detected: string[];
  lanes: ObservationLane[];
}

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
    latest_editorial_classification?: string;
    latest_article_update_mode?: string;
    latest_cc_matched_store_count?: number | null;
    latest_prior_related_article_title?: string | null;
    latest_prior_related_article_identity?: string | null;
    latest_material_delta_status?: string;
    latest_decision_reason?: string;
    latest_stage_stopped?: string;
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
  observation?: ObservationReadModel;
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
