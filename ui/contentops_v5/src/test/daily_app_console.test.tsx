import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { DailyAppSnapshot } from '../dailyAppTypes';
import { DailyAppConsole, formatUtcDateTime } from '../views/DailyAppConsole';

function snapshot(overrides: Partial<DailyAppSnapshot> = {}): DailyAppSnapshot {
  const base: DailyAppSnapshot = {
    schema_version: 'contentops.daily_app_ui_snapshot.v1', generated_at_utc: '2026-08-10T12:00:00Z',
    freshness: { state: 'STALE', source_last_updated_at_utc: '2026-08-10T11:00:00Z', source_age_seconds: 3600, fresh_threshold_seconds: 300, provenance: 'canonical durable store timestamps' },
    runtime: { app_identity: 'Capital Chronicle ContentOps V1 — Daily App', operating_mode: 'AUTONOMOUS_DEFAULT', mode_state_version: 1, mode_updated_at_utc: '2026-08-10T12:00:00Z', mode_control_source: 'TEST', kill_switch_active: false, controller_health: 'HEALTHY', latest_heartbeat_at_utc: '2026-08-10T12:00:00Z', production_epoch_start_utc: null, last_tick_state: 'NO_TICK_RECORDED', last_tick_at_utc: null, next_wake_utc: null, next_editorial_window: null, operator_cycle_trigger: null, active_editorial_cycle_window_id: null, headline_freshness: 'HEADLINE_FRESHNESS_METADATA_UNAVAILABLE', headline_ingestion: { lane_state: 'RUNNING', last_ingest_utc: '2026-08-10T11:56:00Z', rows_last_iteration: 0 }, rolling_24h_unique_headlines: 581, capital_chronicle_read_model: 'READY', provider_invocation_count: 0, prompt_tokens: 0, completion_tokens: 0, cost_metadata: 'COST_METADATA_UNAVAILABLE' },
    today: { current_cycle: null, pending_lifecycle_recovery_count: 1, immediate_incident_count: 1, published_today_count: 0, published_corpus_count: 0, daily_target_band: [0, 4] },
    queue: { items: [], upcoming_editorial_windows: [], material_event_wake_state: 'MATERIAL_EVENT_METADATA_UNAVAILABLE', active_or_held_work_count: 0, pending_readback_count: 1, due_performance_observation_count: 0 },
    published: { objects: [
      { dispatch_id: 'd-real', platform: 'substack', lifecycle_classification: 'REAL_PUBLICATION_CONFIRMED', public_object_id: 'object-1' },
      { dispatch_id: 'd-controlled', platform: 'telegram', lifecycle_classification: 'CONTROLLED_NO_PUBLIC_WRITE', public_object_id: null },
      { dispatch_id: 'd-unknown', platform: 'x', lifecycle_classification: 'UNKNOWN_WRITE', public_object_id: null },
      { dispatch_id: 'd-pending', platform: 'linkedin', lifecycle_classification: 'CONFIRMED_DISPATCH_PENDING_READBACK', public_object_id: 'object-2' },
    ], real_publication_count: 1, controlled_no_public_write_count: 1, unknown_write_count: 1, pending_readback_count: 1, empty_reason: null },
    performance: { observations: [{ observation_id: 'obs-1', platform: 'substack', observation_window: 'EARLY', collection_status: 'SCHEDULED', metric_availability: { shares: 'UNAVAILABLE' }, native_metrics: {} }], real_observation_count: 1, empty_reason: null, empty_detail: null },
    learning: { active_policy: null, policy_history: [], empty_reason: 'NO_LEARNING_UPDATE_YET', configured_default: { policy_version: 'bootstrap', provenance: 'CONFIGURED_DEFAULT', sample_count: 0, confidence: 'BOOTSTRAP_NOT_LEARNED' } },
    platforms: { destinations: [{ platform_id: 'substack', display_name: 'Substack', binding_class: 'BROWSER_AUTHENTICATED', readiness: 'READINESS_UNAVAILABLE_NOT_PERSISTED', write_eligible: false, last_dispatch_state: 'REAL_PUBLICATION_CONFIRMED', metrics_capability: 'OBSERVATION_RECORDED', pending_incident: false }] },
    incidents: { items: [{ incident_id: 'incident-1', severity: 'CRITICAL', what_happened: 'UNKNOWN_WRITE', safe_now: 'Automatic retry is stopped.', automatic_action: 'Read back.', operator_action: 'Do not retry blindly.', work_item_id: 'w1' }], active_count: 1, empty_reason: null },
    controls: { current_mode: 'AUTONOMOUS_DEFAULT', state_version: 1, updated_at_utc: '2026-08-10T12:00:00Z', control_source: 'TEST', allowed_modes: ['AUTONOMOUS_DEFAULT', 'SUPERVISED_OPERATOR_GATE', 'SHADOW_ONLY', 'KILL_SWITCH'], write_endpoint: '/api/daily-app/control/mode', run_now_endpoint: '/api/daily-app/control/run-now', run_now_allowed: true, run_now_mode_consequence: 'Runs one governed editorial cycle now. A publishable package may be published automatically if every canonical gate passes.', semantics: { AUTONOMOUS_DEFAULT: 'Routine automation; gates remain.', SUPERVISED_OPERATOR_GATE: 'Pause before writes.', SHADOW_ONLY: 'Zero public writes.', KILL_SWITCH: 'Block new public writes.' }, unsafe_controls_available: false },
    authority: { fixture_fallback: false, snapshot_mutates_lifecycle: false },
    audit: { work_item_count: 0, transition_event_count: 0, artifact_reference_count: 0, review_record_count: 0, recent_events: [], state_counts: {}, provenance: 'canonical' },
  };
  return { ...base, ...overrides };
}

function respond(data: DailyAppSnapshot) {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => data }));
}

afterEach(() => { vi.unstubAllGlobals(); vi.unstubAllEnvs(); });

describe('Final Daily App production console', () => {
  it('renders final navigation and sparse real-state Today without a fake cycle', async () => {
    respond(snapshot()); render(<DailyAppConsole />);
    expect(await screen.findByText('No governed cycle recorded')).toBeInTheDocument();
    for (const label of ['Today', 'Observation / Learning', 'Queue', 'Published', 'Performance', 'Learning', 'Platforms', 'Incidents', 'Controls', 'Evidence / Audit']) {
      expect(screen.getByRole('button', { name: new RegExp(`^${label}`, 'i') })).toBeInTheDocument();
    }
    for (const label of ['Prior related article', 'Material delta', 'Decision reason', 'Stage stopped']) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
    expect(screen.queryByText(/fake current success/i)).not.toBeInTheDocument();
  });

  it('keeps real, controlled, unknown, and pending publication states distinct', async () => {
    respond(snapshot()); render(<DailyAppConsole />);
    await screen.findByText('No governed cycle recorded');
    fireEvent.click(screen.getByRole('button', { name: /^published$/i }));
    expect(screen.getAllByText('Real Publication Confirmed').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Controlled No Public Write').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Unknown Write').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Confirmed Dispatch Pending Readback').length).toBeGreaterThan(0);
  });

  it('renders unavailable native metrics and configured bootstrap as unavailable/not learned', async () => {
    respond(snapshot()); render(<DailyAppConsole />);
    await screen.findByText('No governed cycle recorded');
    fireEvent.click(screen.getByRole('button', { name: /^performance$/i }));
    expect(screen.getByText(/"shares":"UNAVAILABLE"/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /^learning$/i }));
    expect(screen.getByText('Configured default')).toBeInTheDocument();
    expect(screen.getByText('Bootstrap Not Learned')).toBeInTheDocument();
  });

  it('keeps an active bootstrap policy configured across Today, Queue, and Learning', async () => {
    const configured = {
      policy_version: 'policy.bootstrap.v1', parent_policy_version: null, status: 'ACTIVE',
      decision: 'BOOTSTRAP', provenance: 'CONFIGURED_DEFAULT', sample_count: 0, confidence: 0,
    };
    const data = snapshot({
      runtime: { ...snapshot().runtime, next_editorial_window: { provenance: 'CONFIGURED_DEFAULT' } },
      queue: { ...snapshot().queue, items: [{ queue_id: 'window-1', title: 'core_daily', state: 'CONFIGURED_DEFAULT' }] },
      learning: { active_policy: configured, policy_history: [configured], empty_reason: null, configured_default: null },
    });
    respond(data); render(<DailyAppConsole />);
    expect((await screen.findAllByText(/Configured Default/i)).length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole('button', { name: /^queue$/i }));
    expect(screen.getByText('Configured Default')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /^learning$/i }));
    expect(screen.getByRole('heading', { name: 'Configured default' })).toBeInTheDocument();
    expect(screen.queryByText('Active learned policy')).not.toBeInTheDocument();
  });

  it('renders every UTC-semantic queue timestamp explicitly in UTC', async () => {
    const canonicalTime = '2026-08-10T13:00:00Z';
    const data = snapshot({
      queue: { ...snapshot().queue, items: [{
        queue_id: 'window-utc', title: 'core_daily', state: 'CONFIGURED_DEFAULT',
        created_at_utc: canonicalTime, due_at_utc: canonicalTime,
        observation_for_utc: canonicalTime, missing_at_utc: null,
      }] },
    });
    respond(data); render(<DailyAppConsole />);
    await screen.findByText('No governed cycle recorded');
    fireEvent.click(screen.getByRole('button', { name: /^queue$/i }));
    expect(screen.getAllByText('Aug 10, 2026, 13:00 UTC')).toHaveLength(3);
    expect(screen.getByText('Missing At Utc').nextElementSibling).toHaveTextContent('Unavailable');
    expect(screen.getByText('Configured Default')).toBeInTheDocument();
  });

  it('keeps canonical UTC display invariant across materially different host timezones', () => {
    const canonicalTime = '2026-08-10T13:00:00Z';
    vi.stubEnv('TZ', 'America/New_York');
    const newYork = formatUtcDateTime(canonicalTime);
    vi.stubEnv('TZ', 'Asia/Bangkok');
    const Bangkok = formatUtcDateTime(canonicalTime);
    expect(newYork).toBe('Aug 10, 2026, 13:00 UTC');
    expect(Bangkok).toBe(newYork);
    expect(formatUtcDateTime(null)).toBe('Unavailable');
  });

  it('preserves exact safe destination identity while showing readiness evidence', async () => {
    const data = snapshot({
      platforms: { destinations: [{
        ...snapshot().platforms.destinations[0], safe_identity: '@CapitalChronicle',
        identity_match: true, transport_type: 'EDGE_CDP', probed_at_utc: '2026-08-10T12:00:00Z',
        last_successful_readback_at_utc: null, next_metric_availability: 'UNAVAILABLE',
      }] },
    });
    respond(data); render(<DailyAppConsole />);
    await screen.findByText('No governed cycle recorded');
    fireEvent.click(screen.getByRole('button', { name: /^platforms$/i }));
    expect(screen.getByText(/canonical readiness, verified safe identity/i)).toBeInTheDocument();
    expect(screen.queryByText(/readiness remains unavailable/i)).not.toBeInTheDocument();
    expect(screen.getByText('@CapitalChronicle')).toBeInTheDocument();
    expect(screen.getByText('Yes')).toBeInTheDocument();
    expect(screen.getByText('Edge Cdp')).toBeInTheDocument();
  });

  it('renders repeated durable audit event identifiers without duplicate React keys', async () => {
    const repeatedEvent = { event_id: 'contentops.policy.v1', event_kind: 'POLICY', to_state: 'ACTIVE' };
    const data = snapshot({
      audit: { ...snapshot().audit, recent_events: [repeatedEvent, { ...repeatedEvent, to_state: 'SUPERSEDED' }] },
    });
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => undefined);
    respond(data); render(<DailyAppConsole />);
    await screen.findByText('No governed cycle recorded');
    fireEvent.click(screen.getByRole('button', { name: /evidence \/ audit/i }));
    expect(errorSpy.mock.calls.flat().join(' ')).not.toContain('same key');
    errorSpy.mockRestore();
  });

  it('never falls back to fixtures when the API is offline', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('loopback offline')));
    render(<DailyAppConsole />);
    expect(await screen.findByText('Operating state unavailable')).toBeInTheDocument();
    expect(screen.getByText(/no fixture or fallback data is shown/i)).toBeInTheDocument();
    expect(screen.queryByText('No governed cycle recorded')).not.toBeInTheDocument();
  });

  it('shows kill switch prominently and posts an exact CAS-only control payload', async () => {
    const killed = snapshot({
      runtime: { ...snapshot().runtime, operating_mode: 'KILL_SWITCH', kill_switch_active: true },
      controls: { ...snapshot().controls, current_mode: 'KILL_SWITCH', state_version: 4, run_now_allowed: false, run_now_mode_consequence: 'New manual cycles are not accepted while the kill switch is active.' },
    });
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => killed })
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => ({ status: 'OPERATING_MODE_UPDATED' }) })
      .mockResolvedValue({ ok: true, status: 200, json: async () => ({ ...killed, runtime: { ...killed.runtime, operating_mode: 'SHADOW_ONLY', kill_switch_active: false }, controls: { ...killed.controls, current_mode: 'SHADOW_ONLY', state_version: 5 } }) });
    vi.stubGlobal('fetch', fetchMock); render(<DailyAppConsole />);
    await screen.findByText('No governed cycle recorded');
    fireEvent.click(screen.getByRole('button', { name: /^controls$/i }));
    await screen.findByText(/kill switch is active/i);
    fireEvent.click(screen.getByRole('button', { name: /shadow only/i }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
    const [, init] = fetchMock.mock.calls[1];
    expect(JSON.parse(String(init.body))).toEqual({ operating_mode: 'SHADOW_ONLY', expected_state_version: 4 });
    expect(String(fetchMock.mock.calls[1][0])).toContain('/api/daily-app/control/mode');
  });

  it('posts the exact bounded run-now payload and shows governed acceptance without claiming publication', async () => {
    const accepted = snapshot({
      runtime: { ...snapshot().runtime, operator_cycle_trigger: { trigger_id: 'operator-trigger-abc123', trigger_kind: 'OPERATOR_REQUESTED', state: 'PENDING', requested_mode: 'AUTONOMOUS_DEFAULT' } },
    });
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => snapshot() })
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => ({ status: 'OPERATOR_TRIGGER_ACCEPTED', publication_claimed: false }) })
      .mockResolvedValue({ ok: true, status: 200, json: async () => accepted });
    vi.stubGlobal('fetch', fetchMock); render(<DailyAppConsole />);
    const button = await screen.findByRole('button', { name: /run editorial cycle now/i });
    fireEvent.click(button);
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
    const [, init] = fetchMock.mock.calls[1];
    expect(JSON.parse(String(init.body))).toEqual({ trigger: 'OPERATOR_REQUESTED', expected_state_version: 1 });
    expect(String(fetchMock.mock.calls[1][0])).toContain('/api/daily-app/control/run-now');
    await screen.findByText(/operator trigger accepted/i);
    await screen.findByText(/publication is never guaranteed/i);
    await waitFor(() => expect(screen.getByRole('button', { name: /operator trigger pending/i })).toBeDisabled());
  });

  it('keeps the run-now button disabled under KILL_SWITCH with truthful consequence text', async () => {
    const killed = snapshot({
      runtime: { ...snapshot().runtime, operating_mode: 'KILL_SWITCH', kill_switch_active: true },
      controls: { ...snapshot().controls, current_mode: 'KILL_SWITCH', run_now_allowed: false, run_now_mode_consequence: 'New manual cycles are not accepted while the kill switch is active.' },
    });
    respond(killed); render(<DailyAppConsole />);
    await screen.findByText(/new manual cycles are not accepted/i);
    expect(screen.getByRole('button', { name: /run now unavailable/i })).toBeDisabled();
  });

  it('disables duplicate run-now requests while a durable operator trigger is pending or a cycle is active', async () => {
    const pending = snapshot({
      runtime: { ...snapshot().runtime, operator_cycle_trigger: { trigger_id: 'operator-trigger-pending1', state: 'PENDING' } },
    });
    respond(pending); render(<DailyAppConsole />);
    await waitFor(() => expect(screen.getByRole('button', { name: /operator trigger pending/i })).toBeDisabled());
    expect(screen.getByText(/operator-trigger-pending1/i)).toBeInTheDocument();
    const active = snapshot({ runtime: { ...snapshot().runtime, active_editorial_cycle_window_id: 'editorial-window-running' } });
    respond(active); render(<DailyAppConsole />);
    await waitFor(() => expect(screen.getByRole('button', { name: /cycle already active/i })).toBeDisabled());
  });
});
