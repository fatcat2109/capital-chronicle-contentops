import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import type { DailyAppSnapshot } from '../dailyAppTypes';
import { DailyAppConsole } from '../views/DailyAppConsole';

function snapshot(): DailyAppSnapshot {
  return {
    schema_version: 'contentops.daily_app_ui_snapshot.v1', generated_at_utc: '2026-08-13T10:00:00Z',
    freshness: { state: 'FRESH', source_last_updated_at_utc: '2026-08-13T10:00:00Z', source_age_seconds: 0, fresh_threshold_seconds: 300, provenance: 'store' },
    runtime: { app_identity: 'V1', operating_mode: 'KILL_SWITCH', mode_state_version: 4, mode_updated_at_utc: '2026-08-13T10:00:00Z', mode_control_source: 'TEST', kill_switch_active: true, controller_health: 'HEALTHY', latest_heartbeat_at_utc: '2026-08-13T10:00:00Z', production_epoch_start_utc: null, last_tick_state: 'IDLE', last_tick_at_utc: null, next_wake_utc: null, next_editorial_window: null, operator_cycle_trigger: null, active_editorial_cycle_window_id: null, headline_freshness: 'FRESH', headline_ingestion: { lane_state: 'RUNNING', last_ingest_utc: '2026-08-13T09:59:00Z', rows_last_iteration: 2 }, rolling_24h_unique_headlines: 700, capital_chronicle_read_model: 'READY', provider_invocation_count: 0, prompt_tokens: 0, completion_tokens: 0, cost_metadata: 'UNAVAILABLE' },
    today: { current_cycle: null, pending_lifecycle_recovery_count: 0, immediate_incident_count: 0, published_today_count: 0, published_corpus_count: 10, daily_target_band: [5, 8] },
    queue: { items: [], upcoming_editorial_windows: [], material_event_wake_state: 'READY', active_or_held_work_count: 0, pending_readback_count: 0, due_performance_observation_count: 0 },
    published: { objects: [], real_publication_count: 0, controlled_no_public_write_count: 0, unknown_write_count: 0, pending_readback_count: 0, empty_reason: 'NONE' },
    performance: { observations: [], real_observation_count: 0, empty_reason: 'NONE', empty_detail: null },
    learning: { active_policy: null, policy_history: [], empty_reason: 'NONE', configured_default: null },
    platforms: { destinations: [] }, incidents: { items: [], active_count: 0, empty_reason: 'NONE' },
    hourly_audit: { schema_version: 'contentops.hourly_runtime_audit.v1', generated_at_utc: '2026-08-13T09:55:00Z', classification: 'PASS', classification_reasons: ['ALL_REQUIRED_READ_ONLY_CHECKS_PASS'] },
    controls: { current_mode: 'KILL_SWITCH', state_version: 4, updated_at_utc: '2026-08-13T10:00:00Z', control_source: 'TEST', allowed_modes: ['AUTONOMOUS_DEFAULT', 'SUPERVISED_OPERATOR_GATE', 'SHADOW_ONLY', 'KILL_SWITCH'], write_endpoint: '/api/daily-app/control/mode', run_now_endpoint: '/api/daily-app/control/run-now', run_now_allowed: false, run_now_mode_consequence: 'Run now blocked by KILL_SWITCH.', shutdown_endpoint: '/api/daily-app/control/shutdown-all-background', shutdown_allowed: true, shutdown_blockers: [], background_logs_endpoint: '/api/daily-app/background-logs', background_log_streams: [{ stream: 'supervisor_stderr', label: 'Supervisor stderr' }], hourly_audit_endpoint: '/api/daily-app/hourly-audit/latest', semantics: { AUTONOMOUS_DEFAULT: 'Routine', SUPERVISED_OPERATOR_GATE: 'Supervised', SHADOW_ONLY: 'No writes', KILL_SWITCH: 'Blocked' }, unsafe_controls_available: false },
    authority: {}, audit: { work_item_count: 0, transition_event_count: 0, artifact_reference_count: 0, review_record_count: 0, recent_events: [], state_counts: {}, provenance: 'store' },
  };
}

afterEach(() => { vi.unstubAllGlobals(); });

it('shows latest hourly audit and sends the exact confirmed safe-shutdown payload', async () => {
  const fetchMock = vi.fn()
    .mockResolvedValueOnce({ ok: true, status: 200, json: async () => snapshot() })
    .mockResolvedValueOnce({ ok: true, status: 202, json: async () => ({ status: 'SAFE_SHUTDOWN_STARTED' }) });
  vi.stubGlobal('fetch', fetchMock); vi.stubGlobal('confirm', vi.fn(() => true));
  render(<DailyAppConsole />);
  expect((await screen.findAllByText('Pass')).length).toBeGreaterThan(0);
  fireEvent.click(screen.getByRole('button', { name: /^controls$/i }));
  fireEvent.click(screen.getByRole('button', { name: /^shutdown all background$/i }));
  await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
  const [, init] = fetchMock.mock.calls[1];
  expect(JSON.parse(String(init.body))).toEqual({ action: 'SHUTDOWN_ALL_BACKGROUND', expected_state_version: 4 });
  expect(String(fetchMock.mock.calls[1][0])).toContain('/api/daily-app/control/shutdown-all-background');
  expect(await screen.findByText(/safe shutdown started/i)).toBeInTheDocument();
});

it('requests only an allowlisted bounded log stream and renders its sanitized tail', async () => {
  const fetchMock = vi.fn()
    .mockResolvedValueOnce({ ok: true, status: 200, json: async () => snapshot() })
    .mockResolvedValue({ ok: true, status: 200, json: async () => ({ schema_version: 'contentops.background_log_tail.v1', stream: 'supervisor_stderr', label: 'Supervisor stderr', status: 'AVAILABLE', line_count: 1, truncated: false, latest_timestamp_utc: '2026-08-13T10:00:00Z', content: 'controller healthy [REDACTED]' }) });
  vi.stubGlobal('fetch', fetchMock); render(<DailyAppConsole />);
  await screen.findByText('No governed cycle recorded');
  fireEvent.click(screen.getByRole('button', { name: /^background logs$/i }));
  expect(await screen.findByText(/controller healthy \[REDACTED\]/i)).toBeInTheDocument();
  expect(String(fetchMock.mock.calls[1][0])).toContain('stream=supervisor_stderr&lines=200');
  expect(String(fetchMock.mock.calls[1][0])).not.toContain('path=');
});
