import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { DailyAppSnapshot, RuntimePrimaryState } from '../dailyAppTypes';
import { SimpleRunDashboard } from '../views/SimpleRunDashboard';

function snapshot(primary: RuntimePrimaryState = 'RUNNING_IDLE'): DailyAppSnapshot {
  const running = primary === 'RESEARCHING';
  return {
    schema_version: 'contentops.daily_app_ui_snapshot.v1',
    generated_at_utc: '2026-08-24T10:40:00Z',
    freshness: { state: 'FRESH', source_last_updated_at_utc: '2026-08-24T10:40:00Z', source_age_seconds: 2, fresh_threshold_seconds: 30, provenance: 'TEST' },
    runtime: {
      app_identity: 'V1', operating_mode: 'SHADOW_ONLY', mode_state_version: 30,
      mode_updated_at_utc: '2026-08-24T10:36:00Z', mode_control_source: 'TEST', kill_switch_active: false,
      controller_health: 'HEALTHY', latest_heartbeat_at_utc: '2026-08-24T10:40:00Z',
      production_epoch_start_utc: '2026-08-24T10:36:00Z', last_tick_state: 'IDLE',
      last_tick_at_utc: '2026-08-24T10:40:00Z', next_wake_utc: '2026-08-24T14:00:00Z',
      next_editorial_window: null, operator_cycle_trigger: null,
      active_editorial_cycle_window_id: running ? 'window-2100' : null,
      headline_freshness: 'FRESH',
      headline_ingestion: { lane_state: 'RUNNING', last_ingest_utc: '2026-08-24T10:39:00Z', rows_last_iteration: 4 },
      rolling_24h_unique_headlines: 121, capital_chronicle_read_model: 'READY',
      provider_invocation_count: 0, prompt_tokens: 0, completion_tokens: 0, cost_metadata: 'AVAILABLE',
      operator_cockpit: {
        schema_version: 'contentops.daily_app_runtime_cockpit.v1', primary_state: primary,
        supervisor_state: 'RUNNING', controller_health: 'HEALTHY', publication_runtime_health: 'HEALTHY',
        output_health: 'HEALTHY', operating_mode: 'SHADOW_ONLY', runtime_sha_short: '75d5f2a6',
        local_timezone: 'Asia/Bangkok', current_time_utc: '2026-08-24T10:40:00Z', heartbeat_age_seconds: 2,
        current_activity: running ? { work_item_id: 'work-1', cycle_started_at_utc: '2026-08-24T10:36:00Z', stage_started_at_utc: '2026-08-24T10:39:00Z', current_stage: 'GROUNDED_RESEARCH', story_label: 'A governed market story', candidate_rank: 1, candidate_count: 5, grounding: 'source-bound', destination: null, trigger: 'SCHEDULED', instrumentation_state: 'CURRENT' } : null,
        timeline: running ? [
          { stage: 'HEADLINE_INGESTION', label: 'Intake', state: 'completed' },
          { stage: 'CANDIDATE_SELECTION', label: 'Selection', state: 'completed' },
          { stage: 'GROUNDED_RESEARCH', label: 'Research', state: 'current' },
          { stage: 'ARTICLE_WRITING', label: 'Write', state: 'pending' },
        ] : [],
        schedule: { idle_healthy: !running, next_editorial_wake_utc: '2026-08-24T14:00:00Z', next_editorial_wake_reason: 'SCHEDULED', operator_trigger_pending: false, next_x_eligible_capture_utc: null, x_cadence_state: 'NORMAL' },
        last_completed_editorial: null,
        intake: { lane_state: 'RUNNING', last_ingest_utc: '2026-08-24T10:39:00Z', latest_capture_at_utc: '2026-08-24T10:39:00Z', latest_capture_result: 'CAPTURED', rows_last_iteration: 4, newest_source_event_at_utc: '2026-08-24T10:39:00Z', newest_source_event_age_seconds: 60, rolling_24h_unique_headlines: 121 },
        safety: { active_public_write: false, pending_reconciliation_count: 0, pending_readback_recovery_count: 0, unknown_write_count: 0, kill_switch_active: false, new_public_writes_blocked: true },
        browser: { state: 'IDLE', external_browser_activity_active: false, last_active_at_utc: null, last_reason: null, last_destination: null },
        recent_activity: [],
      },
    },
    today: { current_cycle: null, pending_lifecycle_recovery_count: 0, immediate_incident_count: 0, published_today_count: 0, published_corpus_count: 1, daily_target_band: [5, 8], newsroom_production_day_id: 'newsroom-production-day-2026-08-24-bangkok', build_qualified_floor: 4, final_published_target_min: 5, final_published_target_max: 8, qualified_articles_today: 1, published_articles_today: 0, remaining_build_deficit: 3, production_day_state: 'DEFICIT_RECOVERABLE', hard_external_block_reason: null, routine_opportunities_used: 0, routine_opportunities_remaining: 4 },
    queue: { items: [], upcoming_editorial_windows: [], material_event_wake_state: 'IDLE', active_or_held_work_count: 0, pending_readback_count: 0, due_performance_observation_count: 0 },
    published: { objects: [], real_publication_count: 0, controlled_no_public_write_count: 1, unknown_write_count: 0, pending_readback_count: 0, empty_reason: null },
    performance: { observations: [], real_observation_count: 0, empty_reason: null, empty_detail: null },
    learning: { active_policy: null, policy_history: [], empty_reason: null, configured_default: null },
    platforms: { destinations: [] },
    incidents: { items: [], active_count: 0, empty_reason: null },
    controls: { current_mode: 'SHADOW_ONLY', state_version: 30, allowed_modes: [], semantics: {}, write_endpoint: '', run_now_endpoint: '', background_log_streams: [] },
    audit: { work_item_count: 0, transition_event_count: 0, artifact_reference_count: 0, review_record_count: 0, recent_events: [] },
    authority: {},
  } as unknown as DailyAppSnapshot;
}

function respond(value: DailyAppSnapshot) {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => value }));
}

afterEach(() => vi.unstubAllGlobals());

describe('SimpleRunDashboard', () => {
  it('renders one nontechnical visual page with the zero-write safety state', async () => {
    respond(snapshot());
    render(<SimpleRunDashboard />);
    expect(await screen.findByText('Hệ thống đang chờ lịch')).toBeInTheDocument();
    expect(screen.getByText('Không đăng công khai')).toBeInTheDocument();
    expect(screen.getByText('Không chạy lặp')).toBeInTheDocument();
    expect(screen.getByText('Mọi trạng thái rõ ràng')).toBeInTheDocument();
    expect(screen.getByText('121')).toBeInTheDocument();
    for (const time of ['17:00', '21:00', '23:00', '01:00']) expect(screen.getAllByText(time).length).toBeGreaterThan(0);
  });

  it('turns the same page into a visual live-stage view while a run is active', async () => {
    respond(snapshot('RESEARCHING'));
    render(<SimpleRunDashboard />);
    expect(await screen.findByText('Hệ thống đang làm việc')).toBeInTheDocument();
    expect(screen.getByText('A governed market story')).toBeInTheDocument();
    expect(screen.getByText('Tiến độ hiện tại')).toBeInTheDocument();
    expect(screen.getByText('Kiểm chứng')).toBeInTheDocument();
    await waitFor(() => expect(fetch).toHaveBeenCalled());
  });

  it('does not misclassify resolved recovery history as an active warning', async () => {
    const data = snapshot();
    data.incidents = {
      active_count: 23,
      empty_reason: null,
      items: Array.from({ length: 23 }, (_, index) => ({
        incident_id: `history-${index}`,
        severity: 'RECOVERY_AUDIT',
        what_happened: 'Stale derivative expired with zero public write; prior readback history retained.',
        operator_action: 'Inspect the linked lifecycle and follow the exact recovery state.',
      })),
    };
    respond(data);
    render(<SimpleRunDashboard />);

    expect(await screen.findByText('Hệ thống đang chờ lịch')).toBeInTheDocument();
    expect(screen.queryByText('Có việc cần chú ý')).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /23 mục trong lịch sử/i }));
    expect(screen.getByRole('dialog', { name: 'Đã xử lý an toàn' })).toBeInTheDocument();
    expect(screen.getByText('Nội dung cũ đã được đóng an toàn')).toBeInTheDocument();
    expect(screen.getByText('× 23')).toBeInTheDocument();
    expect(screen.getByText('Không cần làm gì.')).toBeInTheDocument();
  });

  it('opens an actionable alert panel from the hero and closes it explicitly', async () => {
    const data = snapshot();
    data.incidents = {
      active_count: 1,
      empty_reason: null,
      items: [{
        incident_id: 'heartbeat-1', severity: 'HIGH',
        what_happened: 'No current supervisor heartbeat is available.',
        operator_action: 'Verify the Daily App supervisor process.',
      }],
    };
    respond(data);
    render(<SimpleRunDashboard />);

    const hero = await screen.findByRole('button', { name: /Có việc cần chú ý/i });
    fireEvent.click(hero);
    expect(screen.getByRole('dialog', { name: 'Cần chú ý' })).toBeInTheDocument();
    expect(screen.getByText('Hệ thống theo dõi chưa phản hồi')).toBeInTheDocument();
    expect(screen.getByText('Chờ một phút rồi bấm Làm mới.')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Đóng' }));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });
});
