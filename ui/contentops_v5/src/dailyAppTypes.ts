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
  | 'audit';

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
    };
    rolling_24h_unique_headlines: number | null;
    capital_chronicle_read_model: string;
    provider_invocation_count: number;
    prompt_tokens: number;
    completion_tokens: number;
    cost_metadata: string;
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
