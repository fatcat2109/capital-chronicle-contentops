// Capital Chronicle ContentOps V5 — Evidence Vault view.
// Forensic / compliance mode. Always rendered in dark-evidence theme (App
// forces it). Read-only audit surface. No network, storage, or credentials.

import { useApp } from '../state';
import { viewModel } from '../fixtures';
import { IconClock, IconFingerprint } from '../ui/icons';
import {
  EvidenceChip,
  Panel,
  SectionLabel,
  StatusChip,
  StatusDot,
} from '../ui/primitives';

export function EvidenceVault() {
  const { select, selected } = useApp();
  const packet = viewModel.evidence_packets[0];

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 font-mono text-[11px] font-bold uppercase tracking-[0.14em] text-fg-subtle">
            <IconFingerprint className="h-4 w-4 text-accent" />
            Forensic mode
          </div>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight text-fg">
            Evidence Vault
          </h1>
          <div className="mt-1 break-all font-mono text-[12px] text-fg-muted">
            {packet.task_label}
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <StatusChip status={packet.result} icon>
              {packet.result_label}
            </StatusChip>
            <EvidenceChip>{packet.commit_ref}</EvidenceChip>
            <span className="flex items-center gap-1 font-mono text-[11px] text-fg-subtle">
              <IconClock className="h-3.5 w-3.5" />
              {packet.timestamp}
            </span>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <div className="space-y-6 xl:col-span-2">
          <Panel title="Validation matrix" subtitle="Each check is part of the evidence record">
            <ul className="divide-y divide-line">
              {packet.validation_matrix.map((v) => {
                const active =
                  selected?.kind === 'validation' && selected.id === v.id;
                return (
                  <li key={v.id}>
                    <button
                      type="button"
                      id={`vm-${v.id}`}
                      onClick={() =>
                        select({
                          kind: 'validation',
                          id: v.id,
                          title: v.label,
                          fields: [
                            { label: 'Status', value: v.status, status: v.status },
                            { label: 'Detail', value: v.detail },
                            { label: 'Packet', value: packet.id, mono: true },
                          ],
                        })
                      }
                      className={`flex w-full items-center justify-between gap-3 px-1 py-2.5 text-left transition-colors ${
                        active ? 'bg-accent/5' : 'hover:bg-surface-2'
                      }`}
                    >
                      <span className="flex items-center gap-2.5">
                        <StatusDot status={v.status} />
                        <span className="text-sm text-fg">{v.label}</span>
                      </span>
                      <span className="flex items-center gap-3">
                        <span className="hidden font-mono text-[11px] text-fg-subtle sm:inline">
                          {v.detail}
                        </span>
                        <StatusChip status={v.status}>{v.status}</StatusChip>
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          </Panel>

          <Panel title="Forbidden scope — proven absent" subtitle="Static guarantees enforced for V5">
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              {packet.forbidden_scope.map((f) => (
                <div
                  key={f.id}
                  className="flex items-center justify-between gap-2 rounded-lg border border-line bg-surface-2 px-3 py-2"
                >
                  <span className="text-[12px] text-fg-muted">{f.label}</span>
                  <StatusChip status={f.status} icon>
                    clean
                  </StatusChip>
                </div>
              ))}
            </div>
          </Panel>
        </div>

        <div className="space-y-6">
          <Panel
            title={
              <span className="flex items-center gap-2">
                <IconFingerprint className="h-4 w-4 text-accent" />
                Secret scan
              </span>
            }
          >
            <div className="flex items-center justify-between gap-2">
              <span className="flex items-center gap-2 text-sm text-fg-muted">
                <StatusDot status={packet.secret_scan.status} />
                {packet.secret_scan.label}
              </span>
              <StatusChip status={packet.secret_scan.status} icon>
                {packet.secret_scan.status}
              </StatusChip>
            </div>
            <p className="mt-2 font-mono text-[11px] leading-relaxed text-fg-subtle">
              {packet.secret_scan.detail}
            </p>
          </Panel>

          <Panel title="Provenance">
            <div className="flex flex-wrap gap-1.5">
              {packet.provenance_chips.map((c) => (
                <EvidenceChip key={c}>{c}</EvidenceChip>
              ))}
            </div>
            <div className="mt-4 border-t border-line pt-3">
              <SectionLabel>Source lineage</SectionLabel>
              <ul className="space-y-2">
                {packet.source_lineage.map((l) => (
                  <li
                    key={l.id}
                    className="flex items-center gap-2.5 rounded-lg border border-line bg-surface-2 px-3 py-2"
                  >
                    <span className="font-mono text-[10.5px] text-fg-subtle">
                      {l.id}
                    </span>
                    <span className="text-[12px] text-fg-muted">{l.label}</span>
                  </li>
                ))}
              </ul>
            </div>
          </Panel>

          <Panel title="Audit trail">
            <ul className="space-y-3">
              {viewModel.audit_events.map((e) => (
                <li key={e.id} className="relative pl-4">
                  <span className="absolute left-0 top-1.5 h-2 w-2 rounded-full bg-accent" />
                  <div className="text-[12px] text-fg">{e.action}</div>
                  <div className="mt-0.5 font-mono text-[10.5px] text-fg-subtle">
                    {e.actor} · {e.ref} · {e.timestamp}
                  </div>
                </li>
              ))}
            </ul>
          </Panel>
        </div>
      </div>
    </div>
  );
}
