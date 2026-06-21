// Capital Chronicle ContentOps V5 — Manual Pilot Trail Reconciliation.
// Read-only local compliance reconciliation page. No API connections, credentials, or posting.

import { manualPilotTrailReconciliationPacket as r } from '../data/manualPilotTrailReconciliationPacket';
import { useApp } from '../state';
import {
  selectManualPilotTrailReconciliationPacket,
  selectLifecycleStep,
  selectPlaceholderField,
} from '../selectors';
import { IconBlock, IconShield } from '../ui/icons';
import { LockedAction, Panel, StatusChip, StatusDot } from '../ui/primitives';

export function ManualPilotTrailReconciliation() {
  const { select, selected } = useApp();

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 font-mono text-[11px] font-bold uppercase tracking-[0.14em] text-fg-subtle">
            Manual Pilot Reconciliation
            <span className="text-fg-subtle/60">·</span>
            <span className="text-fg-muted">0174UZ</span>
          </div>
          <h1 className="mt-2 flex items-center gap-2 text-2xl font-semibold tracking-tight text-fg">
            <IconShield className="h-6 w-6 text-accent" />
            Manual Pilot Trail Reconciliation
          </h1>
          <p className="mt-1 max-w-3xl text-sm font-medium leading-relaxed text-fg-muted">
            Deterministic compliance reconciliation layer linking export verification
            and operator review pipelines. Reconciliation remains blocked until the
            operator records manual off-system URL and metrics.
          </p>
        </div>
        <button
          type="button"
          id="select-reconciliation-packet-btn"
          onClick={() => select(selectManualPilotTrailReconciliationPacket(r))}
          className={`rounded-lg border px-3 py-1 text-left transition-colors ${
            selected?.kind === 'manual_pilot_trail_reconciliation_packet'
              ? 'border-accent/40 bg-accent/5'
              : 'border-line bg-surface-2 hover:border-line-strong'
          }`}
        >
          <span className="block font-mono text-[10.5px] font-semibold text-fg">
            Reconciliation ID
          </span>
          <span className="font-mono text-[11px] text-fg-subtle">
            {r.reconciliation_id.slice(0, 16)}...
          </span>
        </button>
      </header>

      {/* Safety Strip (11 Safety Flags) */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-6 xl:grid-cols-11">
        {Object.entries(r.safety_flags).map(([key, val]) => (
          <div
            key={key}
            id={`reconciliation-safety-${key}`}
            className={`rounded-xl border p-2 text-center ${
              val
                ? 'border-status-verified/20 bg-status-verified/5'
                : 'border-status-blocked/20 bg-status-blocked/5'
            }`}
          >
            <div className="flex flex-col items-center gap-1">
              <StatusDot status={val ? 'verified' : 'blocked'} />
              <span className="break-all font-mono text-[9px] font-bold uppercase tracking-wider text-fg whitespace-normal">
                {key.replace(/_/g, ' ')}
              </span>
              <span className="font-mono text-[9px] font-semibold text-fg-muted">
                {val ? 'TRUE' : 'FALSE'}
              </span>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="space-y-6">
          {/* Overview */}
          <Panel
            title="Reconciliation Overview"
            subtitle="Pipeline status, bounds proof, and identity references"
            bodyClassName="p-4 space-y-4"
          >
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <Metric label="Reconciliation Status" value={r.reconciliation_status} mono status="blocked" />
              <Metric label="Contract Version" value={r.contract_version} mono status="review" />
              <Metric label="Packet Hash" value={r.packet_hash} mono status="verified" />
            </div>

            <div className="rounded-xl border border-line bg-surface-2 p-4 space-y-2">
              <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle">
                Source Pipeline Bindings
              </div>
              <div className="grid gap-2">
                <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-line bg-surface-1 px-3 py-2 text-sm">
                  <span className="font-semibold text-fg">Operator Review Queue ID</span>
                  <span className="font-mono text-[12px] text-fg-muted">{r.source_operator_review_queue_id}</span>
                </div>
                <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-line bg-surface-1 px-3 py-2 text-sm">
                  <span className="font-semibold text-fg">Source Operator Review Packet Hash</span>
                  <span className="font-mono text-[12px] text-fg-muted">{r.source_operator_review_packet_hash}</span>
                </div>
                <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-line bg-surface-1 px-3 py-2 text-sm">
                  <span className="font-semibold text-fg">Source Manual Export Hash</span>
                  <span className="font-mono text-[12px] text-fg-muted">{r.source_manual_export_packet_hash}</span>
                </div>
                <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-line bg-surface-1 px-3 py-2 text-sm">
                  <span className="font-semibold text-fg">Baseline Commit</span>
                  <span className="font-mono text-[12px] text-fg-muted">{r.source_baseline_commit}</span>
                </div>
              </div>
            </div>
          </Panel>

          {/* Lifecycle Steps */}
          <Panel
            title="Reconciliation Lifecycle Steps"
            subtitle="Deterministic manual pilot reconciliation checklist steps"
            bodyClassName="p-0 overflow-x-auto"
          >
            <table className="w-full min-w-[700px] border-collapse text-left text-sm">
              <thead>
                <tr className="border-b border-line bg-surface-2 font-mono text-[10.5px] uppercase tracking-wider text-fg-muted">
                  <th className="px-4 py-3">Step</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Verification Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {r.lifecycle_steps.map((step) => (
                  <tr
                    key={step.step_id}
                    id={`reconciliation-step-${step.step_id}`}
                    onClick={() => select(selectLifecycleStep(step))}
                    className={`cursor-pointer transition-colors hover:bg-surface-2/60 ${
                      selected?.kind === 'reconciliation_lifecycle_step' && selected.id === step.step_id
                        ? 'bg-accent/5'
                        : ''
                    }`}
                  >
                    <td className="px-4 py-3 font-semibold text-fg">
                      {step.label}
                    </td>
                    <td className="px-4 py-3">
                      <StatusChip status={step.status} nowrap>{step.status}</StatusChip>
                    </td>
                    <td className="px-4 py-3 text-[12.5px] text-fg-muted">
                      {step.detail}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Panel>
        </div>

        <div className="space-y-6">
          {/* Missing Evidence & Placeholders */}
          <Panel
            title="Missing Evidence & Placeholders"
            subtitle="Unrecorded compliance proof slots (must remain empty)"
            bodyClassName="p-4 space-y-4"
          >
            <div className="rounded-xl border border-status-blocked/30 bg-status-blocked/5 p-3">
              <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-status-blocked flex items-center gap-1.5">
                <IconBlock className="h-3.5 w-3.5" />
                Reconciliation Blocked
              </div>
              <p className="mt-1 text-xs text-fg-muted leading-relaxed">
                Evidence placeholders remain unrecorded. Reconciling pilot trail requires manual URL and metrics entry from outside ContentOps.
              </p>
            </div>

            <div className="space-y-3">
              {r.placeholder_fields.map((fld) => {
                const active = selected?.kind === 'reconciliation_placeholder_field' && selected.id === fld.field_id;
                return (
                  <button
                    key={fld.field_id}
                    type="button"
                    id={`reconciliation-field-${fld.field_id}`}
                    onClick={() => select(selectPlaceholderField(fld))}
                    className={`flex w-full flex-col gap-2 rounded-xl border p-3 text-left transition-colors hover:border-line-strong ${
                      active ? 'border-accent/40 bg-accent/5' : 'border-line bg-surface-2'
                    }`}
                  >
                    <div className="flex w-full items-center justify-between gap-2">
                      <span className="font-semibold text-sm text-fg">
                        {fld.label}
                      </span>
                      <StatusChip status="review" nowrap>{fld.status}</StatusChip>
                    </div>
                    <div className="w-full rounded-lg border border-dashed border-line-strong bg-surface-1 px-3 py-1.5 font-mono text-[12px] text-fg-subtle">
                      value: ''
                    </div>
                    <p className="text-[12px] text-fg-muted leading-relaxed">
                      {fld.detail}
                    </p>
                  </button>
                );
              })}
            </div>
          </Panel>

          {/* Disabled Live Actions */}
          <Panel
            title="Disabled Live Actions"
            subtitle="Hard bounds guarantee platform security"
            bodyClassName="p-4"
          >
            <div className="mb-4 flex items-start gap-3 rounded-xl border border-status-blocked/30 bg-status-blocked/5 p-3">
              <IconBlock className="mt-0.5 h-4 w-4 shrink-0 text-status-blocked" />
              <p className="text-[12px] leading-relaxed text-fg-muted">
                Automation remains completely disabled. Publishing, sending, scheduling,
                or verifying credentials requires off-system manual pilot execution.
              </p>
            </div>
            <div className="grid gap-2 sm:grid-cols-2">
              {['Publish', 'Send', 'Schedule', 'Connect account', 'Verify credentials', 'Sync platform', 'Live dispatch'].map((label) => (
                <div key={label} id={`reconciliation-disabled-${label.toLowerCase().replace(/\s+/g, '-')}`}>
                  <LockedAction
                    label={label}
                    reason={r.disabled_live_action_state.reason}
                  />
                </div>
              ))}
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}

function Metric({
  label,
  value,
  mono,
  status,
}: {
  label: string;
  value: string;
  mono?: boolean;
  status?: 'verified' | 'review' | 'blocked';
}) {
  return (
    <div className="rounded-xl border border-line bg-surface-2 p-3">
      <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle">
        {label}
      </div>
      <div className={`mt-1 break-all text-sm font-semibold text-fg ${mono ? 'font-mono text-[12px] font-normal' : ''}`}>
        {status ? <StatusChip status={status}>{value}</StatusChip> : value}
      </div>
    </div>
  );
}
