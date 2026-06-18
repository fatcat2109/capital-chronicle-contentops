// Capital Chronicle ContentOps V5 — Command Center view.
// Local-first overview. No network, no storage, no credentials.

import { useApp } from '../state';
import { viewModel } from '../fixtures';
import {
  Metric,
  Panel,
  SectionLabel,
  StatusChip,
  StatusDot,
} from '../ui/primitives';
import { selectBlocker, selectSystemVerdict } from '../selectors';
import { IconChevronRight } from '../ui/icons';

export function CommandCenter() {
  const { select, selected, setView } = useApp();
  const s = viewModel.system_state;
  const topBlocker =
    s.blockers.find((b) => b.severity === 'blocked') ?? s.blockers[0];
  const verdictActive = selected?.kind === 'system_verdict';
  const topBlockerActive =
    selected?.kind === 'blocker' && selected.id === topBlocker.id;

  return (
    <div className="space-y-8">
      <header>
        <div className="flex items-center gap-2 font-mono text-[11px] font-bold uppercase tracking-[0.14em] text-fg-subtle">
          <StatusDot status="blocked" />
          Cockpit read model · local static contract
        </div>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight text-fg">
          Command Center
        </h1>
        <p className="mt-1 max-w-3xl text-sm leading-relaxed text-fg-muted">
          V5 cockpit is bound to the current local read model. It shows reviewable work,
          manual export, platform previews, blocked live dispatch, payload hashes,
          evidence index, and the next safe operator action. No live posting, no
          scheduler, no platform/provider API, and no credential hydration.
        </p>
      </header>

      {/* Cockpit spine — readiness, next action, and hard live-dispatch blocker. */}
      <section className="grid grid-cols-1 gap-4 lg:grid-cols-5">
        <button
          type="button"
          id="verdict-spine"
          onClick={() => select(selectSystemVerdict(s))}
          className={`group flex flex-col rounded-xl border bg-surface-1 p-5 text-left shadow-card transition-colors hover:border-line-strong lg:col-span-3 ${
            verdictActive ? 'border-accent/50 ring-1 ring-accent/20' : 'border-line'
          }`}
        >
          <div className="flex flex-wrap items-center gap-3">
            <span className="flex h-10 w-1.5 shrink-0 rounded-full bg-status-blocked" />
            <StatusChip status={s.verdict_status} icon>
              {s.verdict}
            </StatusChip>
            <span className="font-mono text-[11px] text-fg-subtle">
              {viewModel.cockpit.current_gate}
            </span>
          </div>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <div className="rounded-lg border border-line bg-surface-2 p-3">
              <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle">
                Next safe operator action
              </div>
              <p className="mt-1 text-sm font-medium text-fg">
                {s.next_allowed_action}
              </p>
            </div>
            <div className="rounded-lg border border-line bg-surface-2 p-3">
              <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle">
                Accepted baseline
              </div>
              <p className="mt-1 break-all font-mono text-[12px] font-medium text-fg">
                {viewModel.cockpit.accepted_baseline}
              </p>
            </div>
          </div>
          <div className="mt-3 flex flex-wrap gap-1.5">
            {viewModel.cockpit.safety_modes.map((mode) => (
              <span key={mode} className="rounded-md border border-line bg-surface-2 px-1.5 py-0.5 font-mono text-[10.5px] text-fg-muted">
                {mode}
              </span>
            ))}
          </div>
          <span className="mt-3 flex items-center gap-1 font-mono text-[11px] text-fg-subtle group-hover:text-fg-muted">
            Inspect verdict
            <IconChevronRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
          </span>
        </button>

        <button
          type="button"
          id="top-blocker-spine"
          onClick={() => select(selectBlocker(topBlocker))}
          className={`group flex flex-col rounded-xl border p-5 text-left shadow-card transition-colors hover:border-line-strong lg:col-span-2 ${
            topBlockerActive
              ? 'border-accent/50 ring-1 ring-accent/20'
              : 'border-status-blocked/30'
          } bg-status-blocked/5`}
        >
          <div className="flex items-center justify-between gap-2">
            <span className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-status-blocked">
              Blocked live dispatch
            </span>
            <StatusChip status="blocked">
              {viewModel.cockpit.blocked_live_dispatch_queue.length} gates
            </StatusChip>
          </div>
          <p className="mt-3 text-sm font-semibold leading-snug text-fg">
            {topBlocker.label}
          </p>
          <p className="mt-1 text-[12px] leading-relaxed text-fg-muted">
            {topBlocker.detail}
          </p>
          <p className="mt-3 font-mono text-[10.5px] text-status-blocked">
            can_dispatch: false · public_postable: false
          </p>
          <span className="mt-auto flex items-center gap-1 pt-3 font-mono text-[11px] text-fg-subtle group-hover:text-fg-muted">
            Inspect blocker
            <IconChevronRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
          </span>
        </button>
      </section>

      {/* Pipeline health — cockpit queue counts, not a standalone board. */}
      <section>
        <SectionLabel>Cockpit queues</SectionLabel>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {s.queue_summary.map((m) => (
            <Metric
              key={m.label}
              label={m.label}
              value={String(m.count)}
              status={m.status}
            />
          ))}
        </div>
      </section>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Active blockers */}
        <Panel
          title="Active blockers"
          subtitle="Hard gates holding back progression"
          className="lg:col-span-2"
          actions={
            <StatusChip status="blocked">
              {s.blockers.filter((b) => b.severity === 'blocked').length} hard
            </StatusChip>
          }
          bodyClassName="p-3"
        >
          <ul className="space-y-2">
            {s.blockers.map((b) => {
              const active =
                selected?.kind === 'blocker' && selected.id === b.id;
              return (
                <li key={b.id}>
                  <button
                    type="button"
                    id={`blocker-${b.id}`}
                    onClick={() => select(selectBlocker(b))}
                    className={`flex w-full items-start gap-3 rounded-lg border bg-surface-2 px-3 py-2.5 text-left transition-colors hover:bg-surface-3 ${
                      active ? 'border-accent/50' : 'border-line'
                    }`}
                  >
                    <span className="mt-1.5">
                      <StatusDot status={b.severity} />
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="flex items-center justify-between gap-2">
                        <span className="text-sm font-medium text-fg">
                          {b.label}
                        </span>
                        <StatusChip status={b.severity}>{b.id}</StatusChip>
                      </span>
                      <span className="mt-0.5 block text-xs leading-relaxed text-fg-muted">
                        {b.detail}
                      </span>
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        </Panel>

        {/* Queue summary */}
        <Panel title="Queue summary" subtitle="Editorial objects by state">
          <ul className="space-y-2.5">
            {s.queue_summary.map((q) => (
              <li
                key={q.label}
                className="flex items-center justify-between gap-3 text-sm"
              >
                <span className="flex items-center gap-2 text-fg-muted">
                  <StatusDot status={q.status} />
                  {q.label}
                </span>
                <span className="font-mono text-base font-semibold text-fg">
                  {q.count}
                </span>
              </li>
            ))}
          </ul>
          <button
            type="button"
            id="goto-inventory"
            onClick={() => setView('content_inventory')}
            className="mt-4 flex w-full items-center justify-center gap-1.5 rounded-md border border-line bg-surface-2 px-3 py-2 text-xs font-semibold text-fg-muted transition-colors hover:border-line-strong hover:text-fg"
          >
            Open Content Inventory
            <IconChevronRight className="h-3.5 w-3.5" />
          </button>
        </Panel>
      </div>

      {/* Validation passes */}
      <Panel
        title="Validation passes"
        subtitle="Static + behavioral safety checks"
        bodyClassName="p-3"
      >
        <ul className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          {s.validation_passes.map((v) => (
            <li
              key={v.id}
              className="flex items-start justify-between gap-3 rounded-lg border border-line bg-surface-2 px-3 py-2.5"
            >
              <span className="min-w-0">
                <span className="text-sm font-medium text-fg">{v.label}</span>
                <span className="mt-0.5 block text-xs leading-relaxed text-fg-muted">
                  {v.detail}
                </span>
              </span>
              <StatusChip status={v.status} icon>
                {v.status}
              </StatusChip>
            </li>
          ))}
        </ul>
      </Panel>
    </div>
  );
}
