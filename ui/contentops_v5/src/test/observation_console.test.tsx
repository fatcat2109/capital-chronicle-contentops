import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { DailyAppSnapshot } from '../dailyAppTypes';
import { DailyAppConsole } from '../views/DailyAppConsole';

function snapshot(overrides: Partial<DailyAppSnapshot> = {}): DailyAppSnapshot {
  const base: DailyAppSnapshot = {
    schema_version: 'contentops.daily_app_ui_snapshot.v1',
    generated_at_utc: '2026-08-15T12:00:00Z',
    freshness: { state: 'LIVE_CURRENT', source_last_updated_at_utc: '2026-08-15T11:58:00Z', source_age_seconds: 120, fresh_threshold_seconds: 300, provenance: 'canonical durable store' },
    runtime: {
      app_identity: 'Capital Chronicle ContentOps V1 — Daily App', operating_mode: 'AUTONOMOUS_DEFAULT', mode_state_version: 1,
      mode_updated_at_utc: '2026-08-15T12:00:00Z', mode_control_source: 'TEST', kill_switch_active: false, controller_health: 'HEALTHY',
      latest_heartbeat_at_utc: '2026-08-15T12:00:00Z', production_epoch_start_utc: null, last_tick_state: 'NO_TICK_RECORDED', last_tick_at_utc: null,
      next_wake_utc: null, next_editorial_window: null, operator_cycle_trigger: null, active_editorial_cycle_window_id: null,
      headline_freshness: 'LIVE_CURRENT', headline_ingestion: { lane_state: 'RUNNING', last_ingest_utc: '2026-08-15T11:56:00Z', rows_last_iteration: 5 },
      rolling_24h_unique_headlines: 612, capital_chronicle_read_model: 'READY', provider_invocation_count: 12, prompt_tokens: 4500, completion_tokens: 1200,
      cost_metadata: 'NORMAL_BUDGET',
    },
    today: { current_cycle: null, pending_lifecycle_recovery_count: 0, immediate_incident_count: 0, published_today_count: 1, published_corpus_count: 12, daily_target_band: [0, 4] },
    queue: { items: [], upcoming_editorial_windows: [], material_event_wake_state: 'CLEAR', active_or_held_work_count: 0, pending_readback_count: 0, due_performance_observation_count: 0 },
    published: { objects: [], real_publication_count: 1, controlled_no_public_write_count: 0, unknown_write_count: 0, pending_readback_count: 0, empty_reason: null },
    performance: { observations: [], real_observation_count: 0, empty_reason: null, empty_detail: null },
    learning: { active_policy: null, policy_history: [], empty_reason: null, configured_default: null },
    platforms: { destinations: [] },
    incidents: { items: [], active_count: 0, empty_reason: null },
    controls: {
      current_mode: 'AUTONOMOUS_DEFAULT', state_version: 1, updated_at_utc: '2026-08-15T12:00:00Z', control_source: 'TEST',
      allowed_modes: ['AUTONOMOUS_DEFAULT', 'SUPERVISED_OPERATOR_GATE', 'SHADOW_ONLY', 'KILL_SWITCH'], write_endpoint: '/api/daily-app/control/mode',
      run_now_endpoint: '/api/daily-app/control/run-now', run_now_allowed: true, run_now_mode_consequence: 'Runs one cycle.',
      semantics: { AUTONOMOUS_DEFAULT: 'Routine.', SUPERVISED_OPERATOR_GATE: 'Pause.', SHADOW_ONLY: 'Zero writes.', KILL_SWITCH: 'Block.' },
      unsafe_controls_available: false,
    },
    authority: { fixture_fallback: false, snapshot_mutates_lifecycle: false },
    observation: {
      schema_version: 'contentops.observation_read_model.v1',
      generated_at_utc: '2026-08-15T12:00:00Z',
      summary: {
        total_lanes: 19,
        v1_lane_count: 9,
        v2_lane_count: 8,
        cross_lane_count: 2,
        state_counts: { LIVE_OBSERVATION: 8, SHADOW_READ_ONLY: 5, BLOCKED_OWNER_AUTHORITY: 2, WAITING_FOR_REAL_OBJECT: 2, OPERATOR_SETUP_REQUIRED: 1, INSUFFICIENT_SAMPLE: 1 },
        v1_live_count: 5,
        v2_shadow_count: 3,
        blocked_count: 2,
        insufficient_sample_count: 3,
        operator_setup_required_count: 1,
        zero_public_write_enforced: true,
      },
      v1_performance_windows: { '15m_early': 4, '2h_intermediate': 2, '24h_daily': 1, '7d_long_tail': 0 },
      v2_packages_detected: ['v2_treasury_visual_material_richness_20260815'],
      lanes: [
        { lane_contract_version: 'contentops.observation_lane.v1', lane_id: 'V1_HEADLINE_INTAKE_FRESHNESS', group: 'V1', state: 'LIVE_OBSERVATION', data_source: 'DURABLE_STORE', authority_class: 'DURABLE', last_observed_at_utc: '2026-08-15T11:56:00Z', next_due_at_utc: null, sample_count: 612, coverage: 'Rolling 24h', confidence: 'EXACT', freshness: 'FRESH', blocker: null, write_authority: 'READ_ONLY', notes: 'Continuous intake', metrics: { rolling_24h_unique_headlines: 612 } },
        { lane_contract_version: 'contentops.observation_lane.v1', lane_id: 'V1_CANDIDATE_FUNNEL', group: 'V1', state: 'LIVE_OBSERVATION', data_source: 'WORK_ITEMS', authority_class: 'DURABLE', last_observed_at_utc: '2026-08-15T12:00:00Z', next_due_at_utc: null, sample_count: 12, coverage: 'Candidate funnel', confidence: 'EXACT', freshness: 'FRESH', blocker: null, write_authority: 'READ_ONLY', notes: null, metrics: { total_work_items: 12 } },
        { lane_contract_version: 'contentops.observation_lane.v1', lane_id: 'V1_EVIDENCE_SOURCE_HEALTH', group: 'V1', state: 'LIVE_OBSERVATION', data_source: 'SOURCES', authority_class: 'GOVERNED', last_observed_at_utc: '2026-08-15T12:00:00Z', next_due_at_utc: null, sample_count: null, coverage: 'Official sources', confidence: 'HIGH', freshness: 'FRESH', blocker: null, write_authority: 'READ_ONLY', notes: null, metrics: {} },
        { lane_contract_version: 'contentops.observation_lane.v1', lane_id: 'V1_PUBLICATION_SAFETY_RECOVERY', group: 'V1', state: 'LIVE_OBSERVATION', data_source: 'DISPATCHES', authority_class: 'DURABLE', last_observed_at_utc: '2026-08-15T12:00:00Z', next_due_at_utc: null, sample_count: 4, coverage: '9-surface readiness', confidence: 'EXACT', freshness: 'FRESH', blocker: null, write_authority: 'DURABLE_COORDINATOR', notes: null, metrics: { unknown_write_count: 0 } },
        { lane_contract_version: 'contentops.observation_lane.v1', lane_id: 'V1_REAL_PERFORMANCE_OBSERVATIONS', group: 'V1', state: 'LIVE_OBSERVATION', data_source: 'OBSERVATIONS', authority_class: 'DURABLE', last_observed_at_utc: '2026-08-15T12:00:00Z', next_due_at_utc: null, sample_count: 7, coverage: '4 observation windows', confidence: 'REAL_METRICS', freshness: 'FRESH', blocker: null, write_authority: 'READ_ONLY', notes: null, metrics: { formula_version: 'v1' } },
        { lane_contract_version: 'contentops.observation_lane.v1', lane_id: 'V1_PASSIVE_INTERACTION_QUALITY', group: 'V1', state: 'INSUFFICIENT_SAMPLE', data_source: 'INTERACTIONS', authority_class: 'DURABLE', last_observed_at_utc: null, next_due_at_utc: null, sample_count: 0, coverage: 'Passive categorisation', confidence: 'INSUFFICIENT', freshness: 'UNAVAILABLE', blocker: 'NO_SAMPLE', write_authority: 'DEFERRED_ZERO_WRITE_AUTHORITY', notes: 'Zero reply authority', metrics: {} },
        { lane_contract_version: 'contentops.observation_lane.v1', lane_id: 'V1_CLOSED_LOOP_LEARNING', group: 'V1', state: 'INSUFFICIENT_SAMPLE', data_source: 'POLICIES', authority_class: 'DURABLE', last_observed_at_utc: null, next_due_at_utc: null, sample_count: 0, coverage: 'Policy lineage', confidence: '0.0', freshness: 'CONFIGURED', blocker: null, write_authority: 'READ_ONLY', notes: 'Owner locked schedule', metrics: { owner_locked_schedule: true } },
        { lane_contract_version: 'contentops.observation_lane.v1', lane_id: 'V1_SEARCH_DISCOVERY', group: 'V1', state: 'OPERATOR_SETUP_REQUIRED', data_source: 'SEARCH_CONSOLE', authority_class: 'OPERATOR_SETUP', last_observed_at_utc: null, next_due_at_utc: null, sample_count: 0, coverage: 'Search impressions', confidence: 'NO_SAMPLE', freshness: 'UNAVAILABLE', blocker: 'OPERATOR_SETUP_REQUIRED', write_authority: 'READ_ONLY', notes: 'Post-canary setup', metrics: {} },
        { lane_contract_version: 'contentops.observation_lane.v1', lane_id: 'V1_COST_RUNTIME_YIELD', group: 'V1', state: 'LIVE_OBSERVATION', data_source: 'TELEMETRY', authority_class: 'DURABLE', last_observed_at_utc: '2026-08-15T12:00:00Z', next_due_at_utc: null, sample_count: 12, coverage: 'Tokens and cost', confidence: 'EXACT', freshness: 'CURRENT', blocker: null, write_authority: 'READ_ONLY', notes: null, metrics: { prompt_tokens: 4500 } },
        { lane_contract_version: 'contentops.observation_lane.v1', lane_id: 'V2_V1_TO_VIDEO_TRIGGER_SHADOW', group: 'V2', state: 'SHADOW_READ_ONLY', data_source: 'SHADOW_MAP', authority_class: 'SHADOW', last_observed_at_utc: '2026-08-15T12:00:00Z', next_due_at_utc: null, sample_count: 7, coverage: 'V1 to video mapping', confidence: 'SHADOW', freshness: 'CURRENT', blocker: null, write_authority: 'ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY', notes: 'No job auto-claim', metrics: { v2_video_jobs_claimed: 0 } },
        { lane_contract_version: 'contentops.observation_lane.v1', lane_id: 'V2_SOURCE_RIGHTS_ASSET_SUPPLY', group: 'V2', state: 'LIVE_OBSERVATION', data_source: 'ASSET_BOARD', authority_class: 'BOUNDED_ARTIFACT', last_observed_at_utc: '2026-08-15T12:00:00Z', next_due_at_utc: null, sample_count: 14, coverage: 'Rights-safe supply', confidence: 'VERIFIED', freshness: 'PACKAGE_BOUND', blocker: null, write_authority: 'ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY', notes: null, metrics: { accepted_assets_count: 11 } },
        { lane_contract_version: 'contentops.observation_lane.v1', lane_id: 'V2_ASSET_DIVERSITY_AND_SCREEN_TIME', group: 'V2', state: 'LIVE_OBSERVATION', data_source: 'RENDER_MANIFEST', authority_class: 'BOUNDED_ARTIFACT', last_observed_at_utc: '2026-08-15T12:00:00Z', next_due_at_utc: null, sample_count: 11, coverage: 'Exact reuse & screen time', confidence: 'EXACT', freshness: 'PACKAGE_BOUND', blocker: null, write_authority: 'ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY', notes: null, metrics: { total_screen_seconds: 615.8 } },
        { lane_contract_version: 'contentops.observation_lane.v1', lane_id: 'V2_PRODUCTION_TCO_RECOVERY_SOAK', group: 'V2', state: 'LIVE_OBSERVATION', data_source: 'HANDOFF', authority_class: 'BOUNDED_ARTIFACT', last_observed_at_utc: '2026-08-15T12:00:00Z', next_due_at_utc: null, sample_count: 1, coverage: 'Render & audio soak', confidence: 'PROVEN', freshness: 'PACKAGE_BOUND', blocker: null, write_authority: 'ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY', notes: null, metrics: { short_render_elapsed_ms: 120000 } },
        { lane_contract_version: 'contentops.observation_lane.v1', lane_id: 'V2_ACTUAL_MEDIA_QUALITY_OWNER_GATE', group: 'V2', state: 'LIVE_OBSERVATION', data_source: 'VISUAL_QA', authority_class: 'BOUNDED_ARTIFACT', last_observed_at_utc: '2026-08-15T12:00:00Z', next_due_at_utc: null, sample_count: 1, coverage: 'QA & owner review', confidence: 'WORKER_PASS', freshness: 'PACKAGE_BOUND', blocker: 'PENDING_JIM_CHATGPT_OWNER_ACCEPTANCE', write_authority: 'ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY', notes: 'Owner gate separation', metrics: { owner_acceptance_claimed: false } },
        { lane_contract_version: 'contentops.observation_lane.v1', lane_id: 'V2_PUBLICATION_READINESS', group: 'V2', state: 'LIVE_OBSERVATION', data_source: 'ZERO_WRITE_RECEIPT', authority_class: 'SAFETY', last_observed_at_utc: '2026-08-15T12:00:00Z', next_due_at_utc: null, sample_count: null, coverage: '6-surface shadow control plane', confidence: 'EXACT', freshness: 'PACKAGE_BOUND', blocker: null, write_authority: 'ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY', notes: null, metrics: { public_writes: 0 } },
        { lane_contract_version: 'contentops.observation_lane.v1', lane_id: 'V2_POST_PUBLISH_RETENTION_ATTRIBUTION', group: 'V2', state: 'BLOCKED_OWNER_AUTHORITY', data_source: 'RETENTION_CHANNEL', authority_class: 'OWNER_GATE', last_observed_at_utc: null, next_due_at_utc: null, sample_count: 0, coverage: 'Retention curve', confidence: 'BLOCKED', freshness: 'UNAVAILABLE', blocker: 'ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY', write_authority: 'ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY', notes: 'Zero public video writes', metrics: { published_video_count: 0 } },
        { lane_contract_version: 'contentops.observation_lane.v1', lane_id: 'V2_CLOSED_LOOP_VIDEO_LEARNING', group: 'V2', state: 'WAITING_FOR_REAL_OBJECT', data_source: 'POLICY', authority_class: 'LEARNING', last_observed_at_utc: null, next_due_at_utc: null, sample_count: 0, coverage: 'Video learning', confidence: 'INSUFFICIENT', freshness: 'WAITING', blocker: 'INSUFFICIENT_SAMPLE', write_authority: 'ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY', notes: null, metrics: {} },
        { lane_contract_version: 'contentops.observation_lane.v1', lane_id: 'CROSS_LANE_SOURCE_ACCESS_HEALTH', group: 'CROSS_LANE', state: 'LIVE_OBSERVATION', data_source: 'ACQUISITION_SANDBOX', authority_class: 'GOVERNED', last_observed_at_utc: '2026-08-15T12:00:00Z', next_due_at_utc: null, sample_count: null, coverage: 'API and HTML access', confidence: 'NO_WAF_BYPASS', freshness: 'CURRENT', blocker: null, write_authority: 'READ_ONLY', notes: null, metrics: {} },
        { lane_contract_version: 'contentops.observation_lane.v1', lane_id: 'CROSS_LANE_DATA_FRESHNESS_AND_AUTHORITY', group: 'CROSS_LANE', state: 'LIVE_OBSERVATION', data_source: 'PROJECTION', authority_class: 'CONTRACT', last_observed_at_utc: '2026-08-15T12:00:00Z', next_due_at_utc: null, sample_count: 19, coverage: 'Unified freshness', confidence: 'EXACT', freshness: 'LIVE', blocker: null, write_authority: 'READ_ONLY', notes: null, metrics: { total_lanes: 19 } },
      ],
    },
    audit: { work_item_count: 0, transition_event_count: 0, artifact_reference_count: 0, review_record_count: 0, recent_events: [], state_counts: {}, provenance: 'canonical' },
  };
  return { ...base, ...overrides };
}

function respond(data: DailyAppSnapshot) {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => data }));
}

afterEach(() => { vi.unstubAllGlobals(); vi.unstubAllEnvs(); });

describe('Observation & Closed Learning Console View', () => {
  it('renders all 19 locked lanes when navigating to Observation / Learning', async () => {
    respond(snapshot());
    render(<DailyAppConsole />);

    const navBtn = await screen.findByRole('button', { name: /observation \/ learning/i });
    fireEvent.click(navBtn);

    // Verify view title and section headings
    expect(screen.getByRole('heading', { level: 1, name: 'Observation / Learning' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: /v1 natural observation lanes/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: /v2 shadow \/ soak \/ blocked learning lanes/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: /cross-lane source access/i })).toBeInTheDocument();

    // Verify key lane cards exist
    expect(screen.getByText('V1_HEADLINE_INTAKE_FRESHNESS')).toBeInTheDocument();
    expect(screen.getByText('V1_CANDIDATE_FUNNEL')).toBeInTheDocument();
    expect(screen.getByText('V1_EVIDENCE_SOURCE_HEALTH')).toBeInTheDocument();
    expect(screen.getByText('V1_PUBLICATION_SAFETY_RECOVERY')).toBeInTheDocument();
    expect(screen.getByText('V1_REAL_PERFORMANCE_OBSERVATIONS')).toBeInTheDocument();
    expect(screen.getByText('V2_ASSET_DIVERSITY_AND_SCREEN_TIME')).toBeInTheDocument();
    expect(screen.getByText('V2_ACTUAL_MEDIA_QUALITY_OWNER_GATE')).toBeInTheDocument();
    expect(screen.getByText('V2_POST_PUBLISH_RETENTION_ATTRIBUTION')).toBeInTheDocument();
    expect(screen.getByText('CROSS_LANE_SOURCE_ACCESS_HEALTH')).toBeInTheDocument();
  });

  it('enters report mode and suppresses interactive controls for clean screenshots', async () => {
    respond(snapshot());
    render(<DailyAppConsole />);

    const navBtn = await screen.findByRole('button', { name: /observation \/ learning/i });
    fireEvent.click(navBtn);

    const reportBtn = screen.getByRole('button', { name: /screenshot \/ report mode/i });
    fireEvent.click(reportBtn);

    // Verify report banner is rendered with title and legend
    expect(screen.getByText('AUDIT REPORT')).toBeInTheDocument();
    expect(screen.getByText(/Capital Chronicle ContentOps — Natural Observation & Closed Learning Control Room/i)).toBeInTheDocument();
    expect(screen.getAllByText(/LIVE OBSERVATION/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/SHADOW READ ONLY/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/BLOCKED OWNER AUTHORITY/i).length).toBeGreaterThan(0);

    // Exit report mode button
    const exitBtn = screen.getByRole('button', { name: /exit report mode/i });
    expect(exitBtn).toBeInTheDocument();
    fireEvent.click(exitBtn);

    expect(screen.queryByText('AUDIT REPORT')).not.toBeInTheDocument();
  });
});
