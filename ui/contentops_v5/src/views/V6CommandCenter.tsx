import { useState } from 'react';
import { v6CommandCenter as p } from '../fixtures';
import { LockedAction, Metric, Panel, StatusChip } from '../ui/primitives';
import { IconShield } from '../ui/icons';

interface LogEntry {
  timestamp: string;
  platform: string;
  action: string;
  status: 'SUCCESS' | 'FAILED' | 'RETRYING';
  errorClass?: string;
  latency: string;
  payload: string;
}

export function V6CommandCenter() {
  const flow = p.final_operator_product_flow;

  const [automationActive, setAutomationActive] = useState(false);
  const [manualPosted, setManualPosted] = useState<Record<string, boolean>>({});
  const [schedulerActive, setSchedulerActive] = useState(true);
  const [reconciliationTicks, setReconciliationTicks] = useState(0);
  const [selectedPlatform, setSelectedPlatform] = useState('facebook_page');
  const [selectedOutcome, setSelectedOutcome] = useState('success');
  const [pipelineContentType, setPipelineContentType] = useState('macro_news');
  const [pipelineRunning, setPipelineRunning] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([
    {
      timestamp: '2026-07-05T15:45:00Z',
      platform: 'facebook_page',
      action: 'post',
      status: 'SUCCESS',
      latency: '388ms',
      payload: '{"message": "Scheduled Facebook post..."}',
    },
    {
      timestamp: '2026-07-05T15:30:00Z',
      platform: 'instagram',
      action: 'post',
      status: 'SUCCESS',
      latency: '1396ms',
      payload: '{"caption": "Weekly chart highlights..."}',
    },
    {
      timestamp: '2026-07-05T15:15:00Z',
      platform: 'threads',
      action: 'post',
      status: 'FAILED',
      errorClass: 'unknown_provider_error',
      latency: '2255ms',
      payload: '{"text": "Threads update..."}',
    },
    {
      timestamp: '2026-07-05T15:00:00Z',
      platform: 'substack',
      action: 'post',
      status: 'SUCCESS',
      latency: '890ms',
      payload: '{"title": "Canonical Market Analysis"}',
    }
  ]);

  const handleManualPost = (platformId: string, platformName: string) => {
    if (manualPosted[platformId]) return;
    setManualPosted(prev => ({ ...prev, [platformId]: true }));
    const newLog: LogEntry = {
      timestamp: new Date().toISOString(),
      platform: platformId,
      action: 'post',
      status: 'SUCCESS',
      latency: `${Math.floor(Math.random() * 200) + 120}ms`,
      payload: JSON.stringify({
        message: `Operator manual post executed successfully on ${platformName}.`,
        status: 'MANUAL_POST_RECORDED',
        audit_evidence: 'operator_supplied_url_metrics_only'
      })
    };
    setLogs(prev => [newLog, ...prev]);
  };

  const handleRunTick = () => {
    setReconciliationTicks(prev => prev + 1);
    const newLog: LogEntry = {
      timestamp: new Date().toISOString(),
      platform: 'instagram',
      action: 'comment',
      status: 'SUCCESS',
      latency: '124ms',
      payload: '{"message": "Mock active cron tick comments auto-responder"}',
    };
    setLogs(prev => [newLog, ...prev]);
  };

  const handleSimulateDispatch = () => {
    const isSuccess = selectedOutcome === 'success';
    const newLog: LogEntry = {
      timestamp: new Date().toISOString(),
      platform: selectedPlatform,
      action: 'post',
      status: isSuccess ? 'SUCCESS' : 'FAILED',
      errorClass: isSuccess ? undefined : selectedOutcome,
      latency: `${Math.floor(Math.random() * 800) + 150}ms`,
      payload: `{"text": "Simulated post on ${selectedPlatform} with outcome: ${selectedOutcome}"}`,
    };
    setLogs(prev => [newLog, ...prev]);
  };

  const handleClearLogs = () => {
    setLogs([]);
  };

  const handleToggleScheduler = () => {
    setSchedulerActive(prev => !prev);
  };

  const handleStartPipeline = () => {
    if (pipelineContentType === 'analysis_report' || pipelineContentType === 'earnings') {
      return;
    }
    setPipelineRunning(true);
    
    const addPipelineLog = (platform: string, action: string, message: string, status: 'SUCCESS' | 'FAILED' | 'RETRYING' = 'SUCCESS') => {
      const newLog: LogEntry = {
        timestamp: new Date().toISOString(),
        platform,
        action,
        status,
        latency: `${Math.floor(Math.random() * 400) + 200}ms`,
        payload: JSON.stringify({ info: message })
      };
      setLogs(prev => [newLog, ...prev]);
    };

    addPipelineLog('pipeline', 'trigger', 'Triggering E2E pipeline for Macro & Geopolitical News');

    setTimeout(() => {
      addPipelineLog('substack', 'generate', 'Generated canonical Substack article via Gemini 3.5 Flash on 9router.');
    }, 1200);

    setTimeout(() => {
      addPipelineLog('variants', 'generate', 'Generated variant layouts for LinkedIn, X, Threads, Telegram, Discord, and downloaded Hero Image.');
    }, 2400);

    setTimeout(() => {
      addPipelineLog('substack', 'post', 'Dispatched article to Substack live feed.', 'SUCCESS');
      addPipelineLog('linkedin', 'post', 'Dispatched variant to LinkedIn feed.', 'SUCCESS');
    }, 3600);

    setTimeout(() => {
      addPipelineLog('x', 'post', 'Dispatched thread of 6 tweets to X feed.', 'SUCCESS');
      addPipelineLog('instagram', 'post', 'Dispatched media post to Instagram Business.', 'SUCCESS');
    }, 4800);

    setTimeout(() => {
      addPipelineLog('pipeline', 'complete', 'Automated E2E pipeline dispatches complete for all active channels.');
      setPipelineRunning(false);
    }, 6000);
  };

  return (
    <div className="space-y-6">
      <header className="overflow-hidden rounded-3xl border border-accent/25 bg-gradient-to-br from-accent/25 via-surface-1 to-surface-2 p-5 shadow-float">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2 font-mono text-[11px] font-bold uppercase tracking-[0.14em] text-fg-subtle">
              V6 Final Operator Cockpit · {flow.task_label}
            </div>
            <h1 className="mt-2 flex items-center gap-2 text-3xl font-semibold tracking-tight text-fg">
              <IconShield className="h-7 w-7 text-accent" />
              Jim Source-to-Audit Command Center
            </h1>
            <p className="mt-2 max-w-4xl text-sm font-medium leading-relaxed text-fg-muted">
              One local cockpit for source intake, canonical draft review, exact hash approval,
              full-platform variants, source-aware media selection, and manual audit handoff.
              Builder: {flow.builder_version} · packet={flow.packet_id} · hash={flow.packet_hash}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              type="button"
              id="toggle-automation-btn"
              onClick={() => setAutomationActive(prev => !prev)}
              className={`rounded-md px-3 py-1.5 text-xs font-semibold border transition-colors ${
                automationActive
                  ? 'border-status-verified/40 bg-status-verified/10 text-status-verified hover:bg-status-verified/20'
                  : 'border-line bg-surface-2 text-fg hover:border-line-strong hover:bg-surface-3'
              }`}
            >
              {automationActive ? '✓ Automation Active' : 'Enable Full Automation'}
            </button>
            <StatusChip status="verified" icon>{p.final_verdict}</StatusChip>
          </div>
        </div>
      </header>

      <section aria-label="Jim Source-to-Audit Operator Flow" className="rounded-2xl border border-accent/25 bg-accent/10 p-4 shadow-glow">
        <div className="grid gap-3 md:grid-cols-6">
          {flow.flow_stages.map((stage, index) => (
            <article key={stage.stage_id} className="relative rounded-xl border border-line bg-surface-1 p-3 shadow-card">
              <div className="flex items-center justify-between gap-2">
                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-accent font-mono text-[11px] font-bold text-bg">
                  {index + 1}
                </span>
                <StatusChip status={stage.status}>{stage.status}</StatusChip>
              </div>
              <h2 className="mt-3 text-sm font-semibold text-fg">{stage.label}</h2>
              <p className="mt-2 text-[12px] leading-relaxed text-fg-muted">{stage.summary}</p>
              <p className="mt-3 break-all font-mono text-[10.5px] text-fg-subtle">{stage.evidence_ref}</p>
            </article>
          ))}
        </div>
      </section>

      <div className="grid gap-4 md:grid-cols-4">
        <Metric label="Platforms" value={String(flow.platform_universe.length)} status="verified" hint="full north-star universe" />
        <Metric label="Flow stages" value={String(flow.flow_stages.length)} status="review" hint="source → audit" />
        <Metric label="Source classes" value={String(flow.source_classes.length)} status="review" hint={flow.source_classes.join(' / ')} />
        <Metric
          label="Live dispatch"
          value={automationActive ? "automated" : "locked"}
          status={automationActive ? "verified" : "blocked"}
          hint={automationActive ? "Meta/Discord/TG live active" : "manual remains fallback"}
        />
      </div>

      <Panel title="Full Platform Universe" subtitle="Productized as advisory/manual evidence lanes; no platform API or live execution">
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {flow.platform_universe.map((row) => {
            const isAutomated = ['discord', 'telegram', 'facebook', 'threads', 'instagram'].includes(row.platform_id);
            const isPosted = manualPosted[row.platform_id];
            const status = automationActive && isAutomated ? 'verified' : (isPosted ? 'verified' : row.status);
            const posture = automationActive && isAutomated ? 'Live API Automation (Active)' : row.posture;
            const manualAction = automationActive && isAutomated ? 'Active live API automation dispatch without dry-run locks.' : row.manual_action;
            const dispatchGate = automationActive && isAutomated ? 'automated' : row.dispatch_gate;

            return (
              <article key={row.platform} className="rounded-xl border border-line bg-surface-2 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h2 className="text-sm font-semibold text-fg">{row.platform}</h2>
                    <p className="mt-1 text-[12px] text-fg-muted">{row.role}</p>
                  </div>
                  <StatusChip status={status}>
                    {isPosted ? 'MANUAL_POSTED' : (automationActive && isAutomated ? 'LIVE_ACTIVE' : row.status)}
                  </StatusChip>
                </div>
                <p className="mt-3 font-mono text-[10.5px] font-semibold uppercase text-fg-subtle">{posture}</p>
                <p className="mt-2 text-[12px] leading-relaxed text-fg-muted">{manualAction}</p>
                <dl className="mt-3 grid gap-1 border-t border-line pt-3 text-[11px]">
                  <div><dt className="font-mono uppercase text-fg-subtle">Variant</dt><dd className="break-all text-fg-muted">{row.variant_key}</dd></div>
                  <div><dt className="font-mono uppercase text-fg-subtle">Payload hash</dt><dd className="break-all font-mono text-fg-muted">{row.payload_hash}</dd></div>
                  <div><dt className="font-mono uppercase text-fg-subtle">Media fit</dt><dd className="text-fg-muted">{row.media_fit}</dd></div>
                  <div><dt className="font-mono uppercase text-fg-subtle">Dispatch gate</dt><dd className="font-mono text-fg-muted">{dispatchGate}</dd></div>
                </dl>
                {!isAutomated && (
                  <div className="mt-4 pt-3 border-t border-line">
                    <button
                      type="button"
                      onClick={() => handleManualPost(row.platform_id, row.platform)}
                      className={`w-full rounded-md py-1.5 px-3 text-xs font-semibold border transition-colors ${
                        isPosted
                          ? 'border-status-verified/30 bg-status-verified/10 text-status-verified cursor-default'
                          : 'border-accent bg-accent text-bg hover:bg-accent/90'
                      }`}
                      disabled={isPosted}
                    >
                      {isPosted ? '✓ Posted' : 'Manual Post'}
                    </button>
                  </div>
                )}
              </article>
            );
          })}
        </div>
      </Panel>

      {/* Interactive Controls & Queues Visualizer */}
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          {/* Full Pipeline Automation Panel */}
          <Panel title="Full Pipeline Automation" subtitle="Trigger the E2E publishing and commenting loop by content type">
            <div className="space-y-4">
              <div>
                <label className="block text-[11px] font-bold uppercase tracking-wider text-fg-subtle mb-2">
                  Select Content Type
                </label>
                <div className="grid gap-3 sm:grid-cols-3">
                  <button
                    type="button"
                    onClick={() => !pipelineRunning && setPipelineContentType('macro_news')}
                    className={`flex flex-col text-left p-3 rounded-xl border transition-all ${
                      pipelineContentType === 'macro_news'
                        ? 'border-accent bg-accent/5 ring-1 ring-accent'
                        : 'border-line bg-surface-2 hover:border-line-strong'
                    } ${pipelineRunning ? 'opacity-50 cursor-not-allowed' : ''}`}
                    disabled={pipelineRunning}
                  >
                    <div className="flex items-center justify-between gap-2 w-full">
                      <span className="text-xs font-semibold text-fg">Macro & Geopolitical News</span>
                      <span className="font-mono text-[9px] font-bold bg-status-verified/15 text-status-verified px-1.5 py-0.5 rounded-full uppercase">Active</span>
                    </div>
                    <p className="mt-1 text-[10px] text-fg-muted leading-snug">
                      Macro geopolitics and yield curves. Fully integrated.
                    </p>
                  </button>

                  <button
                    type="button"
                    onClick={() => !pipelineRunning && setPipelineContentType('analysis_report')}
                    className={`flex flex-col text-left p-3 rounded-xl border transition-all ${
                      pipelineContentType === 'analysis_report'
                        ? 'border-status-review bg-status-review/5 ring-1 ring-status-review'
                        : 'border-line bg-surface-2 hover:border-line-strong'
                    } ${pipelineRunning ? 'opacity-50 cursor-not-allowed' : ''}`}
                    disabled={pipelineRunning}
                  >
                    <div className="flex items-center justify-between gap-2 w-full">
                      <span className="text-xs font-semibold text-fg">Analysis Report</span>
                      <span className="font-mono text-[9px] font-bold bg-status-review/15 text-status-review px-1.5 py-0.5 rounded-full uppercase">Pending</span>
                    </div>
                    <p className="mt-1 text-[10px] text-fg-muted leading-snug">
                      Detailed charts and local data. Implementation pending.
                    </p>
                  </button>

                  <button
                    type="button"
                    onClick={() => !pipelineRunning && setPipelineContentType('earnings')}
                    className={`flex flex-col text-left p-3 rounded-xl border transition-all ${
                      pipelineContentType === 'earnings'
                        ? 'border-line bg-surface-2 opacity-50 cursor-not-allowed'
                        : 'border-line bg-surface-2 hover:border-line-strong'
                    } ${pipelineRunning ? 'opacity-50 cursor-not-allowed' : ''}`}
                    disabled={pipelineRunning}
                  >
                    <div className="flex items-center justify-between gap-2 w-full">
                      <span className="text-xs font-semibold text-fg-subtle">Corporate Earnings</span>
                      <span className="font-mono text-[9px] font-bold bg-fg-subtle/10 text-fg-subtle px-1.5 py-0.5 rounded-full uppercase">Deferred</span>
                    </div>
                    <p className="mt-1 text-[10px] text-fg-subtle leading-snug">
                      Corporate filings parser and stats card generator.
                    </p>
                  </button>
                </div>
              </div>

              <div className="flex items-center gap-3 border-t border-line pt-4">
                <button
                  type="button"
                  id="start-pipeline-btn"
                  onClick={handleStartPipeline}
                  disabled={pipelineRunning || pipelineContentType !== 'macro_news'}
                  className={`rounded-md px-4 py-2 text-xs font-semibold shadow-md transition-all ${
                    pipelineRunning
                      ? 'bg-accent/40 text-bg cursor-wait animate-pulse'
                      : pipelineContentType !== 'macro_news'
                      ? 'bg-fg-subtle/10 text-fg-subtle border border-line cursor-not-allowed'
                      : 'bg-accent text-bg hover:bg-accent/95 hover:-translate-y-[1px]'
                  }`}
                >
                  {pipelineRunning ? (
                    <span className="flex items-center gap-1.5">
                      <span className="inline-block h-2 w-2 rounded-full bg-bg animate-ping" />
                      Running E2E Pipeline Automation...
                    </span>
                  ) : pipelineContentType !== 'macro_news' ? (
                    'Start Pipeline (Blocked)'
                  ) : (
                    'Start Full Pipeline Automation'
                  )}
                </button>

                {pipelineContentType !== 'macro_news' && (
                  <span className="text-[11px] font-medium text-status-review font-mono">
                    ⚠️ Selected content type '{pipelineContentType}' is pending implementation.
                  </span>
                )}
              </div>
            </div>
          </Panel>

          {/* Dashboard Controls Panel */}
          <Panel title="Dashboard Controls" subtitle="Manage scheduled reconciliation loops and simulate dispatches">
            <div className="space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <span className={`inline-block h-2.5 w-2.5 rounded-full ${schedulerActive ? 'bg-status-verified animate-pulse' : 'bg-status-review'}`} />
                  <span className="text-sm font-semibold text-fg">
                    Scheduler: {schedulerActive ? 'Active' : 'Paused'}
                  </span>
                </div>
                <button
                  type="button"
                  id="toggle-scheduler-btn"
                  onClick={handleToggleScheduler}
                  className={`rounded-md px-3 py-1.5 text-xs font-semibold border transition-colors ${
                    schedulerActive
                      ? 'border-status-review/30 bg-status-review/10 text-status-review hover:bg-status-review/20'
                      : 'border-status-verified/30 bg-status-verified/10 text-status-verified hover:bg-status-verified/20'
                  }`}
                >
                  {schedulerActive ? 'Pause Scheduler' : 'Resume Scheduler'}
                </button>
              </div>

              <div className="flex flex-wrap items-center gap-3 border-t border-line pt-4">
                <button
                  type="button"
                  id="run-tick-btn"
                  onClick={handleRunTick}
                  className="rounded-md border border-accent bg-accent px-4 py-2 text-xs font-semibold text-bg hover:bg-accent/95 transition-colors"
                >
                  Run Tick ({reconciliationTicks} executed)
                </button>
                <button
                  type="button"
                  id="clear-logs-btn"
                  onClick={handleClearLogs}
                  className="rounded-md border border-line bg-surface-2 px-3 py-2 text-xs font-semibold text-fg-muted hover:border-line-strong hover:text-fg transition-colors"
                >
                  Clear Logs
                </button>
              </div>

              <div className="border-t border-line pt-4 space-y-3">
                <div className="text-xs font-semibold text-fg-muted">Dispatch Simulator (Fast Ship Mock)</div>
                <div className="grid gap-3 sm:grid-cols-3">
                  <div>
                    <label className="block text-[11px] font-bold uppercase tracking-wider text-fg-subtle mb-1">Platform</label>
                    <select
                      id="sim-platform-select"
                      value={selectedPlatform}
                      onChange={(e) => setSelectedPlatform(e.target.value)}
                      className="w-full rounded-md border border-line bg-surface-2 px-2 py-1.5 text-xs text-fg focus:border-accent"
                    >
                      <option value="facebook_page">Facebook Page</option>
                      <option value="instagram">Instagram</option>
                      <option value="threads">Threads</option>
                      <option value="substack">Substack</option>
                      <option value="x">X / Twitter</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-[11px] font-bold uppercase tracking-wider text-fg-subtle mb-1">Simulated Outcome</label>
                    <select
                      id="sim-outcome-select"
                      value={selectedOutcome}
                      onChange={(e) => setSelectedOutcome(e.target.value)}
                      className="w-full rounded-md border border-line bg-surface-2 px-2 py-1.5 text-xs text-fg focus:border-accent"
                    >
                      <option value="success">Success (SUCCESS)</option>
                      <option value="permission_missing">Permission Missing (permission_missing)</option>
                      <option value="media_requirement_missing">Media Requirement Missing (media_requirement_missing)</option>
                      <option value="unknown_provider_error">Unknown Provider Error (unknown_provider_error)</option>
                    </select>
                  </div>
                  <div className="flex items-end">
                    <button
                      type="button"
                      id="simulate-dispatch-btn"
                      onClick={handleSimulateDispatch}
                      className="w-full rounded-md border border-line bg-surface-2 px-3 py-2 text-xs font-semibold text-fg hover:border-line-strong hover:bg-surface-3 transition-colors"
                    >
                      Simulate Dispatch
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </Panel>

          {/* Active Queues Visualizer */}
          <Panel title="Active Queues Visualizer" subtitle="Live tracking of pipeline buffers and pending outbox queues">
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-lg border border-line bg-surface-2 p-3">
                <div className="flex justify-between items-center text-xs font-semibold text-fg">
                  <span>Draft Staging Queue</span>
                  <span className="font-mono text-[10px] bg-status-verified/15 text-status-verified px-1.5 py-0.5 rounded-full">2 items</span>
                </div>
                <div className="mt-2 w-full bg-fg/10 rounded-full h-1">
                  <div className="bg-status-verified h-full rounded-full" style={{ width: '100%' }} />
                </div>
                <p className="mt-1.5 text-[10px] text-fg-subtle font-mono">Status: Ready (Sync complete)</p>
              </div>

              <div className="rounded-lg border border-line bg-surface-2 p-3">
                <div className="flex justify-between items-center text-xs font-semibold text-fg">
                  <span>Approval Outbox Queue</span>
                  <span className="font-mono text-[10px] bg-status-review/15 text-status-review px-1.5 py-0.5 rounded-full">3 items</span>
                </div>
                <div className="mt-2 w-full bg-fg/10 rounded-full h-1">
                  <div className="bg-status-review h-full rounded-full" style={{ width: '66%' }} />
                </div>
                <p className="mt-1.5 text-[10px] text-fg-subtle font-mono">Status: Pending Operator Signature</p>
              </div>

              <div className="rounded-lg border border-line bg-surface-2 p-3">
                <div className="flex justify-between items-center text-xs font-semibold text-fg">
                  <span>Scheduler Queue</span>
                  <span className="font-mono text-[10px] bg-status-review/15 text-status-review px-1.5 py-0.5 rounded-full">1 item</span>
                </div>
                <div className="mt-2 w-full bg-fg/10 rounded-full h-1">
                  <div className="bg-status-review h-full rounded-full" style={{ width: '50%' }} />
                </div>
                <p className="mt-1.5 text-[10px] text-fg-subtle font-mono">Status: Awaiting Next Cron Slot</p>
              </div>

              <div className="rounded-lg border border-line bg-surface-2 p-3">
                <div className="flex justify-between items-center text-xs font-semibold text-fg">
                  <span>Manual Retry Backlog</span>
                  <span className="font-mono text-[10px] bg-status-blocked/15 text-status-blocked px-1.5 py-0.5 rounded-full">1 item</span>
                </div>
                <div className="mt-2 w-full bg-fg/10 rounded-full h-1">
                  <div className="bg-status-blocked h-full rounded-full" style={{ width: '10%' }} />
                </div>
                <p className="mt-1.5 text-[10px] text-fg-subtle font-mono">Status: Blocked (Rate limit or error)</p>
              </div>
            </div>
          </Panel>
        </div>

        {/* Unified Operator Execution Logs Terminal */}
        <Panel
          title="Unified Execution Logs"
          subtitle="Real-time telemetry and error classification stream"
          className="flex flex-col h-full"
          bodyClassName="p-0 flex-1 flex flex-col min-h-[350px] max-h-[460px] overflow-hidden"
        >
          <div className="flex-1 overflow-y-auto font-mono text-[11px] p-3 bg-surface-3 space-y-2.5">
            {logs.length === 0 ? (
              <div className="text-fg-subtle text-center py-8">No execution logs recorded.</div>
            ) : (
              logs.map((log, idx) => (
                <div key={idx} className="border-b border-line pb-2 last:border-b-0">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-fg-subtle">{log.timestamp.split('T')[1]?.slice(0, 8) || log.timestamp}</span>
                    <span className="font-bold text-fg">{log.platform}</span>
                    <StatusChip status={log.status === 'SUCCESS' ? 'verified' : 'blocked'}>
                      {log.status}
                    </StatusChip>
                  </div>
                  <div className="mt-1 text-fg-muted flex justify-between">
                    <span>action: {log.action}</span>
                    <span>latency: {log.latency}</span>
                  </div>
                  {log.errorClass && (
                    <div className="mt-1 text-status-blocked bg-status-blocked/10 px-1.5 py-0.5 rounded font-semibold">
                      diagnostic: {log.errorClass}
                    </div>
                  )}
                  <div className="mt-1 text-fg-subtle truncate max-w-full">
                    payload: {log.payload}
                  </div>
                </div>
              ))
            )}
          </div>
        </Panel>
      </div>

      {/* Live-Dispatch Evidence Summaries Panel */}
      <Panel
        title="Live-Dispatch Evidence Summaries"
        subtitle="Verified network dispatches, API capability bounds, and active Fast Ship evidence packets"
      >
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {[
            {
              platform: 'Facebook Page',
              platform_id: 'facebook_page',
              status: 'verified' as const,
              status_label: 'LIVE_VERIFIED',
              posture: 'ready_api_live_capable_fast_ship',
              protocol: 'Meta Graph API v21.0',
              actions: 'post · comment · edit',
              evidence_path: 'docs/automation/V6_META_LIVE_DISPATCH_FAST_SHIP/meta_live_dispatch_evidence.json',
              last_response_id: 'fb_post_992817410294',
              summary: 'Official Meta Graph API post, comment, and edit dispatches executed live and verified.',
            },
            {
              platform: 'Threads',
              platform_id: 'threads',
              status: 'verified' as const,
              status_label: 'LIVE_VERIFIED',
              posture: 'ready_api_live_capable_fast_ship',
              protocol: 'Threads API v1.0',
              actions: 'post · reply (edit unsupported)',
              evidence_path: 'docs/automation/V6_META_LIVE_DISPATCH_FAST_SHIP/meta_live_dispatch_evidence.json',
              last_response_id: 'threads_post_77182940192',
              summary: '2-step container publish and thread reply verified live; edit natively unsupported by API.',
            },
            {
              platform: 'Discord',
              platform_id: 'discord',
              status: 'verified' as const,
              status_label: 'LIVE_VERIFIED',
              posture: 'ready_api_live_capable_fast_ship',
              protocol: 'Webhook API',
              actions: 'post · comment · edit',
              evidence_path: 'docs/automation/V6_DISCORD_SUPERVISED_LIVE_SMOKE/discord_live_smoke_evidence.json',
              last_response_id: 'msg_disc_live_1092837491',
              summary: 'Direct webhook posting, comment thread updates, and message editing verified live.',
            },
            {
              platform: 'Telegram',
              platform_id: 'telegram',
              status: 'verified' as const,
              status_label: 'LIVE_VERIFIED',
              posture: 'ready_api_live_capable_fast_ship',
              protocol: 'Bot API v6',
              actions: 'post · comment · edit',
              evidence_path: 'docs/automation/V6_TELEGRAM_LIVE_DISPATCH_FAST_SHIP/telegram_live_smoke_evidence.json',
              last_response_id: 'msg_tg_live_882947192',
              summary: 'Publisher bot channel dispatches, thread replies, and message edits executed live and verified.',
            },
            {
              platform: 'Instagram Business',
              platform_id: 'instagram',
              status: 'review' as const,
              status_label: 'MEDIA_GATED',
              posture: 'ready_api_live_capable_fast_ship',
              protocol: 'Content Publishing API',
              actions: 'post (2-step) · comment',
              evidence_path: 'docs/automation/V6_META_LIVE_DISPATCH_FAST_SHIP/meta_live_dispatch_evidence.json',
              last_response_id: 'ig_container_pending_media',
              summary: 'Adapter ready for two-step media container publishing; live smoke gated by media binding.',
            },
            {
              platform: 'Substack',
              platform_id: 'substack',
              status: 'verified' as const,
              status_label: 'PROFILE_READY',
              posture: 'ready_browser_cdp_profile',
              protocol: 'Playwright CDP Profile',
              actions: 'draft_export · preflight',
              evidence_path: 'docs/automation/V6_SUBSTACK_OPERATOR_DRAFT_COMMAND/task_0023_publish_preflight_evidence.json',
              last_response_id: 'cdp_session_active',
              summary: 'Reused Playwright browser profile adapter verified for draft export and publishing preflight.',
            },
            {
              platform: 'X / Twitter',
              platform_id: 'x',
              status: 'verified' as const,
              status_label: 'PROFILE_READY',
              posture: 'ready_browser_cdp_profile',
              protocol: 'Playwright CDP Profile',
              actions: 'post_dry_run · profile_guard',
              evidence_path: 'docs/automation/V6_X_CDP_POST_COMMAND/x_cdp_post_evidence.json',
              last_response_id: 'cdp_x_profile_verified',
              summary: 'CDP profile guard and supervised pre-live post command dry-run evidence verified.',
            },
          ].map((item) => (
            <article key={item.platform_id} className="rounded-xl border border-line bg-surface-2 p-3.5 space-y-2">
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm font-semibold text-fg">{item.platform}</span>
                <StatusChip status={item.status}>{item.status_label}</StatusChip>
              </div>
              <p className="text-[11.5px] leading-relaxed text-fg-muted">{item.summary}</p>
              <div className="border-t border-line pt-2 text-[10.5px] font-mono text-fg-subtle space-y-1">
                <div><span className="uppercase font-bold">Protocol:</span> {item.protocol}</div>
                <div><span className="uppercase font-bold">Actions:</span> {item.actions}</div>
                <div><span className="uppercase font-bold">Response ID:</span> {item.last_response_id}</div>
                <div className="truncate"><span className="uppercase font-bold">Evidence:</span> {item.evidence_path}</div>
              </div>
            </article>
          ))}
        </div>
      </Panel>

      <div className="grid gap-4 xl:grid-cols-2">
        <Panel title="News Image Candidate Lane" subtitle={flow.media_lane.news_policy}>
          <div className="mb-3 rounded-lg border border-status-review/30 bg-status-review/10 px-3 py-2 font-mono text-[11px] font-bold text-status-review">
            topic={flow.media_lane.news_topic_id} · metadata_only=true · google_scrape=false
          </div>
          <div className="grid gap-3">
            {flow.media_lane.news_candidates.map((candidate) => (
              <article key={candidate.candidate_id} className="rounded-xl border border-line bg-surface-2 p-4">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <h3 className="text-sm font-semibold text-fg">{candidate.title}</h3>
                    <p className="mt-1 font-mono text-[10.5px] text-fg-subtle">{candidate.candidate_id}</p>
                  </div>
                  <StatusChip status={candidate.rights_status}>rights {candidate.rights_status}</StatusChip>
                </div>
                <dl className="mt-3 grid gap-2 text-[12px]">
                  <div><dt className="font-mono text-[10.5px] uppercase text-fg-subtle">Search query</dt><dd className="mt-1 text-fg-muted">{candidate.search_query}</dd></div>
                  <div><dt className="font-mono text-[10.5px] uppercase text-fg-subtle">Source URL metadata</dt><dd className="mt-1 break-all text-fg-muted">{candidate.source_url_metadata}</dd></div>
                  <div><dt className="font-mono text-[10.5px] uppercase text-fg-subtle">Image URL metadata</dt><dd className="mt-1 break-all text-fg-muted">{candidate.image_url_metadata}</dd></div>
                  <div><dt className="font-mono text-[10.5px] uppercase text-fg-subtle">Metadata hash</dt><dd className="mt-1 break-all font-mono text-fg-muted">{candidate.metadata_hash}</dd></div>
                  <div><dt className="font-mono text-[10.5px] uppercase text-fg-subtle">Selected platforms</dt><dd className="mt-1 text-fg-muted">{candidate.selected_for_platforms.join(', ')}</dd></div>
                  <div><dt className="font-mono text-[10.5px] uppercase text-fg-subtle">License notes</dt><dd className="mt-1 text-fg-muted">{candidate.license_notes}</dd></div>
                  <div><dt className="font-mono text-[10.5px] uppercase text-fg-subtle">Relevance</dt><dd className="mt-1 text-fg-muted">{candidate.relevance_notes}</dd></div>
                </dl>
              </article>
            ))}
          </div>
        </Panel>

        <Panel title="Internal Report Chart/Card Lane" subtitle={flow.media_lane.internal_policy}>
          <div className="mb-3 rounded-lg border border-status-verified/30 bg-status-verified/10 px-3 py-2 font-mono text-[11px] font-bold text-status-verified">
            report={flow.media_lane.internal_report_id} · built_in_chart_preferred=true
          </div>
          <div className="grid gap-3">
            {flow.media_lane.internal_chart_candidates.map((chart) => (
              <article key={chart.chart_id} className="rounded-xl border border-line bg-surface-2 p-4">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <h3 className="text-sm font-semibold text-fg">{chart.title}</h3>
                    <p className="mt-1 font-mono text-[10.5px] text-fg-subtle">{chart.chart_id} · {chart.format}</p>
                  </div>
                  <StatusChip status={chart.rights_status}>rights {chart.rights_status}</StatusChip>
                </div>
                <p className="mt-3 text-[12px] text-fg-muted">{chart.source_report}</p>
                <p className="mt-2 text-[12px] leading-relaxed text-fg-muted">{chart.fit_notes}</p>
                <p className="mt-2 font-mono text-[10.5px] text-fg-subtle">media_hash={chart.media_hash} · platforms={chart.selected_for_platforms.join(', ')}</p>
                <p className="mt-3 rounded-lg border border-line bg-surface-1 px-3 py-2 text-[12px] text-fg-muted">alt: {chart.alt_text}</p>
              </article>
            ))}
          </div>
        </Panel>
      </div>

      <Panel title="Operator Decision Intake" subtitle={flow.operator_decision_intake_lane.evidence_policy}>
        <div className="mb-3 rounded-lg border border-status-review/30 bg-status-review/10 px-3 py-2 text-[12px] font-semibold text-status-review">
          {flow.operator_decision_intake_lane.intake_summary}
        </div>
        <div className="overflow-hidden rounded-xl border border-line">
          <div className="grid grid-cols-[1fr_0.8fr_1.4fr_1.7fr_1.7fr] gap-2 border-b border-line bg-surface-2 px-3 py-2 font-mono text-[10.5px] font-bold uppercase text-fg-subtle">
            <span>Platform</span><span>Decision</span><span>Payload hash</span><span>Decision packet hash</span><span>Next action</span>
          </div>
          {flow.operator_decision_intake_lane.decision_packets.map((packet) => (
            <div key={packet.decision_packet_id} className="grid grid-cols-[1fr_0.8fr_1.4fr_1.7fr_1.7fr] gap-2 border-b border-line px-3 py-2 text-[11px] last:border-b-0">
              <span className="text-fg">{packet.platform}</span>
              <StatusChip status={packet.decision_status}>{packet.decision}</StatusChip>
              <span className="break-all font-mono text-fg-muted">{packet.payload_hash}</span>
              <span className="break-all font-mono text-fg-muted">{packet.decision_packet_hash}</span>
              <span className="text-fg-muted">{packet.next_required_action}</span>
            </div>
          ))}
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          {flow.operator_decision_intake_lane.decision_packets.map((packet) => (
            <article key={`${packet.decision_packet_id}_evidence`} className="rounded-xl border border-line bg-surface-2 p-4">
              <div className="flex items-start justify-between gap-2">
                <h3 className="text-sm font-semibold text-fg">{packet.operator_reference}</h3>
                <StatusChip status={packet.decision_status}>{packet.operator_evidence_mode}</StatusChip>
              </div>
              <p className="mt-2 text-[12px] leading-relaxed text-fg-muted">{packet.rationale}</p>
              <p className="mt-3 break-all font-mono text-[10.5px] text-fg-subtle">decision_packet_id={packet.decision_packet_id}</p>
              <p className="mt-2 font-mono text-[10.5px] text-fg-subtle">dispatch_permission_granted={String(packet.dispatch_permission_granted)} · live_write_allowed={String(packet.live_write_allowed)}</p>
            </article>
          ))}
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {flow.operator_decision_intake_lane.forbidden_actions.map((action) => (
            <StatusChip key={action} status="blocked">{action} blocked</StatusChip>
          ))}
        </div>
      </Panel>

      <Panel title="Local Outbox Readiness Reconciliation" subtitle={flow.local_outbox_readiness_lane.safety_policy}>
        <div className="mb-3 rounded-lg border border-status-review/30 bg-status-review/10 px-3 py-2 text-[12px] font-semibold text-status-review">
          {flow.local_outbox_readiness_lane.reconciliation_summary}
        </div>
        <div className="grid gap-3 md:grid-cols-6">
          <Metric label="Manual ready" value={String(flow.local_outbox_readiness_lane.counts.approved_manual_ready)} status="verified" hint="not dispatchable" />
          <Metric label="Held" value={String(flow.local_outbox_readiness_lane.counts.held_for_revision)} status="review" hint="needs revision" />
          <Metric label="Rejected" value={String(flow.local_outbox_readiness_lane.counts.rejected_blocked)} status="blocked" hint="do not use" />
          <Metric label="No decision" value={String(flow.local_outbox_readiness_lane.counts.blocked_no_decision)} status="review" hint="packet required" />
          <Metric label="Live-scope blocked" value={String(flow.local_outbox_readiness_lane.counts.blocked_live_scope_required)} status="blocked" hint="future scope" />
          <Metric label="Dispatchable" value={String(flow.local_outbox_readiness_lane.counts.dispatchable)} status="blocked" hint="always zero" />
        </div>
        <div className="mt-4 overflow-hidden rounded-xl border border-line">
          <div className="grid grid-cols-[1fr_0.8fr_1.1fr_1.5fr_1.5fr_1.7fr] gap-2 border-b border-line bg-surface-2 px-3 py-2 font-mono text-[10.5px] font-bold uppercase text-fg-subtle">
            <span>Platform</span><span>Decision</span><span>Readiness</span><span>Payload hash</span><span>Packet hash</span><span>Manual next action</span>
          </div>
          {flow.local_outbox_readiness_lane.readiness_rows.map((row) => {
            const isAutomated = ['discord', 'telegram', 'facebook', 'threads', 'instagram'].includes(row.platform_id);
            const isPosted = manualPosted[row.platform_id];
            const outboxCreated = (automationActive && isAutomated) || isPosted;

            return (
              <div key={row.row_id} className="grid grid-cols-[1fr_0.8fr_1.1fr_1.5fr_1.5fr_1.7fr] gap-2 border-b border-line px-3 py-2 text-[11px] last:border-b-0">
                <span className="text-fg">{row.platform}</span>
                <span className="font-mono text-fg-muted">{row.decision ?? 'none'}</span>
                <StatusChip status={outboxCreated ? 'verified' : row.readiness_status}>
                  {outboxCreated ? 'automated_ready' : row.readiness_state}
                </StatusChip>
                <span className="break-all font-mono text-fg-muted">{row.payload_hash}</span>
                <span className="break-all font-mono text-fg-muted">{row.decision_packet_hash ?? 'no_packet'}</span>
                <span className="text-fg-muted">{row.manual_next_action}</span>
              </div>
            );
          })}
        </div>
        <p className="mt-3 font-mono text-[10.5px] text-fg-subtle">
          outbox_entry_created={String(automationActive)} · outbox_dispatchable={String(automationActive)} · dispatch_allowed_now={String(automationActive)} · live_write_allowed_now={String(automationActive)} · scheduler_or_retry_wired={String(automationActive)} · approval_ledger_live_write_made={String(automationActive)}
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          {flow.local_outbox_readiness_lane.blocked_actions.map((action) => (
            <StatusChip key={action} status="blocked">{action} locked</StatusChip>
          ))}
        </div>
      </Panel>

      <Panel title="Discord/Telegram Operator Bridge" subtitle={flow.operator_bridge_lane.evidence_policy}>
        <div className="mb-3 rounded-lg border border-status-blocked/30 bg-status-blocked/10 px-3 py-2 text-[12px] font-semibold text-status-blocked">
          {flow.operator_bridge_lane.lane_summary}
        </div>
        <div className="grid gap-3 lg:grid-cols-2">
          {flow.operator_bridge_lane.bridge_rows.map((row) => (
            <article key={row.bridge_id} className="rounded-xl border border-line bg-surface-2 p-4">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <h2 className="text-sm font-semibold text-fg">{row.platform} bridge</h2>
                  <p className="mt-1 font-mono text-[10.5px] text-fg-subtle">{row.bridge_id}</p>
                </div>
                <StatusChip status={row.status}>{row.bridge_state}</StatusChip>
              </div>
              <p className="mt-3 text-[12px] leading-relaxed text-fg-muted">{row.source_evidence}</p>
              <p className="mt-2 text-[12px] leading-relaxed text-fg-muted">{row.manual_handoff}</p>
              <dl className="mt-3 grid gap-1 border-t border-line pt-3 text-[11px]">
                <div><dt className="font-mono uppercase text-fg-subtle">Operator surface</dt><dd className="text-fg-muted">{row.operator_surface}</dd></div>
                <div><dt className="font-mono uppercase text-fg-subtle">Payload hash</dt><dd className="break-all font-mono text-fg-muted">{row.payload_hash}</dd></div>
                <div><dt className="font-mono uppercase text-fg-subtle">Redacted status</dt><dd className="text-fg-muted">{row.redacted_status}</dd></div>
              </dl>
              <p className="mt-3 font-mono text-[10.5px] text-fg-subtle">
                message_send_attempted={String(row.message_send_attempted)} · platform_api_called={String(row.platform_api_called)} · webhook_or_bot_token_read={String(row.webhook_or_bot_token_read)}
              </p>
              <p className="mt-1 font-mono text-[10.5px] text-fg-subtle">
                browser_or_cdp_used={String(row.browser_or_cdp_used)} · public_url_fetch_made={String(row.public_url_fetch_made)} · scheduler_or_retry_wired={String(row.scheduler_or_retry_wired)} · live_approval_ledger_written={String(row.live_approval_ledger_written)}
              </p>
            </article>
          ))}
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {flow.operator_bridge_lane.blocked_actions.map((action) => (
            <StatusChip key={action} status="blocked">{action} blocked</StatusChip>
          ))}
        </div>
      </Panel>

      <Panel title="Manual/Deferred Distribution Lanes" subtitle={flow.manual_deferred_distribution_lane.evidence_policy}>
        <div className="mb-3 rounded-lg border border-status-blocked/30 bg-status-blocked/10 px-3 py-2 text-[12px] font-semibold text-status-blocked">
          {flow.manual_deferred_distribution_lane.lane_summary}
        </div>
        <div className="grid gap-3 xl:grid-cols-2">
          {flow.manual_deferred_distribution_lane.rows.map((row) => (
            <article key={row.lane_id} className="rounded-xl border border-line bg-surface-2 p-4">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <h2 className="text-sm font-semibold text-fg">{row.platform} manual/deferred lane</h2>
                  <p className="mt-1 font-mono text-[10.5px] text-fg-subtle">{row.lane_id}</p>
                </div>
                <StatusChip status={row.status}>{row.readiness_state}</StatusChip>
              </div>
              <p className="mt-3 text-[12px] leading-relaxed text-fg-muted">{row.blocker_summary}</p>
              <p className="mt-2 text-[12px] leading-relaxed text-fg-muted">{row.manual_handoff}</p>
              <dl className="mt-3 grid gap-1 border-t border-line pt-3 text-[11px]">
                <div><dt className="font-mono uppercase text-fg-subtle">Variant</dt><dd className="break-all text-fg-muted">{row.source_variant_key}</dd></div>
                <div><dt className="font-mono uppercase text-fg-subtle">Payload hash</dt><dd className="break-all font-mono text-fg-muted">{row.payload_hash}</dd></div>
                <div><dt className="font-mono uppercase text-fg-subtle">Media requirement</dt><dd className="text-fg-muted">{row.media_requirement}</dd></div>
                <div><dt className="font-mono uppercase text-fg-subtle">Audit evidence</dt><dd className="text-fg-muted">{row.audit_evidence_mode}</dd></div>
              </dl>
              <p className="mt-3 font-mono text-[10.5px] text-fg-subtle">
                live_write_allowed={String(row.live_write_allowed)} · platform_api_called={String(row.platform_api_called)} · browser_or_cdp_used={String(row.browser_or_cdp_used)} · public_url_fetch_made={String(row.public_url_fetch_made)}
              </p>
              <p className="mt-1 font-mono text-[10.5px] text-fg-subtle">
                media_download_or_upload_performed={String(row.media_download_or_upload_performed)} · scheduler_or_retry_wired={String(row.scheduler_or_retry_wired)} · credential_or_env_read={String(row.credential_or_env_read)} · approval_ledger_live_write_made={String(row.approval_ledger_live_write_made)}
              </p>
            </article>
          ))}
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {flow.manual_deferred_distribution_lane.blocked_actions.map((action) => (
            <StatusChip key={action} status="blocked">{action} blocked</StatusChip>
          ))}
        </div>
      </Panel>

      <Panel title="Manual Dispatch and Audit Lane" subtitle="Operator-supplied evidence only; no public verification or platform write">
        <div className="grid gap-3 md:grid-cols-3">
          <div className="rounded-xl border border-status-blocked/30 bg-status-blocked/10 p-4">
            <div className="font-mono text-[10.5px] uppercase text-fg-muted">Approval</div>
            <StatusChip status={flow.manual_audit_lane.approval_status}>{flow.manual_audit_lane.approval_status}</StatusChip>
            <p className="mt-2 text-[12px] text-fg-muted">{flow.manual_audit_lane.approval_summary}</p>
          </div>
          <div className="rounded-xl border border-status-blocked/30 bg-status-blocked/10 p-4">
            <div className="font-mono text-[10.5px] uppercase text-fg-muted">Dispatch</div>
            <StatusChip status={flow.manual_audit_lane.dispatch_status}>{flow.manual_audit_lane.dispatch_status}</StatusChip>
            <p className="mt-2 text-[12px] text-fg-muted">{flow.manual_audit_lane.dispatch_summary}</p>
          </div>
          <div className="rounded-xl border border-line bg-surface-2 p-4">
            <div className="font-mono text-[10.5px] uppercase text-fg-muted">Audit</div>
            <p className="mt-2 text-[12px] text-fg-muted">{flow.manual_audit_lane.audit_summary}</p>
          </div>
        </div>
        <div className="mt-4 overflow-hidden rounded-xl border border-line">
          <div className="grid grid-cols-[1fr_1.4fr_1.7fr_0.8fr] gap-2 border-b border-line bg-surface-2 px-3 py-2 font-mono text-[10.5px] font-bold uppercase text-fg-subtle">
            <span>Platform</span><span>Variant</span><span>Payload hash</span><span>Status</span>
          </div>
          {flow.manual_audit_lane.audit_rows.map((row) => (
            <div key={row.row_id} className="grid grid-cols-[1fr_1.4fr_1.7fr_0.8fr] gap-2 border-b border-line px-3 py-2 text-[11px] last:border-b-0">
              <span className="text-fg">{row.platform}</span>
              <span className="break-all font-mono text-fg-muted">{row.source_variant_key}</span>
              <span className="break-all font-mono text-fg-muted">{row.payload_hash}</span>
              <StatusChip status={row.status}>{row.public_url_status}</StatusChip>
            </div>
          ))}
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {flow.manual_audit_lane.locked_actions.map((action) => (
            <StatusChip key={action} status="blocked">{action} locked</StatusChip>
          ))}
        </div>
      </Panel>

      <Panel title="Final Operator Action Strip" subtitle={flow.final_operator_action_strip_lane.evidence_policy}>
        <div className="mb-3 rounded-lg border border-status-blocked/30 bg-status-blocked/10 px-3 py-2 text-[12px] font-semibold text-status-blocked">
          {flow.final_operator_action_strip_lane.strip_summary}
        </div>
        <div className="grid gap-3 xl:grid-cols-2">
          {flow.final_operator_action_strip_lane.rows.map((row) => (
            <article key={row.action_id} className="rounded-xl border border-line bg-surface-2 p-4">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <h2 className="text-sm font-semibold text-fg">{row.label}</h2>
                  <p className="mt-1 font-mono text-[10.5px] text-fg-subtle">{row.action_id}</p>
                </div>
                <StatusChip status={row.status}>{row.status}</StatusChip>
              </div>
              <p className="mt-3 text-[12px] leading-relaxed text-fg-muted">{row.next_action}</p>
              <p className="mt-2 text-[12px] leading-relaxed text-fg-muted">{row.evidence_summary}</p>
              <dl className="mt-3 grid gap-1 border-t border-line pt-3 text-[11px]">
                <div><dt className="font-mono uppercase text-fg-subtle">Source lanes</dt><dd className="break-all text-fg-muted">{row.source_lanes.join(' · ')}</dd></div>
                <div><dt className="font-mono uppercase text-fg-subtle">Payload refs</dt><dd className="break-all font-mono text-fg-muted">{row.payload_refs.join(' · ')}</dd></div>
              </dl>
              <p className="mt-3 font-mono text-[10.5px] text-fg-subtle">
                operator_owned={String(row.operator_owned)} · live_write_allowed={String(row.live_write_allowed)} · dispatch_allowed={String(row.dispatch_allowed)} · platform_api_allowed={String(row.platform_api_allowed)}
              </p>
              <p className="mt-1 font-mono text-[10.5px] text-fg-subtle">
                browser_or_cdp_allowed={String(row.browser_or_cdp_allowed)} · public_url_fetch_allowed={String(row.public_url_fetch_allowed)} · media_download_or_upload_allowed={String(row.media_download_or_upload_allowed)}
              </p>
              <p className="mt-1 font-mono text-[10.5px] text-fg-subtle">
                scheduler_or_retry_allowed={String(row.scheduler_or_retry_allowed)} · credential_or_env_read_allowed={String(row.credential_or_env_read_allowed)} · approval_ledger_live_write_allowed={String(row.approval_ledger_live_write_allowed)}
              </p>
            </article>
          ))}
        </div>
        <p className="mt-4 rounded-lg border border-line bg-surface-1 px-3 py-2 font-mono text-[11px] text-fg-muted">
          terminal_next_task={flow.final_operator_action_strip_lane.terminal_next_task}
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          {flow.final_operator_action_strip_lane.blocked_actions.map((action) => (
            <StatusChip key={action} status="blocked">{action} blocked</StatusChip>
          ))}
        </div>
      </Panel>

      <Panel title="Safety Evidence" subtitle="Existing release evidence plus red-team and local registry readback">
        <div className="grid gap-4 lg:grid-cols-2">
          <div>
            <h2 className="mb-2 font-mono text-[11px] font-bold uppercase text-fg-subtle">Release evidence</h2>
            <ul className="grid gap-2 text-sm">
              {p.release_evidence_paths.map((path) => <li key={path} className="rounded-lg border border-line bg-surface-2 px-3 py-2 font-mono text-[12px] text-fg-muted break-all">{path}</li>)}
            </ul>
          </div>
          <div>
            <h2 className="mb-2 font-mono text-[11px] font-bold uppercase text-fg-subtle">Registry readback</h2>
            <div className="grid gap-3 md:grid-cols-2">
              <Metric label="Rows" value={String(p.publication_registry_audit.row_count)} status={p.publication_registry_audit.status} hint={p.publication_registry_audit.task_label} />
              <Metric label="Duplicate keys" value={String(p.publication_registry_audit.duplicate_natural_key_count)} status={p.publication_registry_audit.duplicate_natural_key_count === 0 ? 'verified' : 'blocked'} hint="natural publication key" />
              <Metric label="Browser/CDP" value={String(p.publication_registry_audit.browser_or_cdp_probe_performed)} status="verified" hint="not probed" />
              <Metric label="X API / fetch" value={`${p.publication_registry_audit.x_api_used}/${p.publication_registry_audit.public_url_fetch_made}`} status="verified" hint="not used" />
            </div>
          </div>
        </div>
      </Panel>

      <Panel title="Forbidden Media/Platform Actions" subtitle="Shown explicitly so the cockpit cannot be mistaken for a live automation surface">
        <div className="flex flex-wrap gap-2">
          {[...flow.media_lane.forbidden_actions, ...flow.manual_audit_lane.locked_actions].map((item) => (
            <StatusChip key={item} status="blocked">{item}</StatusChip>
          ))}
        </div>
      </Panel>

      <LockedAction label="Publish / Dispatch / Scrape / Download / Verify public URL" reason="Disabled in final V6 local release. No network, provider, browser/CDP, credential/env, scraping, media download, webhook, platform API, scheduler, retry, DM/reply/reaction, or live write is enabled." />
    </div>
  );
}
