import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Activity, AlertTriangle, Archive, BarChart3, BookOpenCheck, CalendarClock,
  ChevronRight, CircleOff, Database, Gauge, Menu, PanelLeftClose, RefreshCw,
  Shield, ShieldAlert, SlidersHorizontal, Sparkles,
} from 'lucide-react';
import type { DailyAppSnapshot, DailyView, LoadState, OperatingMode } from '../dailyAppTypes';

const API_ROOT = 'http://127.0.0.1:5174';
const POLL_MS = 15_000;

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
      const snapshot = await response.json() as DailyAppSnapshot;
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
  if (/UNKNOWN|KILL|CRITICAL|FAILED|BLOCKED|OFFLINE/.test(status)) return 'bad';
  if (/PENDING|STALE|DUE|REVIEW|UNAVAILABLE|HELD|SUPERVISED/.test(status)) return 'warn';
  if (/HEALTHY|READY|CONFIRMED|PUBLISHED|CURRENT|ACTIVE|RECONCILED|AVAILABLE/.test(status)) return 'good';
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

function Today({ data, refresh }: { data: DailyAppSnapshot; refresh: () => Promise<void> }) {
  const cycle = data.today.current_cycle;
  const nextAction = data.incidents.active_count > 0
    ? 'Review the active incident lifecycle before any intervention.'
    : data.queue.items.length > 0 ? 'The next governed queue item is scheduled.' : 'No operator action is currently recorded.';
  return <div className="daily-view">
    <div className="daily-first-fold">
      <Panel title="Operating mode" eyebrow="Control posture"><Status value={data.runtime.operating_mode} /><p>{data.controls.semantics[data.runtime.operating_mode]}</p><Status value={data.runtime.kill_switch_active ? 'KILL_SWITCH_ACTIVE' : 'KILL_SWITCH_DISENGAGED'} /></Panel>
      <Panel title="Controller health" eyebrow="Runtime"><Status value={data.runtime.controller_health} /><p>Last heartbeat: {formatUtcDateTime(data.runtime.latest_heartbeat_at_utc)}</p></Panel>
      <RunEditorialNow data={data} refresh={refresh} />
      <Panel title="Next safe action" eyebrow="Operator"><p className="daily-callout">{nextAction}</p><p>Next wake: {formatUtcDateTime(data.runtime.next_wake_utc)}</p><Status value={data.runtime.next_editorial_window?.provenance ?? 'WINDOW_PROVENANCE_UNAVAILABLE'} /></Panel>
      <Panel title="Active incidents" eyebrow="Safety"><strong className="daily-big-number">{data.incidents.active_count}</strong><Status value={data.incidents.active_count ? 'ATTENTION_REQUIRED' : 'NO_ACTIVE_INCIDENTS'} /></Panel>
    </div>
    <Panel title="Current cycle" eyebrow="Today">
      {cycle ? <DefinitionRows object={cycle} /> : <Empty title="No governed cycle recorded" detail="The durable store has no current cycle. The console will not invent one." />}
    </Panel>
    <Panel title="Continuous intelligence" eyebrow="Newsroom input truth">
      <div className="daily-grid-4">
        <Metric label="Headline ingestion" value={words(data.runtime.headline_ingestion?.lane_state ?? 'UNAVAILABLE')} status={data.runtime.headline_ingestion?.lane_state} />
        <Metric label="Last headline ingest" value={formatUtcDateTime(data.runtime.headline_ingestion?.last_ingest_utc)} />
        <Metric label="Rolling 24h unique headlines" value={data.runtime.rolling_24h_unique_headlines ?? 'Unavailable'} />
        <Metric label="Capital Chronicle read model" value={words(data.runtime.capital_chronicle_read_model)} status={data.runtime.capital_chronicle_read_model} />
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
    <div className="daily-platform-grid">{data.platforms.destinations.map(item => <article className="daily-platform" key={String(item.platform_id)}><div><strong>{String(item.display_name)}</strong><small>{words(item.binding_class)}</small></div><Status value={item.readiness} /><DefinitionRows object={{ safe_identity: item.safe_identity, identity_match: item.identity_match, transport_type: item.transport_type, probed_at_utc: item.probed_at_utc, last_dispatch_state: item.last_dispatch_state, last_successful_readback_at_utc: item.last_successful_readback_at_utc, metrics_capability: item.metrics_capability, next_metric_availability: item.next_metric_availability, pending_incident: item.pending_incident }} /></article>)}</div>
  </div>;
}

function Incidents({ data }: { data: DailyAppSnapshot }) {
  return <div className="daily-view"><ViewTitle title="Incidents" detail="What happened, what is safe now, automatic recovery, and exact operator action." />
    {data.incidents.items.length ? <div className="daily-stack">{data.incidents.items.map(item => <Panel key={String(item.incident_id)} title={words(item.what_happened)} eyebrow={String(item.severity)}><DefinitionRows object={{ safe_now: item.safe_now, automatic_action: item.automatic_action, operator_action: item.operator_action, work_item_id: item.work_item_id }} /></Panel>)}</div> : <Empty title={words(data.incidents.empty_reason)} detail="No durable or derived incident requires attention." />}
  </div>;
}

function Controls({ data, refresh }: { data: DailyAppSnapshot; refresh: () => Promise<void> }) {
  const [pending, setPending] = useState<OperatingMode | null>(null);
  const [message, setMessage] = useState<string | null>(null);
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
  return <div className="daily-view"><ViewTitle title="Controls" detail="The console writes are a CAS mode change and a durable run-now trigger. Neither launches a pipeline directly, changes a gate, nor clears the kill switch." />
    {data.runtime.kill_switch_active && <div className="daily-kill-banner"><ShieldAlert />Kill switch is active. New public writes are blocked.</div>}
    <Panel title="Operating mode" eyebrow={`State version ${data.controls.state_version}`}><div className="daily-control-list">{data.controls.allowed_modes.map(mode => <button type="button" key={mode} className={mode === data.controls.current_mode ? 'is-active' : mode === 'KILL_SWITCH' ? 'is-kill' : ''} disabled={pending !== null || mode === data.controls.current_mode} onClick={() => void changeMode(mode)}><span><strong>{words(mode)}</strong><small>{data.controls.semantics[mode]}</small></span>{mode === data.controls.current_mode ? <Status value="CURRENT" /> : <ChevronRight />}</button>)}</div>{message && <p role="status" className="daily-control-message">{message}</p>}</Panel>
  </div>;
}

function Audit({ data }: { data: DailyAppSnapshot }) {
  return <div className="daily-view"><ViewTitle title="Evidence / Audit" detail="Read-model provenance and durable counts; no credential or raw browser state." />
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
  const activeLabel = useMemo(() => NAV.flatMap(group => group.items).find(item => item.id === view)?.label ?? 'Today', [view]);

  return <div className="daily-shell" data-theme="daily-dark">
    {navOpen && <button type="button" className="daily-scrim" aria-label="Close navigation" onClick={() => setNavOpen(false)} />}
    <aside className={`daily-nav ${navOpen ? 'is-open' : ''}`} aria-label="Primary navigation">
      <div className="daily-brand"><div className="daily-mark">CC</div><div><strong>ContentOps</strong><small>Daily App · V1</small></div><button type="button" onClick={() => setNavOpen(false)} aria-label="Close navigation"><PanelLeftClose /></button></div>
      <nav>{NAV.map(group => <div className="daily-nav-group" key={group.group}><span>{group.group}</span>{group.items.map(item => { const Icon = item.icon; return <button type="button" key={item.id} aria-current={view === item.id ? 'page' : undefined} onClick={() => { setView(item.id); setNavOpen(false); }}><Icon /><b>{item.label}</b>{item.id === 'incidents' && snapshot && snapshot.incidents.active_count > 0 && <em>{snapshot.incidents.active_count}</em>}</button>; })}</div>)}</nav>
      <div className="daily-nav-foot"><Shield /><span><b>Local control plane</b><small>No public-write launcher</small></span></div>
    </aside>
    <div className="daily-main">
      <header className="daily-topbar"><button type="button" className="daily-menu" onClick={() => setNavOpen(true)} aria-label="Open navigation"><Menu /></button><div><span>{activeLabel}</span>{snapshot && <Status value={snapshot.runtime.operating_mode} />}</div><div className="daily-top-actions">{snapshot && <Status value={state.kind === 'online' ? snapshot.freshness.state : 'OFFLINE_STALE_VIEW'} />}<button type="button" onClick={() => void refresh()} aria-label="Refresh snapshot"><RefreshCw /></button></div></header>
      {state.kind === 'offline' && <div className="daily-offline" role="alert"><AlertTriangle /> <span><strong>Live snapshot unavailable.</strong> {snapshot ? 'Showing the last received snapshot; it may be stale.' : 'No fixture or fallback data is shown.'} {state.error}</span></div>}
      <main id="daily-workspace">
        {state.kind === 'loading' && <div className="daily-loading"><Gauge /><span>Reading canonical operating state…</span></div>}
        {!snapshot && state.kind === 'offline' && <Empty title="Operating state unavailable" detail="Start the loopback API with an explicit canonical store binding. This surface has no fixture fallback." />}
        {snapshot && <>
          {view === 'today' && <Today data={snapshot} refresh={refresh} />}
          {view === 'queue' && <Queue data={snapshot} />}
          {view === 'published' && <Published data={snapshot} />}
          {view === 'performance' && <Performance data={snapshot} />}
          {view === 'learning' && <Learning data={snapshot} />}
          {view === 'platforms' && <Platforms data={snapshot} />}
          {view === 'incidents' && <Incidents data={snapshot} />}
          {view === 'controls' && <Controls data={snapshot} refresh={refresh} />}
          {view === 'audit' && <Audit data={snapshot} />}
        </>}
      </main>
    </div>
  </div>;
}
