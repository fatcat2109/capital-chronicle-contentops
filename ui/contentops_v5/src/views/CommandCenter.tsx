// Capital Chronicle ContentOps V5 — Command Center view.
// Local-first overview. No network, no storage, no credentials.

import { useApp } from '../state';
import { viewModel } from '../fixtures';
import { Metric, Panel, StatusChip } from '../ui/primitives';

export function CommandCenter() {
  const { select } = useApp();
  const s = viewModel.system_state;

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-fg">
          Command Center
        </h1>
        <p className="mt-1 text-sm text-fg-muted">
          Local-first editorial operations. Review-only. No live posting,
          no scheduler, no provider/platform API.
        </p>
      </header>

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

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Panel title="System verdict" className="lg:col-span-2">
          <div className="flex flex-wrap items-center gap-3">
            <StatusChip status={s.verdict_status}>{s.verdict}</StatusChip>
            <span className="font-mono text-[12px] text-fg-muted">
              {s.baseline_ref}
            </span>
          </div>
          <p className="mt-3 text-sm text-fg">
            Next allowed action:{' '}
            <span className="font-medium">{s.next_allowed_action}</span>
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            {s.modes.map((m) => (
              <span
                key={m.code}
                className="rounded border border-line bg-surface-2 px-1.5 py-0.5 font-mono text-[11px] text-fg-muted"
              >
                {m.code}
              </span>
            ))}
          </div>
        </Panel>

        <Panel title="Queue summary">
          <ul className="space-y-2">
            {s.queue_summary.map((q) => (
              <li
                key={q.label}
                className="flex items-center justify-between text-sm"
              >
                <span className="text-fg-muted">{q.label}</span>
                <StatusChip status={q.status}>{q.count}</StatusChip>
              </li>
            ))}
          </ul>
        </Panel>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Panel title="Active blockers">
          <ul className="space-y-2">
            {s.blockers.map((b) => (
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
                        { label: 'Severity', value: b.severity, mono: true },
                        { label: 'Detail', value: b.detail },
                      ],
                    })
                  }
                  className="flex w-full items-start justify-between gap-3 rounded-md border border-line bg-surface-2 px-3 py-2 text-left hover:bg-surface-3"
                >
                  <span>
                    <span className="text-sm font-medium text-fg">
                      {b.label}
                    </span>
                    <span className="mt-0.5 block text-xs text-fg-muted">
                      {b.detail}
                    </span>
                  </span>
                  <StatusChip status={b.severity}>{b.id}</StatusChip>
                </button>
              </li>
            ))}
          </ul>
        </Panel>

        <Panel title="Validation passes">
          <ul className="space-y-2">
            {s.validation_passes.map((v) => (
              <li
                key={v.id}
                className="flex items-start justify-between gap-3 rounded-md border border-line bg-surface-2 px-3 py-2"
              >
                <span>
                  <span className="text-sm font-medium text-fg">
                    {v.label}
                  </span>
                  <span className="mt-0.5 block text-xs text-fg-muted">
                    {v.detail}
                  </span>
                </span>
                <StatusChip status={v.status}>{v.status}</StatusChip>
              </li>
            ))}
          </ul>
        </Panel>
      </div>
    </div>
  );
}
