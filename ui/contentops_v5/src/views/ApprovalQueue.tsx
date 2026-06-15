// Capital Chronicle ContentOps V5 — Approval Queue + Dispatch Control view.
// Dispatch is visibly future-gated and DISABLED. No live publish/post/
// schedule/API affordance. No network, no storage, no credentials.

import { useApp } from '../state';
import { viewModel } from '../fixtures';
import { LockedAction, Panel, StatusChip } from '../ui/primitives';

export function ApprovalQueue() {
  const { select } = useApp();
  const packet = viewModel.approval_packets[0];

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-fg">
            Approval &amp; Dispatch Control
          </h1>
          <p className="mt-1 text-sm text-fg-muted">
            Manual approval packets and a future-gated dispatch hierarchy.
            No live posting, scheduling, or platform/provider API exists.
          </p>
        </div>
        <StatusChip status="blocked">DISPATCH DISABLED</StatusChip>
      </header>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Panel title={`Approval packet · ${packet.id}`}>
          <h3 className="text-sm font-semibold text-fg">{packet.title}</h3>
          <dl className="mt-3 space-y-2 text-sm">
            <Row label="Required approver" value={packet.required_approver} />
            <Row label="Draft hash" value={packet.draft_hash} mono />
            <Row label="Payload hash" value={packet.payload_hash} mono />
            <Row label="Approval state" value={packet.approval_state} />
            <Row label="Revocation" value={packet.revocation_state} mono />
            <Row label="Redacted audit" value={packet.redacted_audit_state} />
          </dl>
          <div className="mt-3 flex flex-wrap gap-2">
            {packet.evidence_sources.map((e) => (
              <span
                key={e}
                className="rounded border border-line bg-surface-2 px-1.5 py-0.5 font-mono text-[11px] text-fg-muted"
              >
                {e}
              </span>
            ))}
          </div>
          <div className="mt-4 border-t border-line pt-3">
            {packet.comments.map((c, i) => (
              <p key={i} className="text-xs text-fg-muted">
                <span className="font-semibold text-fg">{c.author}:</span>{' '}
                {c.note}
              </p>
            ))}
          </div>
        </Panel>

        <Panel
          title="Dispatch gate hierarchy"
          actions={<StatusChip status="blocked">FUTURE-GATED</StatusChip>}
        >
          <ul className="space-y-2">
            {packet.gates.map((g) => (
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
                  className="flex w-full items-center justify-between gap-3 rounded-md border border-line bg-surface-2 px-3 py-2 text-left hover:bg-surface-3"
                >
                  <span className="flex items-center gap-2">
                    <span
                      className={`inline-block h-2 w-2 rounded-full ${
                        g.cleared ? 'bg-status-verified' : 'bg-fg-muted'
                      }`}
                      aria-hidden
                    />
                    <span className="text-sm text-fg">{g.label}</span>
                  </span>
                  <StatusChip status={g.status}>
                    {g.cleared ? 'cleared' : 'pending'}
                  </StatusChip>
                </button>
              </li>
            ))}
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
      <dt className="font-mono text-[11px] uppercase text-fg-muted">{label}</dt>
      <dd className={`text-sm text-fg ${mono ? 'font-mono text-[12px]' : ''}`}>
        {value}
      </dd>
    </div>
  );
}
