// Capital Chronicle ContentOps V5 — Approval Queue + Dispatch Control view.
// Dispatch is visibly future-gated and DISABLED. No live publish/post/
// schedule/API affordance. No network, no storage, no credentials.

import { useApp } from '../state';
import { viewModel } from '../fixtures';
import {
  LockedAction,
  Panel,
  SectionLabel,
  StatusChip,
  StatusDot,
} from '../ui/primitives';

export function ApprovalQueue() {
  const { select, selected } = useApp();
  const packet = viewModel.approval_packets[0];
  const clearedCount = packet.gates.filter((g) => g.cleared).length;

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="font-mono text-[11px] font-bold uppercase tracking-[0.14em] text-fg-subtle">
            Approval &amp; Dispatch Control
          </div>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight text-fg">
            Manual approval, future-gated dispatch
          </h1>
          <p className="mt-1 max-w-2xl text-sm leading-relaxed text-fg-muted">
            Manual approval packets and a future-gated dispatch hierarchy. No
            live posting, scheduling, or platform/provider API exists.
          </p>
        </div>
        <StatusChip status="blocked" icon>
          Dispatch disabled
        </StatusChip>
      </header>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Panel
          title={`Approval packet · ${packet.id}`}
          subtitle={packet.title}
          actions={
            <StatusChip status={packet.approval_status}>
              {packet.approval_state}
            </StatusChip>
          }
        >
          <dl className="space-y-2.5 text-sm">
            <Row label="Approver" value={packet.required_approver} />
            <Row label="Draft hash" value={packet.draft_hash} mono />
            <Row label="Payload hash" value={packet.payload_hash} mono />
            <Row label="Revocation" value={packet.revocation_state} mono />
            <Row label="Redacted audit" value={packet.redacted_audit_state} />
          </dl>

          <div className="mt-4 border-t border-line pt-3">
            <SectionLabel>Evidence sources</SectionLabel>
            <div className="flex flex-wrap gap-1.5">
              {packet.evidence_sources.map((e) => (
                <span
                  key={e}
                  className="rounded-md border border-line bg-surface-2 px-1.5 py-0.5 font-mono text-[10.5px] text-fg-muted"
                >
                  {e}
                </span>
              ))}
            </div>
          </div>

          <div className="mt-4 space-y-2 border-t border-line pt-3">
            {packet.comments.map((c, i) => (
              <p key={i} className="text-xs leading-relaxed text-fg-muted">
                <span className="font-semibold text-fg">{c.author}:</span>{' '}
                {c.note}
              </p>
            ))}
          </div>
        </Panel>

        <Panel
          title="Dispatch gate hierarchy"
          subtitle={`${clearedCount}/${packet.gates.length} gates cleared · dispatch globally disabled`}
          actions={<StatusChip status="blocked">Future-gated</StatusChip>}
        >
          <ul className="space-y-1.5">
            {packet.gates.map((g) => {
              const active =
                selected?.kind === 'dispatch_gate' && selected.id === g.id;
              return (
                <li key={g.id}>
                  <button
                    type="button"
                    id={`gate-${g.id}`}
                    onClick={() =>
                      select({
                        kind: 'dispatch_gate',
                        id: g.id,
                        title: g.label,
                        fields: [
                          { label: 'Status', value: g.status, status: g.status },
                          { label: 'Cleared', value: g.cleared ? 'yes' : 'no', mono: true },
                          { label: 'Detail', value: g.detail },
                        ],
                      })
                    }
                    className={`flex w-full items-center justify-between gap-3 rounded-lg border px-3 py-2.5 text-left transition-colors ${
                      active
                        ? 'border-accent/40 bg-accent/5'
                        : 'border-line bg-surface-2 hover:border-line-strong'
                    }`}
                  >
                    <span className="flex min-w-0 items-center gap-2.5">
                      <StatusDot status={g.cleared ? 'verified' : g.status} />
                      <span className="truncate text-sm text-fg">{g.label}</span>
                    </span>
                    <StatusChip status={g.status}>
                      {g.cleared ? 'cleared' : 'pending'}
                    </StatusChip>
                  </button>
                </li>
              );
            })}
          </ul>

          <div className="mt-4">
            <LockedAction
              label="Dispatch to platform"
              reason="No platform/provider API. Live dispatch is future-gated and globally disabled by policy."
            />
          </div>
        </Panel>
      </div>
    </div>
  );
}

function Row({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-3">
      <dt className="font-mono text-[10.5px] uppercase tracking-wide text-fg-subtle">
        {label}
      </dt>
      <dd
        className={`truncate text-sm text-fg ${
          mono ? 'font-mono text-[12px]' : ''
        }`}
      >
        {value}
      </dd>
    </div>
  );
}
