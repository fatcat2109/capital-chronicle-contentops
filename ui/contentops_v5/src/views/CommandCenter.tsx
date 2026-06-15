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
import { IconChevronRight } from '../ui/icons';

export function CommandCenter() {
  const { select, selected, setView } = useApp();
  const s = viewModel.system_state;

  return (
    <div className="space-y-8">
      <header>
        <div className="flex items-center gap-2 font-mono text-[11px] font-bold uppercase tracking-[0.14em] text-fg-subtle">
          <StatusDot status="verified" />
          Editorial operations
        </div>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight text-fg">
          Command Center
        </h1>
        <p className="mt-1 max-w-2xl text-sm leading-relaxed text-fg-muted">
          Local-first, review-only control surface. No live posting, no
          scheduler, no provider or platform API. Every action below is a
          supervised, manual step.
        </p>
      </header>

      {/* Verdict spine */}
      <button
        type="button"
        id="verdict-spine"
        onClick={() =>
          select({
            kind: 'system_verdict',
            id: s.baseline_ref,
            title: s.verdict,
            fields: [
              { label: 'Status', value: s.verdict, status: s.verdict_status },
              { label: 'Baseline', value: s.baseline_ref, mono: true },
              { label: 'Provenance', value: s.build_provenance, mono: true },
              { label: 'Next', value: s.next_allowed_action },
            ],
          })
        }
        className={`group flex w-full items-center gap-4 rounded-xl border bg-surface-1 p-4 text-left shadow-card transition-colors hover:border-line-strong ${
          selected?.kind === 'system_verdict'
            ? 'border-accent/50'
            : 'border-line'
        }`}
      >
        <span className="flex h-12 w-1.5 shrink-0 rounded-full bg-status-verified" />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <StatusChip status={s.verdict_status} icon>
              {s.verdict}
            </StatusChip>
            <span className="font-mono text-[11px] text-fg-subtle">
              {s.baseline_ref}
            </span>
          </div>
          <p className="mt-1.5 text-sm text-fg">
            <span className="text-fg-muted">Next allowed action — </span>
            <span className="font-medium">{s.next_allowed_action}</span>
          </p>
        </div>
        <IconChevronRight className="h-4 w-4 shrink-0 text-fg-subtle transition-transform group-hover:translate-x-0.5" />
      </button>

      {/* Pipeline health */}
      <section>
        <SectionLabel>Pipeline health</SectionLabel>
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {s.pipeline_health.map((m) => (
            <Metric
              key={m.label}
              label={m.label}
              value={m.value}
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
                    onClick={() =>
                      select({
                        kind: 'blocker',
                        id: b.id,
                        title: b.label,
                        fields: [
                          { label: 'Severity', value: b.severity, status: b.severity },
                          { label: 'ID', value: b.id, mono: true },
                          { label: 'Detail', value: b.detail },
                        ],
                      })
                    }
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
