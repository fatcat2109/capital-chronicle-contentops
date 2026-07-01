// Capital Chronicle ContentOps V5 â€” Approval Queue + Dispatch Control view.
// Dispatch is visibly future-gated and DISABLED. No live publish/post/
// schedule/API affordance. No network, no storage, no credentials.

import { SubstackArticleStudioCard } from './SubstackArticleStudioCard';
import {
  substackManualApprovalExportEvidencePacket,
  substackManualExportOperatorHandoffPacket,
} from '../data/substackManualExportArticleStudioAdapter';
import { useApp } from '../state';
import { viewModel } from '../fixtures';
import { selectDispatchGate } from '../selectors';
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
  const v6Packet = viewModel.v6_operator_approval_evidence;
  const clearedCount = packet.gates.filter((g) => g.cleared).length;

  return (
    <div className="space-y-6">
      <SubstackArticleStudioCard mode="approval" />
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
          title={`Approval packet Â· ${packet.id}`}
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
          subtitle={`${clearedCount}/${packet.gates.length} gates cleared Â· dispatch globally disabled`}
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
                    onClick={() => select(selectDispatchGate(g))}
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
      <Panel
        title="Substack manual approval/export evidence"
        subtitle={substackManualApprovalExportEvidencePacket.approval_export_evidence_packet_id}
        actions={<StatusChip status="review">{substackManualApprovalExportEvidencePacket.operator_review_status}</StatusChip>}
      >
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          <Row label="Approval" value={substackManualApprovalExportEvidencePacket.approval_status} />
          <Row label="Manual export" value={substackManualApprovalExportEvidencePacket.manual_export_status} />
          <Row label="Substack API" value={String(substackManualApprovalExportEvidencePacket.substack_api_used)} mono />
        </div>
        <div className="mt-3 rounded-lg border border-status-blocked/30 bg-status-blocked/5 p-3 font-mono text-[11px] text-status-blocked">
          approve/send/publish/dispatch controls enabled={String(substackManualApprovalExportEvidencePacket.enabled_publish_send_dispatch_approve_controls)}
        </div>
      </Panel>
      <Panel
        title="Substack operator handoff pending review"
        subtitle={substackManualExportOperatorHandoffPacket.operator_handoff_packet_id}
        actions={<StatusChip status="review">{substackManualExportOperatorHandoffPacket.operator_handoff_status}</StatusChip>}
      >
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          <Row label="Approval" value={substackManualExportOperatorHandoffPacket.approval_status} />
          <Row label="Manual copy only" value={String(substackManualExportOperatorHandoffPacket.manual_copy_only)} mono />
          <Row label="Live publish" value={String(substackManualExportOperatorHandoffPacket.live_publish_allowed)} mono />
        </div>
        <div className="mt-3 rounded-lg border border-status-blocked/30 bg-status-blocked/5 p-3 font-mono text-[11px] text-status-blocked">
          blocked controls: {substackManualExportOperatorHandoffPacket.blocked_controls.join(', ')} · enabled={String(substackManualExportOperatorHandoffPacket.enabled_publish_send_dispatch_approve_controls)}
        </div>
      </Panel>
      <Panel
        title="V6 operator approval queue · fixture-only"
        subtitle={`${v6Packet.approval_queue_items.length} pending previews · ${v6Packet.sample_scope}`}
        actions={<StatusChip status="review">sample_fixture_only</StatusChip>}
      >
        <div className="mb-3 rounded-lg border border-status-blocked/30 bg-status-blocked/5 p-3 text-xs leading-relaxed text-fg-muted">
          Committed sample packet only. Runtime proof is false; live send, dispatch,
          provider calls, network, browser session use, raw secret serialization,
          and env line serialization are all disabled/false.
        </div>
        <ul className="space-y-2">
          {v6Packet.approval_queue_items.map((item) => (
            <li key={item.queue_item_id} className="rounded-lg border border-line bg-surface-2 p-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="min-w-0">
                  <div className="font-mono text-[11px] font-bold uppercase tracking-wide text-fg-subtle">
                    {item.platform}
                  </div>
                  <div className="mt-1 truncate text-sm font-semibold text-fg">
                    {item.preview_id}
                  </div>
                </div>
                <StatusChip status="review">{item.approval_status}</StatusChip>
              </div>
              <div className="mt-2 break-all font-mono text-[11px] text-fg-muted">
                preview_hash: {item.preview_hash}
              </div>
              <p className="mt-2 text-xs leading-relaxed text-fg-muted">
                {item.required_operator_action}
              </p>
              <StatusChip status="blocked">live blocked</StatusChip>
            </li>
          ))}
        </ul>
      </Panel>
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
