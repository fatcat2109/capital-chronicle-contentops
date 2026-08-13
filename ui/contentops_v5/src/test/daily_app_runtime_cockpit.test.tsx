import { render, screen } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import type { DailyAppSnapshot, RuntimeCockpit, RuntimePrimaryState } from '../dailyAppTypes';
import { DailyAppConsole } from '../views/DailyAppConsole';

const stages = ['HEADLINE_INGESTION', 'CANDIDATE_SELECTION', 'CC_CONTEXT', 'GROUNDED_RESEARCH', 'ARTICLE_WRITING', 'MEDIA_BUILD', 'FACTUAL_CHECK', 'READER_VALUE_CHECK', 'PACKAGE_BUILD', 'PUBLICATION_JIT', 'CANONICAL_DISPATCH', 'CANONICAL_READBACK', 'DERIVATIVE_DISPATCH', 'RECONCILIATION'];

function cockpit(primary: RuntimePrimaryState): RuntimeCockpit {
  const researching = primary === 'RESEARCHING';
  return {
    schema_version: 'contentops.daily_app_runtime_cockpit.v1', primary_state: primary,
    supervisor_state: primary === 'STOPPED' ? 'STOPPED' : 'RUNNING', controller_health: primary === 'STOPPED' ? 'OFFLINE' : 'HEALTHY',
    publication_runtime_health: primary === 'STOPPED' ? 'STOPPED' : 'HEALTHY', operating_mode: primary === 'STOPPED' ? 'KILL_SWITCH' : 'AUTONOMOUS_DEFAULT',
    runtime_sha_short: 'c8f578c1a2c7', local_timezone: 'Asia/Ho_Chi_Minh', current_time_utc: '2026-08-14T04:00:00Z', heartbeat_age_seconds: primary === 'STOPPED' ? 430 : 3,
    current_activity: researching ? { work_item_id: 'cycle-1', cycle_started_at_utc: '2026-08-14T03:55:00Z', stage_started_at_utc: '2026-08-14T03:58:00Z', current_stage: 'GROUNDED_RESEARCH', story_label: 'Fed policy signals reshape the rate-cut path', candidate_rank: 1, candidate_count: 6, grounding: 'latest-web source-bound evidence', destination: null, trigger: 'SCHEDULED', instrumentation_state: 'EXPLICIT_STAGE_RECORDED' } : null,
    timeline: stages.map(stage => ({ stage, label: stage, state: stage === 'GROUNDED_RESEARCH' && researching ? 'current' : ['HEADLINE_INGESTION', 'CANDIDATE_SELECTION', 'CC_CONTEXT'].includes(stage) && researching ? 'completed' : 'pending' })),
    schedule: { idle_healthy: primary === 'RUNNING_IDLE', next_editorial_wake_utc: '2026-08-14T06:00:00Z', next_editorial_wake_reason: 'CORE_DAILY', operator_trigger_pending: false, next_x_eligible_capture_utc: '2026-08-14T04:30:00Z', x_cadence_state: 'NORMAL_30M' },
    last_completed_editorial: null,
    intake: { lane_state: primary === 'DEGRADED' ? 'DEGRADED' : 'RUNNING', last_ingest_utc: '2026-08-14T03:59:00Z', latest_capture_at_utc: '2026-08-14T03:59:00Z', latest_capture_result: primary === 'DEGRADED' ? 'CDP_UNAVAILABLE' : 'RUNNING', rows_last_iteration: 3, newest_source_event_at_utc: '2026-08-14T03:58:00Z', newest_source_event_age_seconds: 120, next_eligible_capture_utc: '2026-08-14T04:30:00Z', cadence_state: primary === 'DEGRADED' ? 'TRANSIENT_BACKOFF_30M_PLUS' : 'NORMAL_30M', rolling_24h_unique_headlines: 581 },
    safety: { active_public_write: false, pending_reconciliation_count: 0, pending_readback_recovery_count: 0, unknown_write_count: 0, kill_switch_active: primary === 'STOPPED', new_public_writes_blocked: primary === 'STOPPED' },
    browser: { state: 'IDLE', external_browser_activity_active: false, last_active_at_utc: '2026-08-14T03:45:00Z', last_reason: 'EXACT_DESTINATION_READBACK', last_destination: 'substack' }, recent_activity: [],
  };
}

function snapshot(primary: RuntimePrimaryState): DailyAppSnapshot {
  const cp = cockpit(primary);
  return {
    schema_version: 'contentops.daily_app_ui_snapshot.v1', generated_at_utc: '2026-08-14T04:00:00Z',
    freshness: { state: 'LIVE_CURRENT', source_last_updated_at_utc: '2026-08-14T04:00:00Z', source_age_seconds: 0, fresh_threshold_seconds: 300, provenance: 'store' },
    runtime: { app_identity: 'V1', operating_mode: cp.operating_mode, mode_state_version: 1, mode_updated_at_utc: '2026-08-14T04:00:00Z', mode_control_source: 'TEST', kill_switch_active: cp.safety.kill_switch_active, controller_health: cp.controller_health, latest_heartbeat_at_utc: '2026-08-14T04:00:00Z', production_epoch_start_utc: null, last_tick_state: 'IDLE', last_tick_at_utc: null, next_wake_utc: cp.schedule.next_editorial_wake_utc, next_editorial_window: null, operator_cycle_trigger: null, active_editorial_cycle_window_id: cp.current_activity?.work_item_id ?? null, headline_freshness: 'FRESH', headline_ingestion: { lane_state: cp.intake.lane_state, last_ingest_utc: cp.intake.last_ingest_utc, rows_last_iteration: cp.intake.rows_last_iteration }, browser_automation: { state: 'IDLE', last_active_browser_interaction_at_utc: cp.browser.last_active_at_utc, last_reason: cp.browser.last_reason }, rolling_24h_unique_headlines: 581, capital_chronicle_read_model: 'READY', provider_invocation_count: 0, prompt_tokens: 0, completion_tokens: 0, cost_metadata: 'UNAVAILABLE', operator_cockpit: cp },
    today: { current_cycle: null, pending_lifecycle_recovery_count: 0, immediate_incident_count: 0, published_today_count: 0, published_corpus_count: 10, daily_target_band: [5, 8] },
    queue: { items: [], upcoming_editorial_windows: [], material_event_wake_state: 'READY', active_or_held_work_count: 0, pending_readback_count: 0, due_performance_observation_count: 0 },
    published: { objects: [], real_publication_count: 0, controlled_no_public_write_count: 0, unknown_write_count: 0, pending_readback_count: 0, empty_reason: 'NONE' },
    performance: { observations: [], real_observation_count: 0, empty_reason: 'NONE', empty_detail: null }, learning: { active_policy: null, policy_history: [], empty_reason: 'NONE', configured_default: null }, platforms: { destinations: [] }, incidents: { items: [], active_count: 0, empty_reason: 'NONE' },
    controls: { current_mode: cp.operating_mode, state_version: 1, updated_at_utc: '2026-08-14T04:00:00Z', control_source: 'TEST', allowed_modes: ['AUTONOMOUS_DEFAULT', 'SUPERVISED_OPERATOR_GATE', 'SHADOW_ONLY', 'KILL_SWITCH'], write_endpoint: '/api/daily-app/control/mode', run_now_endpoint: '/api/daily-app/control/run-now', run_now_allowed: !cp.safety.kill_switch_active, run_now_mode_consequence: cp.safety.kill_switch_active ? 'Run now blocked by KILL_SWITCH.' : 'Governed request.', semantics: { AUTONOMOUS_DEFAULT: 'Routine', SUPERVISED_OPERATOR_GATE: 'Supervised', SHADOW_ONLY: 'No writes', KILL_SWITCH: 'Blocked' }, unsafe_controls_available: false }, authority: {}, audit: { work_item_count: 0, transition_event_count: 0, artifact_reference_count: 0, review_record_count: 0, recent_events: [], state_counts: {}, provenance: 'store' },
  };
}

function respond(primary: RuntimePrimaryState) {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => snapshot(primary) }));
}

function respondWith(data: DailyAppSnapshot) {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => data }));
}

afterEach(() => vi.unstubAllGlobals());

it('renders a healthy idle cockpit without presenting countdowns as active work', async () => {
  respond('RUNNING_IDLE'); render(<DailyAppConsole />);
  expect(await screen.findByRole('heading', { name: 'Running Idle' })).toBeInTheDocument();
  expect(screen.getByText('Waiting')).toBeInTheDocument();
  expect(screen.getByText(/no countdown is shown as active work/i)).toBeInTheDocument();
  expect(screen.getByText(/no active public write/i)).toBeInTheDocument();
});

it('renders explicit researching stage, story, candidate rank, grounding, and timeline', async () => {
  respond('RESEARCHING'); render(<DailyAppConsole />);
  expect(await screen.findByRole('heading', { name: 'Researching' })).toBeInTheDocument();
  expect(screen.getByText('Fed policy signals reshape the rate-cut path')).toBeInTheDocument();
  expect(screen.getByText('1 / 6')).toBeInTheDocument();
  expect(screen.getByText('latest-web source-bound evidence')).toBeInTheDocument();
  expect(document.querySelector('.daily-timeline-step.is-current')).toHaveTextContent('GROUNDED_RESEARCH');
});

it.each([
  ['WRITING', 'Writing'],
  ['PUBLISHING', 'Publishing'],
  ['RECONCILING', 'Reconciling'],
] as const)('renders the deterministic %s runtime state', async (primary, heading) => {
  respond(primary); render(<DailyAppConsole />);
  expect(await screen.findByRole('heading', { name: heading })).toBeInTheDocument();
});

it('keeps degraded intake distinct from a healthy publication runtime', async () => {
  respond('DEGRADED'); render(<DailyAppConsole />);
  expect(await screen.findByRole('heading', { name: 'Degraded' })).toBeInTheDocument();
  expect(screen.getAllByText('Degraded').length).toBeGreaterThan(1);
  expect(screen.getByText('Publication runtime').parentElement).toHaveTextContent('Healthy');
  expect(screen.getByText('Transient Backoff 30m Plus')).toBeInTheDocument();
});

it('renders stopped supervisor and kill-switch safety truth together', async () => {
  respond('STOPPED'); render(<DailyAppConsole />);
  expect(await screen.findByRole('heading', { name: 'Stopped' })).toBeInTheDocument();
  expect(screen.getByText('Supervisor Stopped')).toBeInTheDocument();
  expect(screen.getByText('Kill switch').parentElement).toHaveTextContent('ACTIVE');
  expect(screen.getByRole('button', { name: /run now unavailable/i })).toBeDisabled();
});

it('keeps recent published and no-publication cycles distinct with a safe canonical link', async () => {
  const data = snapshot('RUNNING_IDLE');
  const cp = data.runtime.operator_cockpit!;
  cp.recent_activity = [
    { activity_type: 'EDITORIAL_CYCLE', work_item_id: 'published', started_at_utc: '2026-08-14T03:00:00Z', completed_at_utc: '2026-08-14T03:02:41Z', duration_seconds: 161, story_label: 'A published evidence-bound story', candidate_rank: 1, candidate_count: 5, grounding: 'source-bound evidence', research_result: 'PASS', result: 'REAL_PUBLICATION_CONFIRMED', exact_reason: null, canonical_public_url: 'https://capitalchronicle.substack.com/p/safe-article' },
    { activity_type: 'EDITORIAL_CYCLE', work_item_id: 'no-publication', started_at_utc: '2026-08-14T02:00:00Z', completed_at_utc: '2026-08-14T02:00:39Z', duration_seconds: 39, story_label: 'A held candidate', candidate_rank: 2, candidate_count: 6, grounding: 'grounding unavailable', research_result: 'MINIMUM_EVIDENCE_NOT_MET', result: 'NO_PUBLICATION', exact_reason: 'MINIMUM_TRUSTWORTHY_EVIDENCE_NOT_MET', canonical_public_url: null },
  ];
  respondWith(data); render(<DailyAppConsole />);
  expect((await screen.findAllByText('Real Publication Confirmed')).length).toBeGreaterThan(0);
  expect(screen.getByText('No Publication')).toBeInTheDocument();
  const link = screen.getByRole('link', { name: /open canonical substack article/i });
  expect(link).toHaveAttribute('href', 'https://capitalchronicle.substack.com/p/safe-article');
  expect(screen.queryByText(/session=/i)).not.toBeInTheDocument();
});
