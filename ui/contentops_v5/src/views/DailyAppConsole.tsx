import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Activity, AlertTriangle, Archive, BarChart3, BookOpenCheck, CalendarClock,
  ChevronRight, CircleOff, Database, Gauge, Menu, PanelLeftClose, RefreshCw,
  ScrollText, Shield, ShieldAlert, SlidersHorizontal, Sparkles, ExternalLink,
} from 'lucide-react';
import type { BackgroundLogTail, DailyAppSnapshot, DailyView, HourlyAudit, LoadState, OperatingMode, RuntimeCockpit, RuntimePrimaryState } from '../dailyAppTypes';

const API_ROOT = 'http://127.0.0.1:5174';
const POLL_MS = 3_000;

const NAV: Array<{ group: string; items: Array<{ id: DailyView; label: string; icon: typeof Activity }> }> = [
  { group: 'Daily app', items: [
    { id: 'today', label: 'Today', icon: Activity },
    { id: 'queue', label: 'Queue', icon: CalendarClock },
    { id: 'published', label: 'Published', icon: Archive },
    { id: 'performance', label: 'Performance', icon: BarChart3 },
    { id: 'learning', label: 'Learning', icon: Sparkles },
  ] },
  { group: 'Operations', items: [
    { id: 'platforms', label: 'Platforms', icon: Database },
    { id: 'incidents', label: 'Incidents', icon: ShieldAlert },
    { id: 'controls', label: 'Controls', icon: SlidersHorizontal },
    { id: 'background_logs', label: 'Background logs', icon: ScrollText },
  ] },
  { group: 'Reference', items: [{ id: 'audit', label: 'Evidence / Audit', icon: BookOpenCheck }] },
];

function useDailyAppSnapshot(): [LoadState, () => Promise<void>] {
  const [state, setState] = useState<LoadState>({ kind: 'loading', snapshot: null, error: null });
  const refresh = useCallback(async () => {
    try {
      const response = await fetch(`${API_ROOT}/api/daily-app/snapshot`, {
        headers: { Accept: 'application/json' }, cache: 'no-store',
      });
      if (!response.ok) throw new Error(`Snapshot unavailable (${response.status})`);
      const snapshot = applyRuntimeQaFixture(await response.json() as DailyAppSnapshot);
      if (snapshot.schema_version !== 'contentops.daily_app_ui_snapshot.v1') {
        throw new Error('Snapshot schema is not supported');
      }
      setState({ kind: 'online', snapshot, error: null });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Snapshot unavailable';
      setState(previous => ({ kind: 'offline', snapshot: previous.snapshot, error: message }));
    }
  }, []);

  useEffect(() => {
    void refresh();
    const timer = window.setInterval(() => {
      if (document.visibilityState === 'visible') void refresh();
    }, POLL_MS);
    return () => window.clearInterval(timer);
  }, [refresh]);
  return [state, refresh];
}

function runtimeQaFixtureName(): string | null {
  const env = (import.meta as unknown as { env: Record<string, string | undefined> }).env;
  if (env.VITE_ENABLE_RUNTIME_QA_FIXTURES !== '1') return null;
  const fixture = new URLSearchParams(window.location.search).get('runtime_fixture');
  return fixture && ['idle', 'researching', 'degraded', 'stopped'].includes(fixture) ? fixture : null;
}

function applyRuntimeQaFixture(snapshot: DailyAppSnapshot): DailyAppSnapshot {
  const fixture = runtimeQaFixtureName();
  const source = snapshot.runtime.operator_cockpit ?? legacyCockpit(snapshot);
  if (!fixture) return snapshot;
  const cockpit: RuntimeCockpit = structuredClone(source);
  const fixtureTimeline = cockpit.timeline.length ? cockpit.timeline : [
    { stage: 'HEADLINE_INGESTION', label: 'Intake', state: 'pending' as const },
    { stage: 'CANDIDATE_SELECTION', label: 'Selection', state: 'pending' as const },
    { stage: 'CC_CONTEXT', label: 'Context', state: 'pending' as const },
    { stage: 'GROUNDED_RESEARCH', label: 'Research', state: 'pending' as const },
    { stage: 'ARTICLE_WRITING', label: 'Write', state: 'pending' as const },
    { stage: 'MEDIA_BUILD', label: 'Media', state: 'pending' as const },
    { stage: 'PACKAGE_BUILD', label: 'Package', state: 'pending' as const },
    { stage: 'CANONICAL_DISPATCH', label: 'Publish', state: 'pending' as const },
    { stage: 'CANONICAL_READBACK', label: 'Readback', state: 'pending' as const },
  ];
  cockpit.runtime_sha_short = 'QA-FIXTURE';
  cockpit.operating_mode = 'AUTONOMOUS_DEFAULT';
  cockpit.publication_runtime_health = 'HEALTHY';
  cockpit.heartbeat_age_seconds = 3;
  cockpit.schedule.operator_trigger_pending = false;
  cockpit.intake.lane_state = 'RUNNING';
  cockpit.intake.latest_capture_result = 'CAPTURED_NEW';
  cockpit.safety = { active_public_write: false, pending_reconciliation_count: 0,
    pending_readback_recovery_count: 0, unknown_write_count: 0,
    kill_switch_active: false, new_public_writes_blocked: false };
  cockpit.browser = { state: 'IDLE', external_browser_activity_active: false,
    last_active_at_utc: null, last_reason: null, last_destination: null };
  cockpit.schedule.next_editorial_wake_utc = new Date(Date.now() + 38 * 60_000).toISOString();
  cockpit.schedule.next_editorial_wake_reason = 'CORE_DAILY';
  cockpit.schedule.next_x_eligible_capture_utc = new Date(Date.now() + 12 * 60_000).toISOString();
  cockpit.schedule.x_cadence_state = 'NORMAL_30M';
  cockpit.intake.next_eligible_capture_utc = cockpit.schedule.next_x_eligible_capture_utc;
  cockpit.intake.cadence_state = cockpit.schedule.x_cadence_state;
  cockpit.intake.newest_source_event_age_seconds = 94;
  if (fixture === 'idle') {
    cockpit.primary_state = 'RUNNING_IDLE'; cockpit.supervisor_state = 'RUNNING';
    cockpit.controller_health = 'HEALTHY'; cockpit.schedule.idle_healthy = true;
    cockpit.current_activity = null; cockpit.timeline = [];
  } else if (fixture === 'researching') {
    cockpit.primary_state = 'RESEARCHING'; cockpit.supervisor_state = 'RUNNING';
    cockpit.controller_health = 'HEALTHY'; cockpit.schedule.idle_healthy = false;
    cockpit.current_activity = {
      work_item_id: 'qa-fixture-researching', cycle_started_at_utc: new Date(Date.now() - 247_000).toISOString(),
      stage_started_at_utc: new Date(Date.now() - 81_000).toISOString(), current_stage: 'GROUNDED_RESEARCH',
      story_label: 'Fed policy signals reshape the rate-cut path', candidate_rank: 1, candidate_count: 6,
      grounding: 'latest-web source-bound evidence', destination: null, trigger: 'SCHEDULED',
      instrumentation_state: 'DETERMINISTIC_LOCAL_QA_FIXTURE',
    };
    const order = ['HEADLINE_INGESTION', 'CANDIDATE_SELECTION', 'CC_CONTEXT'];
    cockpit.timeline = fixtureTimeline.map(step => ({ ...step, state: step.stage === 'GROUNDED_RESEARCH' ? 'current' : order.includes(step.stage) ? 'completed' : 'pending' }));
  } else if (fixture === 'degraded') {
    cockpit.primary_state = 'DEGRADED'; cockpit.supervisor_state = 'RUNNING';
    cockpit.controller_health = 'HEALTHY'; cockpit.publication_runtime_health = 'HEALTHY';
    cockpit.intake.lane_state = 'DEGRADED'; cockpit.intake.latest_capture_result = 'CDP_UNAVAILABLE';
    cockpit.intake.cadence_state = 'TRANSIENT_BACKOFF_30M_PLUS'; cockpit.schedule.x_cadence_state = 'TRANSIENT_BACKOFF_30M_PLUS';
    cockpit.current_activity = null; cockpit.timeline = [];
  } else {
    cockpit.primary_state = 'STOPPED'; cockpit.supervisor_state = 'STOPPED';
    cockpit.controller_health = 'OFFLINE'; cockpit.operating_mode = 'KILL_SWITCH';
    cockpit.safety.kill_switch_active = true; cockpit.safety.new_public_writes_blocked = true;
    cockpit.current_activity = null; cockpit.timeline = []; cockpit.heartbeat_age_seconds = 437;
  }
  return { ...snapshot, freshness: { ...snapshot.freshness, state: 'LIVE_CURRENT', source_age_seconds: 0 },
    runtime: { ...snapshot.runtime, operator_cockpit: cockpit } };
}

function words(value: unknown): string {
  if (value === null || value === undefined || value === '') return 'Unavailable';
  return String(value).replace(/_/g, ' ').toLowerCase().replace(/(^|\s)\S/g, (c: string) => c.toUpperCase());
}

const UTC_MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

export function formatUtcDateTime(value: unknown): string {
  if (!value) return 'Unavailable';
  const date = new Date(String(value));
  if (Number.isNaN(date.valueOf())) return 'Invalid timestamp';
  const hour = String(date.getUTCHours()).padStart(2, '0');
  const minute = String(date.getUTCMinutes()).padStart(2, '0');
  return `${UTC_MONTHS[date.getUTCMonth()]} ${date.getUTCDate()}, ${date.getUTCFullYear()}, ${hour}:${minute} UTC`;
}

function statusTone(value: unknown): 'good' | 'warn' | 'bad' | 'neutral' {
  const status = String(value ?? '').toUpperCase();
  if (/UNKNOWN|KILL|CRITICAL|FAILED|BLOCKED|OFFLINE|STOPPED|ACTION_REQUIRED/.test(status)) return 'bad';
  if (/PENDING|STALE|DUE|REVIEW|UNAVAILABLE|HELD|SUPERVISED|DEGRADED/.test(status)) return 'warn';
  if (/HEALTHY|READY|CONFIRMED|PUBLISHED|CURRENT|ACTIVE|RECONCILED|AVAILABLE|RUNNING|INGESTING|PREPARING|RESEARCHING|WRITING|MEDIA_BUILDING|PACKAGING|PUBLISHING|READING_BACK|RECONCILING/.test(status)) return 'good';
  return 'neutral';
}

function Status({ value, label }: { value: unknown; label?: string }) {
  const tone = statusTone(value);
  return <span className={`daily-status daily-status--${tone}`} data-status={String(value)}><i />{label ?? words(value)}</span>;
}

function Empty({ title, detail }: { title: string; detail: string }) {
  return <div className="daily-empty"><CircleOff aria-hidden="true" /><strong>{title}</strong><p>{detail}</p></div>;
}

function Panel({ title, eyebrow, children, className = '' }: { title: string; eyebrow?: string; children: React.ReactNode; className?: string }) {
  return <section className={`daily-panel ${className}`}>{eyebrow && <div className="daily-eyebrow">{eyebrow}</div>}<h2>{title}</h2>{children}</section>;
}

function Metric({ label, value, status }: { label: string; value: unknown; status?: unknown }) {
  return <div className="daily-metric"><span>{label}</span><strong>{value === null || value === undefined ? 'Unavailable' : String(value)}</strong>{status !== null && status !== undefined && <Status value={status} />}</div>;
}

function displayValue(key: string, value: unknown): string {
  if (value === null || value === undefined || value === '') return 'Unavailable';
  if (typeof value === 'object') return JSON.stringify(value);
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  if (/_utc$/.test(key)) return formatUtcDateTime(value);
  const text = String(value);
  return /^[A-Z][A-Z0-9_]*$/.test(text) ? words(text) : text;
}

function DefinitionRows({ object }: { object: Record<string, unknown> }) {
  return <dl className="daily-definitions">{Object.entries(object).map(([key, value]) => <div key={key}><dt>{words(key)}</dt><dd>{displayValue(key, value)}</dd></div>)}</dl>;
}

function RunEditorialNow({ data, refresh }: { data: DailyAppSnapshot; refresh: () => Promise<void> }) {
  const [phase, setPhase] = useState<'idle' | 'submitting'>('idle');
  const [message, setMessage] = useState<string | null>(null);
  const trigger = data.runtime.operator_cycle_trigger;
  const pending = Boolean(trigger && trigger.state === 'PENDING');
  const activeCycle = Boolean(data.runtime.active_editorial_cycle_window_id);
  const allowed = Boolean(data.controls.run_now_allowed);
  const disabled = phase === 'submitting' || pending || activeCycle || !allowed;
  const label = phase === 'submitting'
    ? 'Requesting…'
    : activeCycle ? 'Cycle already active'
    : pending ? 'Operator trigger pending'
    : allowed ? 'Run editorial cycle now'
    : 'Run now unavailable';
  const request = async () => {
    if (disabled) return;
    setPhase('submitting');
    setMessage(null);
    try {
      const response = await fetch(`${API_ROOT}${data.controls.run_now_endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ trigger: 'OPERATOR_REQUESTED', expected_state_version: data.controls.state_version }),
      });
      const result = await response.json() as { status?: string; error?: string };
      if (result.status === 'OPERATOR_TRIGGER_ACCEPTED') {
        setMessage('Operator trigger accepted. One governed cycle is queued; every gate remains unchanged and no publication is claimed.');
        await refresh();
        return;
      }
      setMessage(words(result.status ?? result.error ?? 'RUN_NOW_REQUEST_NOT_ACCEPTED'));
      await refresh();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Run now request failed');
    } finally {
      setPhase('idle');
    }
  };
  return <Panel title="Run editorial cycle now" eyebrow="Operator trigger">
    <p className="daily-callout">{data.controls.run_now_mode_consequence ?? 'Mode consequence unavailable'}</p>
    <button type="button" className="daily-run-now-button" disabled={disabled} onClick={() => void request()}>{label}</button>
    {message && <p role="status" className="daily-control-message">{message}</p>}
    {pending && trigger && <p>Durable operator trigger {String(trigger.trigger_id)} is pending supervisor consumption.</p>}
    <p>Governed request only: it bypasses the wait for the scheduled window and nothing else. Evidence, review, freshness, permission, readiness, and publication gates stay unchanged, and publication is never guaranteed.</p>
  </Panel>;
}

const PRIMARY_STATE_COPY: Record<RuntimePrimaryState, string> = {
  STOPPED: 'The persistent supervisor is not reporting a current heartbeat.',
  STARTING: 'The supervisor is starting and has not yet reached its steady loop.',
  RUNNING_IDLE: 'Idle is healthy. V1 is waiting for the next governed opportunity.',
  INGESTING: 'Refreshing the durable rolling X headline universe.',
  PREPARING: 'Selecting and binding the next governed story candidate.',
  RESEARCHING: 'Obtaining minimum trustworthy, source-bound evidence.',
  WRITING: 'Writing and checking the selected evidence-bound article.',
  MEDIA_BUILDING: 'Preparing rights-safe, source-backed article media.',
  PACKAGING: 'Building the locked canonical and derivative packages.',
  PUBLISHING: 'A governed destination dispatch is active.',
  READING_BACK: 'Reading back the exact canonical public object identity.',
  RECONCILING: 'Reconciling durable lifecycle truth before any retry.',
  DEGRADED: 'A durable runtime input is degraded; publication safety remains intact.',
  ACTION_REQUIRED: 'A durable safety or operator condition requires attention.',
};

function legacyCockpit(data: DailyAppSnapshot): RuntimeCockpit {
  const primary: RuntimePrimaryState = data.runtime.controller_health === 'OFFLINE'
    ? 'STOPPED' : data.runtime.kill_switch_active || data.incidents.active_count > 0
      ? 'ACTION_REQUIRED' : data.runtime.headline_ingestion.lane_state === 'RUNNING'
        ? 'RUNNING_IDLE' : 'DEGRADED';
  return {
    schema_version: 'contentops.daily_app_runtime_cockpit.v1', primary_state: primary,
    supervisor_state: primary === 'STOPPED' ? 'STOPPED' : 'RUNNING', controller_health: data.runtime.controller_health,
    publication_runtime_health: primary === 'STOPPED' ? 'STOPPED' : 'HEALTHY', operating_mode: data.runtime.operating_mode,
    runtime_sha_short: 'UNAVAILABLE', local_timezone: 'Asia/Ho_Chi_Minh', current_time_utc: data.generated_at_utc,
    heartbeat_age_seconds: null, current_activity: null, timeline: [],
    schedule: { idle_healthy: primary === 'RUNNING_IDLE', next_editorial_wake_utc: data.runtime.next_wake_utc,
      next_editorial_wake_reason: 'SCHEDULED_EDITORIAL_WINDOW', operator_trigger_pending: Boolean(data.runtime.operator_cycle_trigger),
      next_x_eligible_capture_utc: data.runtime.headline_ingestion.next_eligible_capture_utc ?? null,
      x_cadence_state: data.runtime.headline_ingestion.cadence_state ?? 'UNAVAILABLE' },
    last_completed_editorial: null,
    intake: { lane_state: data.runtime.headline_ingestion.lane_state, last_ingest_utc: data.runtime.headline_ingestion.last_ingest_utc,
      latest_capture_at_utc: data.runtime.headline_ingestion.last_ingest_utc, latest_capture_result: data.runtime.headline_ingestion.lane_state,
      rows_last_iteration: data.runtime.headline_ingestion.rows_last_iteration, newest_source_event_at_utc: null,
      newest_source_event_age_seconds: null, next_eligible_capture_utc: data.runtime.headline_ingestion.next_eligible_capture_utc,
      cadence_state: data.runtime.headline_ingestion.cadence_state, rolling_24h_unique_headlines: data.runtime.rolling_24h_unique_headlines },
    safety: { active_public_write: false, pending_reconciliation_count: data.today.pending_lifecycle_recovery_count,
      pending_readback_recovery_count: data.today.pending_lifecycle_recovery_count,
      unknown_write_count: data.published.unknown_write_count, kill_switch_active: data.runtime.kill_switch_active,
      new_public_writes_blocked: data.runtime.operating_mode !== 'AUTONOMOUS_DEFAULT' },
    browser: { state: data.runtime.browser_automation?.state ?? 'IDLE', external_browser_activity_active: false,
      last_active_at_utc: data.runtime.browser_automation?.last_active_browser_interaction_at_utc ?? null,
      last_reason: data.runtime.browser_automation?.last_reason ?? null,
      last_destination: data.runtime.browser_automation?.last_destination ?? null }, recent_activity: [],
  };
}

function formatLocalClock(value: string, timezone: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.valueOf())) return 'Unavailable';
  return new Intl.DateTimeFormat('en-GB', { timeZone: timezone, hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }).format(date);
}

function formatLocalDateTime(value: string | null, timezone: string): string {
  if (!value) return 'Unavailable';
  const date = new Date(value);
  if (Number.isNaN(date.valueOf())) return 'Unavailable';
  return new Intl.DateTimeFormat('en-GB', {
    timeZone: timezone, day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false,
  }).format(date);
}

function formatCountdown(target: string | null, nowMs: number): string {
  if (!target) return 'Not scheduled';
  const remaining = new Date(target).valueOf() - nowMs;
  if (Number.isNaN(remaining)) return 'Unavailable';
  if (remaining <= 0) return 'Due now';
  const total = Math.ceil(remaining / 1000); const hours = Math.floor(total / 3600); const minutes = Math.floor((total % 3600) / 60); const seconds = total % 60;
  return `${hours ? `${hours}h ` : ''}${String(minutes).padStart(2, '0')}m ${String(seconds).padStart(2, '0')}s`;
}

function formatDuration(seconds: number | null): string {
  if (seconds === null) return 'Unavailable';
  const minutes = Math.floor(seconds / 60); const rest = seconds % 60;
  return minutes ? `${minutes}m ${rest}s` : `${rest}s`;
}

function elapsedSince(value: string | null, nowMs: number): string {
  if (!value) return 'Unavailable';
  const seconds = Math.max(0, Math.floor((nowMs - new Date(value).valueOf()) / 1000));
  return Number.isFinite(seconds) ? formatDuration(seconds) : 'Unavailable';
}

function ActivitySummary({ cockpit, nowMs }: { cockpit: RuntimeCockpit; nowMs: number }) {
  const active = cockpit.current_activity;
  const last = cockpit.last_completed_editorial;
  if (active) return <>
    <div className="daily-activity-heading"><div><span>Current activity</span><strong>{words(active.current_stage)}</strong></div><Status value="ACTIVE" /></div>
    <h3>{active.story_label ?? 'Story label not yet selected'}</h3>
    <div className="daily-activity-facts"><span>Elapsed <b>{elapsedSince(active.cycle_started_at_utc, nowMs)}</b></span><span>Candidate <b>{active.candidate_rank ?? '—'} / {active.candidate_count ?? '—'}</b></span><span>Grounding <b>{active.grounding ?? 'Unavailable'}</b></span><span>Cycle start <b>{formatLocalDateTime(active.cycle_started_at_utc, cockpit.local_timezone)}</b></span><span>Stage start <b>{formatLocalDateTime(active.stage_started_at_utc, cockpit.local_timezone)}</b></span><span>Cycle ID <b>{active.work_item_id.slice(0, 24)}</b></span></div>
  </>;
  if (last) return <>
    <div className="daily-activity-heading"><div><span>Last completed cycle</span><strong>{words(last.result)}</strong></div><Status value={last.result} /></div>
    <h3>{last.story_label ?? 'No selected story label recorded'}</h3>
    <div className="daily-activity-facts"><span>Duration <b>{formatDuration(last.duration_seconds)}</b></span><span>Research <b>{words(last.research_result)}</b></span><span>Result <b>{words(last.exact_reason ?? last.result)}</b></span></div>
    {last.canonical_public_url && <a className="daily-public-link" href={last.canonical_public_url} target="_blank" rel="noreferrer">Open canonical Substack article <ExternalLink /></a>}
  </>;
  return <div className="daily-waiting"><span>Current activity</span><strong>{cockpit.primary_state === 'STOPPED' ? 'Supervisor stopped' : 'Waiting'}</strong><p>{PRIMARY_STATE_COPY[cockpit.primary_state]}</p></div>;
}

function RuntimeCockpitView({ data }: { data: DailyAppSnapshot }) {
  const cockpit = data.runtime.operator_cockpit ?? legacyCockpit(data);
  const [nowMs, setNowMs] = useState(Date.now());
  useEffect(() => { const timer = window.setInterval(() => setNowMs(Date.now()), 1_000); return () => window.clearInterval(timer); }, []);
  const safetyClear = !cockpit.safety.active_public_write
    && cockpit.safety.pending_reconciliation_count === 0
    && cockpit.safety.pending_readback_recovery_count === 0
    && cockpit.safety.unknown_write_count === 0
    && !cockpit.safety.kill_switch_active;
  return <>
    <section className={`daily-cockpit daily-cockpit--${statusTone(cockpit.primary_state)}`} data-primary-state={cockpit.primary_state}>
      <header className="daily-cockpit-rail">
        <div><span className="daily-live-mark"><i />V1 LIVE</span><Status value={cockpit.supervisor_state} label={`Supervisor ${words(cockpit.supervisor_state)}`} /><Status value={cockpit.controller_health} label={`Controller ${words(cockpit.controller_health)}`} /><Status value={cockpit.operating_mode} /></div>
        <div><span>SHA {cockpit.runtime_sha_short}</span><strong>{formatLocalClock(new Date(nowMs).toISOString(), cockpit.local_timezone)}</strong><small>Jim local</small></div>
      </header>
      <div className="daily-cockpit-core">
        <div className="daily-primary-state"><span>Runtime state</span><h1>{words(cockpit.primary_state)}</h1><p>{PRIMARY_STATE_COPY[cockpit.primary_state]}</p><div className="daily-heartbeat">Heartbeat age <b>{cockpit.heartbeat_age_seconds === null ? 'Unavailable' : `${cockpit.heartbeat_age_seconds}s`}</b></div></div>
        <div className="daily-schedule-block"><div><span>Next editorial wake</span><strong>{formatCountdown(cockpit.schedule.next_editorial_wake_utc, nowMs)}</strong><small>{words(cockpit.schedule.next_editorial_wake_reason)} · {formatLocalDateTime(cockpit.schedule.next_editorial_wake_utc, cockpit.local_timezone)} Jim local</small></div><div><span>Next X eligibility</span><strong>{formatCountdown(cockpit.schedule.next_x_eligible_capture_utc, nowMs)}</strong><small>{words(cockpit.schedule.x_cadence_state)} · no countdown is shown as active work</small></div></div>
      </div>
      <div className="daily-timeline" aria-label="Current canonical cycle timeline">
        {cockpit.timeline.length ? cockpit.timeline.map(step => <div key={step.stage} className={`daily-timeline-step is-${step.state}`}><i /><span>{step.label}</span></div>) : <span className="daily-timeline-empty">{cockpit.primary_state === 'RUNNING_IDLE' ? `Waiting → next editorial opportunity at ${formatLocalDateTime(cockpit.schedule.next_editorial_wake_utc, cockpit.local_timezone)} Jim local` : cockpit.primary_state === 'STOPPED' ? 'Timeline paused · supervisor is stopped.' : 'Timeline activates only when an exact canonical cycle stage is recorded.'}</span>}
      </div>
      <div className="daily-safety-strip">
        {safetyClear ? <span className="daily-safety-clear"><b>Publication safety</b> Clear · no active public write, unknown write, readback, or reconciliation backlog</span> : <>
          <span><b>Write</b> {cockpit.safety.active_public_write ? 'ACTIVE' : 'No active public write'}</span>
          <span><b>Reconciliation</b> {cockpit.safety.pending_reconciliation_count} pending</span>
          <span><b>Readback / recovery</b> {cockpit.safety.pending_readback_recovery_count} pending</span>
          <span><b>Unknown write</b> {cockpit.safety.unknown_write_count}</span>
          <span className={cockpit.safety.kill_switch_active ? 'is-alert' : ''}><b>Kill switch</b> {cockpit.safety.kill_switch_active ? 'ACTIVE' : 'Disengaged'}</span>
        </>}
        <span><b>Publication runtime</b> {words(cockpit.publication_runtime_health)}</span>
        <span><b>External browser activity</b> {cockpit.browser.external_browser_activity_active ? 'YES' : 'NO'} · {words(cockpit.browser.state)}{cockpit.browser.last_destination ? ` · ${cockpit.browser.last_destination}` : ''}</span>
        <span><b>Last browser interaction</b> {formatLocalDateTime(cockpit.browser.last_active_at_utc, cockpit.local_timezone)} · {words(cockpit.browser.last_reason ?? 'NONE')}</span>
        <span><b>Operator trigger</b> {cockpit.schedule.operator_trigger_pending ? 'PENDING' : 'None'}</span>
      </div>
    </section>
    <div className="daily-cockpit-support">
      <Panel title="Activity" eyebrow="Current or last completed" className="daily-activity-panel"><ActivitySummary cockpit={cockpit} nowMs={nowMs} /></Panel>
      <Panel title="X intake" eyebrow="Continuous intelligence" className={cockpit.intake.lane_state === 'DEGRADED' ? 'daily-intake-degraded' : ''}>
        <div className="daily-intake-head"><Status value={cockpit.intake.lane_state} /><strong>{cockpit.intake.rolling_24h_unique_headlines ?? '—'}<small>unique / 24h</small></strong></div>
        <dl className="daily-compact-facts"><div><dt>Newest source event</dt><dd>{cockpit.intake.newest_source_event_age_seconds === null ? 'Unavailable' : `${formatDuration(cockpit.intake.newest_source_event_age_seconds)} ago`}</dd></div><div><dt>Latest capture</dt><dd>{formatLocalDateTime(cockpit.intake.latest_capture_at_utc, cockpit.local_timezone)} · {words(cockpit.intake.latest_capture_result)}</dd></div><div><dt>Next eligible</dt><dd>{formatLocalDateTime(cockpit.intake.next_eligible_capture_utc ?? null, cockpit.local_timezone)}</dd></div><div><dt>Cadence</dt><dd>{words(cockpit.intake.cadence_state)}</dd></div></dl>
      </Panel>
    </div>
    <Panel title="Recent runtime activity" eyebrow="Editorial cycles + X intake">
      {cockpit.recent_activity.length ? <div className="daily-history-table" role="table"><div className="daily-history-row daily-history-header" role="row"><span>Time / type</span><span>Story or lane</span><span>Duration</span><span>Result</span></div>{cockpit.recent_activity.map((row, index) => <div className="daily-history-row" role="row" key={`${row.activity_type}:${row.work_item_id ?? row.started_at_utc}:${index}`}><span><b>{formatLocalDateTime(row.started_at_utc, cockpit.local_timezone)}</b><small>{words(row.activity_type)}</small></span><span>{row.story_label ?? 'No story label recorded'}<small>{row.candidate_rank ? `Candidate ${row.candidate_rank} / ${row.candidate_count ?? '—'} · ` : ''}{row.grounding ?? ''}</small></span><span>{formatDuration(row.duration_seconds)}</span><span><Status value={row.result} />{row.canonical_public_url && <a href={row.canonical_public_url} target="_blank" rel="noreferrer" aria-label="Open canonical Substack article"><ExternalLink /></a>}</span></div>)}</div> : <Empty title="No runtime history recorded" detail="The durable store has no completed editorial cycle or X capture timestamp to show." />}
    </Panel>
  </>;
}

function Today({ data, refresh, hourlyAudit }: { data: DailyAppSnapshot; refresh: () => Promise<void>; hourlyAudit: HourlyAudit | null }) {
  const cycle = data.today.current_cycle;
  const nextAction = data.incidents.active_count > 0
    ? 'Review the active incident lifecycle before any intervention.'
    : data.queue.items.length > 0 ? 'The next governed queue item is scheduled.' : 'No operator action is currently recorded.';
  return <div className="daily-view">
    <RuntimeCockpitView data={data} />
    <div className="daily-grid-3"><Panel title="Hourly audit" eyebrow="Independent readback"><Status value={hourlyAudit?.classification ?? 'AUDIT_NOT_YET_AVAILABLE'} /><p>Last run: {formatUtcDateTime(hourlyAudit?.generated_at_utc)}</p></Panel><Panel title="Next safe action" eyebrow="Operator"><p className="daily-callout">{nextAction}</p><Status value={data.incidents.active_count ? 'ATTENTION_REQUIRED' : 'NO_ACTION_REQUIRED'} /></Panel><RunEditorialNow data={data} refresh={refresh} /></div>
    <Panel title="Current cycle" eyebrow="Today">
      {cycle ? <DefinitionRows object={cycle} /> : <Empty title="No governed cycle recorded" detail="The durable store has no current cycle. The console will not invent one." />}
    </Panel>
    <Panel title="Continuous intelligence" eyebrow="Newsroom input truth">
      <div className="daily-grid-4">
        <Metric label="Headline ingestion" value={words(data.runtime.headline_ingestion?.lane_state ?? 'UNAVAILABLE')} status={data.runtime.headline_ingestion?.lane_state} />
        <Metric label="Last headline ingest" value={formatUtcDateTime(data.runtime.headline_ingestion?.last_ingest_utc)} />
        <Metric label="Next eligible X capture" value={formatUtcDateTime(data.runtime.headline_ingestion?.next_eligible_capture_utc)} />
        <Metric label="X cadence" value={words(data.runtime.headline_ingestion?.cadence_state ?? 'UNAVAILABLE')} />
        <Metric label="Rolling 24h unique headlines" value={data.runtime.rolling_24h_unique_headlines ?? 'Unavailable'} />
        <Metric label="Capital Chronicle read model" value={words(data.runtime.capital_chronicle_read_model)} status={data.runtime.capital_chronicle_read_model} />
      </div>
      <div className="daily-grid-3">
        <Metric label="Browser automation" value={words(data.runtime.browser_automation?.state ?? 'IDLE')} status={data.runtime.browser_automation?.state ?? 'IDLE'} />
        <Metric label="Last browser interaction" value={formatUtcDateTime(data.runtime.browser_automation?.last_active_browser_interaction_at_utc)} />
        <Metric label="Browser reason" value={words(data.runtime.browser_automation?.last_reason ?? 'NONE')} />
      </div>
      <div className="daily-grid-3">
        <Metric label="Published today" value={data.today.published_today_count} status={data.today.published_today_count ? 'PUBLISHED' : 'NONE_TODAY'} />
        <Metric label="Daily target" value={`${(data.today.daily_target_band ?? [5, 8])[0]}–${(data.today.daily_target_band ?? [5, 8])[1]}`} />
        <Metric label="Published corpus" value={data.today.published_corpus_count} />
      </div>
      <div className="daily-grid-4">
        <Metric label="Latest classification" value={words(data.today.latest_editorial_classification ?? 'UNAVAILABLE')} status={data.today.latest_editorial_classification} />
        <Metric label="Article / update mode" value={words(data.today.latest_article_update_mode ?? 'UNAVAILABLE')} />
        <Metric label="CC matched stores" value={data.today.latest_cc_matched_store_count ?? 'Unavailable'} />
        <Metric label="Material-event wake" value={words(data.queue.material_event_wake_state)} status={data.queue.material_event_wake_state} />
      </div>
      <div className="daily-grid-4">
        <Metric label="Prior related article" value={data.today.latest_prior_related_article_title ?? data.today.latest_prior_related_article_identity ?? 'None'} />
        <Metric label="Material delta" value={words(data.today.latest_material_delta_status ?? 'UNAVAILABLE')} />
        <Metric label="Decision reason" value={words(data.today.latest_decision_reason ?? 'UNAVAILABLE')} />
        <Metric label="Stage stopped" value={words(data.today.latest_stage_stopped ?? 'UNAVAILABLE')} />
      </div>
    </Panel>
    <div className="daily-grid-3">
      <Metric label="Lifecycle recovery" value={data.today.pending_lifecycle_recovery_count} status={data.today.pending_lifecycle_recovery_count ? 'PENDING' : 'CLEAR'} />
      <Metric label="Real publications" value={data.published.real_publication_count} status={data.published.real_publication_count ? 'CONFIRMED' : 'NONE_RECORDED'} />
      <Metric label="Headline freshness" value={words(data.runtime.headline_freshness)} status={data.runtime.headline_freshness} />
    </div>
    <div className="daily-grid-4">
      <Metric label="Provider invocations" value={data.runtime.provider_invocation_count} />
      <Metric label="Prompt tokens" value={data.runtime.prompt_tokens} />
      <Metric label="Completion tokens" value={data.runtime.completion_tokens} />
      <Metric label="Cost state" value={words(data.runtime.cost_metadata)} status={data.runtime.cost_metadata} />
    </div>
  </div>;
}

function Queue({ data }: { data: DailyAppSnapshot }) {
  return <div className="daily-view"><ViewTitle title="Queue" detail="Editorial windows, lifecycle recovery, and due performance observations." />
    <div className="daily-grid-3"><Metric label="Active / held work" value={data.queue.active_or_held_work_count} /><Metric label="Pending readback" value={data.queue.pending_readback_count} status={data.queue.pending_readback_count ? 'PENDING' : 'CLEAR'} /><Metric label="Due observations" value={data.queue.due_performance_observation_count} status={data.queue.due_performance_observation_count ? 'DUE' : 'CLEAR'} /></div>
    <Panel title="Governed queue">{data.queue.items.length ? <CardList items={data.queue.items} titleKey="title" statusKey="state" /> : <Empty title="Queue is clear" detail="No lifecycle recovery, observation, or upcoming editorial item is recorded." />}</Panel>
  </div>;
}

function Published({ data }: { data: DailyAppSnapshot }) {
  return <div className="daily-view"><ViewTitle title="Published" detail="Confirmed public objects, controlled no-writes, and unresolved write truth stay distinct." />
    <div className="daily-grid-4"><Metric label="Real confirmed" value={data.published.real_publication_count} status={data.published.real_publication_count ? 'CONFIRMED' : 'NONE_RECORDED'} /><Metric label="Controlled no-write" value={data.published.controlled_no_public_write_count} status={data.published.controlled_no_public_write_count ? 'CONTROLLED_NO_PUBLIC_WRITE' : 'NONE_RECORDED'} /><Metric label="Unknown write" value={data.published.unknown_write_count} status={data.published.unknown_write_count ? 'UNKNOWN_WRITE' : 'NONE'} /><Metric label="Pending readback" value={data.published.pending_readback_count} status={data.published.pending_readback_count ? 'PENDING' : 'NONE'} /></div>
    <Panel title="Publication lifecycle">{data.published.objects.length ? <CardList items={data.published.objects} titleKey="platform" statusKey="lifecycle_classification" /> : <Empty title={words(data.published.empty_reason)} detail="No durable platform dispatch exists. Nothing is represented as published." />}</Panel>
  </div>;
}

function Performance({ data }: { data: DailyAppSnapshot }) {
  return <div className="daily-view"><ViewTitle title="Performance" detail="Native platform observations only; unavailable metrics never become zero." />
    <Panel title="Observation windows">{data.performance.observations.length ? <CardList items={data.performance.observations} titleKey="platform" statusKey="collection_status" /> : <Empty title={words(data.performance.empty_reason)} detail={data.performance.empty_detail ?? 'No native performance observation is recorded.'} />}</Panel>
  </div>;
}

function Learning({ data }: { data: DailyAppSnapshot }) {
  const policy = data.learning.active_policy ?? data.learning.configured_default;
  const learned = policy?.provenance === 'LEARNED';
  return <div className="daily-view"><ViewTitle title="Learning" detail="Bounded policy provenance, sample support, and rollback identity." />
    <Panel title={learned ? 'Active learned policy' : 'Configured default'}>{policy ? <DefinitionRows object={policy} /> : <Empty title="No learning update yet" detail="No eligible observations have produced a bounded policy decision." />}</Panel>
    <Panel title="Policy history">{data.learning.policy_history.length ? <CardList items={data.learning.policy_history} titleKey="policy_version" statusKey="status" /> : <Empty title={words(data.learning.empty_reason)} detail="The default is configuration, not learned evidence." />}</Panel>
  </div>;
}

function Platforms({ data }: { data: DailyAppSnapshot }) {
  return <div className="daily-view"><ViewTitle title="Platforms" detail="Canonical readiness, verified safe identity, readback, and metrics availability by destination." />
    <div className="daily-platform-grid">{data.platforms.destinations.map(item => <article className="daily-platform" key={String(item.platform_id)}><div><strong>{String(item.display_name)}</strong><small>{words(item.binding_class)}</small></div><Status value={item.readiness} /><DefinitionRows object={{ safe_identity: item.safe_identity, identity_match: item.identity_match, authenticated: item.authenticated, auth_expiry_at_utc: item.auth_expiry_at_utc, auth_days_remaining: item.auth_days_remaining, transport_type: item.transport_type, readback_capability: item.readback_capability, probed_at_utc: item.probed_at_utc, last_dispatch_state: item.last_dispatch_state, last_successful_readback_at_utc: item.last_successful_readback_at_utc, metrics_capability: item.metrics_capability, next_metric_availability: item.next_metric_availability, pending_incident: item.pending_incident }} /></article>)}</div>
  </div>;
}

function Incidents({ data }: { data: DailyAppSnapshot }) {
  return <div className="daily-view"><ViewTitle title="Incidents" detail="What happened, what is safe now, automatic recovery, and exact operator action." />
    {data.incidents.items.length ? <div className="daily-stack">{data.incidents.items.map(item => <Panel key={String(item.incident_id)} title={words(item.what_happened)} eyebrow={String(item.severity)}><DefinitionRows object={{ safe_now: item.safe_now, automatic_action: item.automatic_action, operator_action: item.operator_action, work_item_id: item.work_item_id }} /></Panel>)}</div> : <Empty title={words(data.incidents.empty_reason)} detail="No durable or derived incident requires attention." />}
  </div>;
}

function BackgroundLogs({ data }: { data: DailyAppSnapshot }) {
  const streams = data.controls.background_log_streams ?? [];
  const [stream, setStream] = useState(streams[0]?.stream ?? 'supervisor_stderr');
  const [tail, setTail] = useState<BackgroundLogTail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const refresh = useCallback(async () => {
    try {
      const response = await fetch(`${API_ROOT}${data.controls.background_logs_endpoint ?? '/api/daily-app/background-logs'}?stream=${encodeURIComponent(stream)}&lines=200`, { headers: { Accept: 'application/json' }, cache: 'no-store' });
      const result = await response.json() as BackgroundLogTail & { error?: string };
      if (!response.ok) throw new Error(result.error ?? `Log unavailable (${response.status})`);
      setTail(result); setError(null);
    } catch (caught) { setError(caught instanceof Error ? caught.message : 'Log unavailable'); }
  }, [data.controls.background_logs_endpoint, stream]);
  useEffect(() => {
    void refresh();
    const timer = window.setInterval(() => { if (document.visibilityState === 'visible') void refresh(); }, 5_000);
    return () => window.clearInterval(timer);
  }, [refresh]);
  return <div className="daily-view"><ViewTitle title="Background logs" detail="Sanitized, bounded tails from a fixed server-side allowlist. No caller-selected path is accepted." />
    <Panel title="Log stream" eyebrow="Auto-refresh · 5 seconds">
      <div className="daily-log-toolbar"><label htmlFor="daily-log-stream">Allowlisted stream</label><select id="daily-log-stream" value={stream} onChange={event => setStream(event.target.value)}>{streams.map(item => <option key={item.stream} value={item.stream}>{item.label}</option>)}</select><button type="button" onClick={() => void refresh()}>Refresh</button></div>
      {error && <p role="alert" className="daily-control-message">{error}</p>}
      {tail && <><div className="daily-log-meta"><Status value={tail.status} /><span>{tail.line_count} lines</span><span>Updated {formatUtcDateTime(tail.latest_timestamp_utc)}</span>{tail.truncated && <span>Bounded tail</span>}</div><pre className="daily-log-output">{tail.content || 'No log content recorded yet.'}</pre></>}
    </Panel>
  </div>;
}

function Controls({ data, refresh }: { data: DailyAppSnapshot; refresh: () => Promise<void> }) {
  const [pending, setPending] = useState<OperatingMode | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [shutdownPending, setShutdownPending] = useState(false);
  const changeMode = async (mode: OperatingMode) => {
    setPending(mode); setMessage(null);
    try {
      const response = await fetch(`${API_ROOT}${data.controls.write_endpoint}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ operating_mode: mode, expected_state_version: data.controls.state_version }),
      });
      const result = await response.json() as { error?: string };
      if (!response.ok) throw new Error(result.error ?? `Control update failed (${response.status})`);
      setMessage(`${words(mode)} recorded. This control did not launch or publish anything.`);
      await refresh();
    } catch (error) { setMessage(error instanceof Error ? error.message : 'Control update failed'); }
    finally { setPending(null); }
  };
  const shutdown = async () => {
    if (data.controls.shutdown_allowed !== true || shutdownPending) return;
    const confirmed = window.confirm('Shutdown every proven ContentOps background process? The canonical store and Chrome/Edge profiles are preserved. The dashboard will go offline after verification starts.');
    if (!confirmed) return;
    setShutdownPending(true); setMessage(null);
    try {
      const response = await fetch(`${API_ROOT}${data.controls.shutdown_endpoint ?? '/api/daily-app/control/shutdown-all-background'}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'SHUTDOWN_ALL_BACKGROUND', expected_state_version: data.controls.state_version }),
      });
      const result = await response.json() as { status?: string; error?: string };
      if (!response.ok) throw new Error(result.error ?? `Shutdown rejected (${response.status})`);
      setMessage('Safe shutdown started. KILL_SWITCH and the durable model pause are active; only proven ContentOps background processes will stop. Store and browser profiles are preserved.');
    } catch (error) { setMessage(error instanceof Error ? error.message : 'Shutdown failed closed'); setShutdownPending(false); }
  };
  return <div className="daily-view"><ViewTitle title="Controls" detail="The console writes are a CAS mode change and a durable run-now trigger. Neither launches a pipeline directly, changes a gate, nor clears the kill switch." />
    {data.runtime.kill_switch_active && <div className="daily-kill-banner"><ShieldAlert />Kill switch is active. New public writes are blocked.</div>}
    <Panel title="Operating mode" eyebrow={`State version ${data.controls.state_version}`}><div className="daily-control-list">{data.controls.allowed_modes.map(mode => <button type="button" key={mode} className={mode === data.controls.current_mode ? 'is-active' : mode === 'KILL_SWITCH' ? 'is-kill' : ''} disabled={pending !== null || mode === data.controls.current_mode} onClick={() => void changeMode(mode)}><span><strong>{words(mode)}</strong><small>{data.controls.semantics[mode]}</small></span>{mode === data.controls.current_mode ? <Status value="CURRENT" /> : <ChevronRight />}</button>)}</div></Panel>
    <Panel title="Shutdown all background" eyebrow="Fail-closed emergency control"><p>Activates KILL_SWITCH and the persistent model pause, then reuses the standalone shutdown fallback. It stops only proven ContentOps background processes and preserves the production store plus Chrome/Edge profiles.</p>{(data.controls.shutdown_blockers?.length ?? 0) > 0 && <p>Blocked: {(data.controls.shutdown_blockers ?? []).map(words).join(', ')}</p>}<button type="button" className="daily-shutdown-button" disabled={data.controls.shutdown_allowed !== true || shutdownPending} onClick={() => void shutdown()}>{shutdownPending ? 'Shutdown verification started…' : 'Shutdown all background'}</button></Panel>
    {message && <p role="status" className="daily-control-message">{message}</p>}
  </div>;
}

function Audit({ data, hourlyAudit }: { data: DailyAppSnapshot; hourlyAudit: HourlyAudit | null }) {
  return <div className="daily-view"><ViewTitle title="Evidence / Audit" detail="Read-model provenance and durable counts; no credential or raw browser state." />
    <Panel title="Latest independent hourly audit" eyebrow={formatUtcDateTime(hourlyAudit?.generated_at_utc)}>{hourlyAudit ? <><Status value={hourlyAudit.classification} /><DefinitionRows object={{ classification_reasons: hourlyAudit.classification_reasons, runtime: hourlyAudit.runtime, browsers: hourlyAudit.browsers, browser_interaction: hourlyAudit.browser_interaction, safety: hourlyAudit.safety, stderr_signal: hourlyAudit.stderr_signal, scheduled_task: hourlyAudit.scheduled_task }} /></> : <Empty title="Audit not yet available" detail="Run or install the independent hourly audit to create the first compact artifact." />}</Panel>
    <div className="daily-grid-4"><Metric label="Work items" value={data.audit.work_item_count} /><Metric label="Transitions" value={data.audit.transition_event_count} /><Metric label="Artifacts" value={data.audit.artifact_reference_count} /><Metric label="Reviews" value={data.audit.review_record_count} /></div>
    <Panel title="Authority"><DefinitionRows object={data.authority} /></Panel>
    <Panel title="Recent transition events">{data.audit.recent_events.length ? <CardList items={data.audit.recent_events} titleKey="event_kind" statusKey="to_state" /> : <Empty title="No transition evidence recorded" detail="The canonical store has no transition event rows." />}</Panel>
  </div>;
}

function CardList({ items, titleKey, statusKey }: { items: Array<Record<string, unknown>>; titleKey: string; statusKey: string }) {
  return <div className="daily-card-list">{items.map((item, index) => {
    const durableIdentity = item.queue_id ?? item.observation_id ?? item.dispatch_id ?? item.policy_version ?? item.event_id ?? 'row';
    return <article key={`${String(durableIdentity)}:${index}`}><header><strong>{words(item[titleKey])}</strong><Status value={item[statusKey]} /></header><DefinitionRows object={Object.fromEntries(Object.entries(item).filter(([key]) => ![titleKey, statusKey].includes(key)))} /></article>;
  })}</div>;
}

function ViewTitle({ title, detail }: { title: string; detail: string }) {
  return <header className="daily-view-title"><div className="daily-eyebrow">Capital Chronicle · Daily App</div><h1>{title}</h1><p>{detail}</p></header>;
}

export function DailyAppConsole() {
  const [view, setView] = useState<DailyView>('today');
  const [navOpen, setNavOpen] = useState(false);
  const [state, refresh] = useDailyAppSnapshot();
  const snapshot = state.snapshot;
  const qaFixture = runtimeQaFixtureName();
  const activeLabel = useMemo(() => NAV.flatMap(group => group.items).find(item => item.id === view)?.label ?? 'Today', [view]);

  return <div className="daily-shell" data-theme="daily-dark">
    {navOpen && <button type="button" className="daily-scrim" aria-label="Close navigation" onClick={() => setNavOpen(false)} />}
    <aside className={`daily-nav ${navOpen ? 'is-open' : ''}`} aria-label="Primary navigation">
      <div className="daily-brand"><div className="daily-mark">CC</div><div><strong>ContentOps</strong><small>Daily App · V1</small></div><button type="button" onClick={() => setNavOpen(false)} aria-label="Close navigation"><PanelLeftClose /></button></div>
      <nav>{NAV.map(group => <div className="daily-nav-group" key={group.group}><span>{group.group}</span>{group.items.map(item => { const Icon = item.icon; return <button type="button" key={item.id} aria-current={view === item.id ? 'page' : undefined} onClick={() => { setView(item.id); setNavOpen(false); }}><Icon /><b>{item.label}</b>{item.id === 'incidents' && snapshot && snapshot.incidents.active_count > 0 && <em>{snapshot.incidents.active_count}</em>}</button>; })}</div>)}</nav>
      <div className="daily-nav-foot"><Shield /><span><b>Local control plane</b><small>No public-write launcher</small></span></div>
    </aside>
    <div className="daily-main">
      <header className="daily-topbar"><button type="button" className="daily-menu" onClick={() => setNavOpen(true)} aria-label="Open navigation"><Menu /></button><div><span>{activeLabel}</span>{snapshot && <Status value={snapshot.runtime.operator_cockpit?.primary_state ?? snapshot.runtime.operating_mode} />}</div><div className="daily-top-actions">{snapshot && <Status value={state.kind === 'online' ? snapshot.freshness.state : 'OFFLINE_STALE_VIEW'} />}<button type="button" onClick={() => void refresh()} aria-label="Refresh snapshot"><RefreshCw /></button></div></header>
      {state.kind === 'offline' && <div className="daily-offline" role="alert"><AlertTriangle /> <span><strong>Live snapshot unavailable.</strong> {snapshot ? 'Showing the last received snapshot; it may be stale.' : 'No fixture or fallback data is shown.'} {state.error}</span></div>}
      {qaFixture && <div className="daily-qa-banner" role="status">Deterministic local browser-QA fixture · {words(qaFixture)} · not runtime authority</div>}
      <main id="daily-workspace">
        {state.kind === 'loading' && <div className="daily-loading"><Gauge /><span>Reading canonical operating state…</span></div>}
        {!snapshot && state.kind === 'offline' && <Empty title="Operating state unavailable" detail="Start the loopback API with an explicit canonical store binding. This surface has no fixture fallback." />}
        {snapshot && <>
          {view === 'today' && <Today data={snapshot} refresh={refresh} hourlyAudit={snapshot.hourly_audit ?? null} />}
          {view === 'queue' && <Queue data={snapshot} />}
          {view === 'published' && <Published data={snapshot} />}
          {view === 'performance' && <Performance data={snapshot} />}
          {view === 'learning' && <Learning data={snapshot} />}
          {view === 'platforms' && <Platforms data={snapshot} />}
          {view === 'incidents' && <Incidents data={snapshot} />}
          {view === 'controls' && <Controls data={snapshot} refresh={refresh} />}
          {view === 'background_logs' && <BackgroundLogs data={snapshot} />}
          {view === 'audit' && <Audit data={snapshot} hourlyAudit={snapshot.hourly_audit ?? null} />}
        </>}
      </main>
    </div>
  </div>;
}
