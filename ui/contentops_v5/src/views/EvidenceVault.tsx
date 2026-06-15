// Capital Chronicle ContentOps V5 — Evidence Vault view (dark evidence mode).
// Forensic / compliance-room surface. No network, no storage, no credentials.

import { useApp } from '../state';
import { viewModel } from '../fixtures';
import { Panel, StatusChip } from '../ui/primitives';

export function EvidenceVault() {
  const { select } = useApp();
  const ev = viewModel.evidence_packets[0];
  const audit = viewModel.audit_events;
  const policy = viewModel.policy_boundaries;

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-fg">
            Evidence Vault
          </h1>
          <p className="mt-1 text-sm text-fg-muted">
            Dark evidence mode. Validation matrix, task evidence packets,
            commit timeline, forbidden-scope matrix, and secret scan.
          </p>
        </div>
        <StatusChip status={ev.result}>{ev.result_label}</StatusChip>
      </header>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Panel title="Validation matrix" className="lg:col-span-2">
          <ul className="space-y-2">
            {ev.validation_matrix.map((v) => (
              <li
                key={v.id}
                className="flex items-start justify-between gap-3 rounded-md border border-line bg-surface-2 px-3 py-2"
              >
                <span>
                  <span className="text-sm font-medium text-fg">{v.label}</span>
                  <span className="mt-0.5 block font-mono text-[11px] text-fg-muted">
                    {v.detail}
                  </span>
                </span>
                <StatusChip status={v.status}>{v.status}</StatusChip>
              </li>
            ))}
          </ul>
        </Panel>

        <Panel title="Secret scan">
          <div className="rounded-md border border-status-verified/40 bg-status-verified/10 p-3">
            <StatusChip status={ev.secret_scan.status}>
              {ev.secret_scan.label}
            </StatusChip>
            <p className="mt-2 font-mono text-[11px] text-fg">
              {ev.secret_scan.detail}
            </p>
          </div>
          <div className="mt-3 flex flex-wrap gap-1">
            {ev.provenance_chips.map((c) => (
              <span
                key={c}
                className="rounded border border-line bg-surface-2 px-1.5 py-0.5 font-mono text-[11px] text-fg-muted"
              >
                {c}
              </span>
            ))}
          </div>
        </Panel>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Panel
          title="Task evidence packet"
          actions={
            <button
              type="button"
              id="evidence-inspect"
              onClick={() =>
                select({
                  kind: 'evidence_packet',
                  id: ev.id,
                  title: ev.task_label,
                  fields: [
                    { label: 'Result', value: ev.result_label, status: ev.result },
                    { label: 'Commit', value: ev.commit_ref, mono: true },
                    { label: 'Timestamp', value: ev.timestamp, mono: true },
                    ...ev.source_lineage.map((l) => ({
                      label: 'Lineage',
                      value: l.label,
                    })),
                  ],
                })
              }
              className="rounded border border-line bg-surface-2 px-2 py-1 font-mono text-[11px] text-fg-muted hover:bg-surface-3"
            >
              inspect
            </button>
          }
        >
          <div className="font-mono text-[12px] text-fg">{ev.id}</div>
          <p className="mt-1 break-all font-mono text-[11px] text-fg-muted">
            {ev.task_label}
          </p>
          <dl className="mt-3 space-y-2 text-sm">
            <div className="flex items-center justify-between">
              <dt className="font-mono text-[11px] uppercase text-fg-muted">
                Commit
              </dt>
              <dd className="font-mono text-[12px] text-fg">{ev.commit_ref}</dd>
            </div>
            <div className="flex items-center justify-between">
              <dt className="font-mono text-[11px] uppercase text-fg-muted">
                Timestamp
              </dt>
              <dd className="font-mono text-[12px] text-fg">{ev.timestamp}</dd>
            </div>
          </dl>
        </Panel>

        <Panel title="Forbidden-scope matrix">
          <ul className="space-y-2">
            {ev.forbidden_scope.map((f) => (
              <li
                key={f.id}
                className="flex items-center justify-between text-sm"
              >
                <span className="text-fg-muted">{f.label}</span>
                <StatusChip status={f.status}>excluded</StatusChip>
              </li>
            ))}
          </ul>
        </Panel>

        <Panel title="Commit timeline">
          <ol className="space-y-3">
            {audit.map((a) => (
              <li key={a.id} className="border-l border-line pl-3">
                <div className="font-mono text-[11px] text-fg-muted">
                  {a.timestamp}
                </div>
                <div className="text-sm text-fg">{a.action}</div>
                <div className="font-mono text-[11px] text-fg-muted">
                  {a.actor} · {a.ref}
                </div>
              </li>
            ))}
          </ol>
        </Panel>
      </div>

      <Panel title="Policy boundaries">
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {policy.map((p) => (
            <div
              key={p.id}
              className="flex items-start justify-between gap-3 rounded-md border border-line bg-surface-2 px-3 py-2"
            >
              <span>
                <span className="text-sm font-medium text-fg">{p.label}</span>
                <span className="mt-0.5 block font-mono text-[11px] text-fg-muted">
                  {p.detail}
                </span>
              </span>
              <StatusChip status={p.status}>{p.status}</StatusChip>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}
