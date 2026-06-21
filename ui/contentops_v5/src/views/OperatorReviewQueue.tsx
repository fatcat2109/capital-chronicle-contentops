// Capital Chronicle ContentOps V5 — Operator Review Queue & Manual Pilot Trail.
// Read-only local-only compliance dashboard. No API connections, credentials, or posting.

import { operatorReviewQueuePacket as q } from '../data/operatorReviewQueuePacket';
import { useApp } from '../state';
import {
  selectOperatorReviewQueuePacket,
  selectReviewItem,
  selectTrailEntry,
  selectLifecycleStage,
} from '../selectors';
import { IconBlock, IconShield } from '../ui/icons';
import { LockedAction, Panel, StatusChip, StatusDot } from '../ui/primitives';
import { contentLifecycleReadModel } from '../data/contentLifecycleReadModelAdapter';

export function OperatorReviewQueue() {
  const { select, selected } = useApp();

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 font-mono text-[11px] font-bold uppercase tracking-[0.14em] text-fg-subtle">
            Manual Pilot Trail
            <span className="text-fg-subtle/60">·</span>
            <span className="text-fg-muted">0174UY</span>
          </div>
          <h1 className="mt-2 flex items-center gap-2 text-2xl font-semibold tracking-tight text-fg">
            <IconShield className="h-6 w-6 text-accent" />
            Operator Review Queue
          </h1>
          <p className="mt-1 max-w-3xl text-sm font-medium leading-relaxed text-fg-muted">
            Local operator review pipeline for manual export packets. It provides verification check
            records and a pilot audit trail without live publish capabilities or credentials.
          </p>
        </div>
        <button
          type="button"
          id="select-operator-queue-packet-btn"
          onClick={() => select(selectOperatorReviewQueuePacket(q))}
          className={`rounded-lg border px-3 py-1 text-left transition-colors ${
            selected?.kind === 'operator_review_queue_packet'
              ? 'border-accent/40 bg-accent/5'
              : 'border-line bg-surface-2 hover:border-line-strong'
          }`}
        >
          <span className="block font-mono text-[10.5px] font-semibold text-fg">
            Queue ID
          </span>
          <span className="font-mono text-[11px] text-fg-subtle">
            {q.queue_id.slice(0, 16)}...
          </span>
        </button>
      </header>

      {/* Safety Strip */}
      <div className="grid grid-cols-1 gap-3 md:grid-cols-5">
        {[
          'Manual Export Only',
          'No platform API',
          'No credentials loaded',
          'No live dispatch',
          'Operator Action Required',
        ].map((label, index) => (
          <div
            key={label}
            id={`operator-queue-safety-${index}`}
            className="rounded-xl border border-status-blocked/30 bg-status-blocked/5 p-3"
          >
            <div className="flex items-center gap-2">
              <StatusDot status="blocked" />
              <span className="text-[12px] font-semibold uppercase tracking-wide text-fg">
                {label}
              </span>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="space-y-6">
          {/* Queue Overview */}
          <Panel
            title="Queue Overview"
            subtitle="Queue references, metadata status, and baseline binding"
            bodyClassName="p-4 space-y-4"
          >
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <Metric label="Queue ID" value={q.queue_id} mono status="review" />
              <Metric label="Item status" value={q.item_status_summary} mono status="review" />
              <Metric label="Packet hash" value={q.packet_hash} mono status="verified" />
            </div>
            <div className="rounded-xl border border-line bg-surface-2 p-4 space-y-2">
              <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle">
                Source References
              </div>
              <div className="grid gap-2">
                <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-line bg-surface-1 px-3 py-2 text-sm">
                  <span className="font-semibold text-fg">Manual Export Hash</span>
                  <span className="font-mono text-[12px] text-fg-muted">{q.source_manual_export_packet_hash}</span>
                </div>
                <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-line bg-surface-1 px-3 py-2 text-sm">
                  <span className="font-semibold text-fg">Baseline Commit</span>
                  <span className="font-mono text-[12px] text-fg-muted">{q.source_baseline_commit}</span>
                </div>
              </div>
            </div>
          </Panel>

          {/* Operator Review Items */}
          <Panel
            title="Operator Review Items"
            subtitle="Awaiting manual human proof checks outside ContentOps"
            bodyClassName="p-0 overflow-x-auto"
          >
            <table className="w-full min-w-[700px] border-collapse text-left text-sm">
              <thead>
                <tr className="border-b border-line bg-surface-2 font-mono text-[10.5px] uppercase tracking-wider text-fg-muted">
                  <th className="px-4 py-3">Item</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">No API</th>
                  <th className="px-4 py-3">No Creds</th>
                  <th className="px-4 py-3">Operator Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {q.review_items.map((item) => (
                  <tr
                    key={item.item_id}
                    id={`operator-review-item-${item.item_id}`}
                    onClick={() => select(selectReviewItem(item))}
                    className={`cursor-pointer transition-colors hover:bg-surface-2/60 ${
                      selected?.kind === 'operator_review_item' && selected.id === item.item_id
                        ? 'bg-accent/5'
                        : ''
                    }`}
                  >
                    <td className="px-4 py-3 font-semibold text-fg">
                      {item.label}
                    </td>
                    <td className="px-4 py-3">
                      <StatusChip status="review">{item.status}</StatusChip>
                    </td>
                    <td className="px-4 py-3">
                      <StatusChip status="verified" nowrap>true</StatusChip>
                    </td>
                    <td className="px-4 py-3">
                      <StatusChip status="verified" nowrap>true</StatusChip>
                    </td>
                    <td className="px-4 py-3 text-[12px] text-fg-muted">
                      Required
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Panel>
        </div>

        <div className="space-y-6">
          {/* Content Lifecycle Spine */}
          <Panel
            title="Content Lifecycle Spine"
            subtitle="16 stages canonical lifecycle & operator read-model"
            bodyClassName="p-4 space-y-4"
          >
            {/* Spine summary / Next task */}
            <div className="rounded-xl border border-line bg-surface-2 p-3 space-y-2">
              <div className="flex flex-wrap items-center justify-between gap-2 text-[12px]">
                <span className="font-semibold text-fg">Current Position</span>
                <span className="font-mono text-[11px] text-fg-subtle">{contentLifecycleReadModel.currentLifecyclePosition}</span>
              </div>
              <div className="flex flex-wrap items-center justify-between gap-2 text-[12px]">
                <span className="font-semibold text-fg">Next Blocker</span>
                <span className="font-mono text-[11px] text-status-blocked">{contentLifecycleReadModel.nextBlocker || 'None'}</span>
              </div>
              <div className="flex flex-col gap-1 text-[12px]">
                <span className="font-semibold text-fg">Next Recommended Task</span>
                <span className="font-mono text-[11px] text-fg-muted break-all">{contentLifecycleReadModel.nextRecommendedTask}</span>
              </div>
            </div>

            {/* Safety Locks Status */}
            <div className="rounded-xl border border-line bg-surface-2 p-3 space-y-2">
              <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle">
                Read-Model Safety Locks
              </div>
              <div className="flex flex-wrap gap-1.5">
                <StatusChip status="verified">
                  Safety Locks: Active
                </StatusChip>
                {contentLifecycleReadModel.safetyFlags.live_api_called ? (
                  <StatusChip status="blocked">Live API</StatusChip>
                ) : (
                  <StatusChip status="verified">No Live API</StatusChip>
                )}
                {contentLifecycleReadModel.safetyFlags.provider_api_called ? (
                  <StatusChip status="blocked">Provider API</StatusChip>
                ) : (
                  <StatusChip status="verified">No Provider API</StatusChip>
                )}
                {contentLifecycleReadModel.safetyFlags.env_read ? (
                  <StatusChip status="blocked">Env Read</StatusChip>
                ) : (
                  <StatusChip status="verified">No Env Read</StatusChip>
                )}
                {contentLifecycleReadModel.safetyFlags.credential_hydrated ? (
                  <StatusChip status="blocked">Credentials</StatusChip>
                ) : (
                  <StatusChip status="verified">No Credentials</StatusChip>
                )}
              </div>
            </div>

            {/* Stage List */}
            <div className="space-y-2 max-h-[400px] overflow-y-auto pr-1">
              {contentLifecycleReadModel.stages.map((stage) => {
                const isCurrent = stage.stage_id === contentLifecycleReadModel.currentLifecyclePosition;
                const isSelected = selected?.kind === 'lifecycle_stage' && selected.id === stage.stage_id;
                let statusColor: 'verified' | 'blocked' | 'review' = 'review';
                if (stage.state === 'COMPLETED') statusColor = 'verified';
                if (stage.state === 'BLOCKED') statusColor = 'blocked';

                return (
                  <button
                    key={stage.stage_id}
                    type="button"
                    onClick={() => select(selectLifecycleStage(stage))}
                    className={`flex w-full items-center justify-between gap-3 rounded-xl border p-3 text-left transition-colors hover:border-line-strong ${
                      isSelected
                        ? 'border-accent/40 bg-accent/5'
                        : isCurrent
                        ? 'border-status-review/50 bg-status-review/5'
                        : 'border-line bg-surface-2'
                    }`}
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <StatusDot status={statusColor} />
                      <div className="min-w-0">
                        <div className="flex items-center gap-1.5">
                          <span className="font-mono text-[10.5px] font-bold text-fg-subtle">
                            {String(stage.stage_order).padStart(2, '0')}
                          </span>
                          <span className={`text-xs font-semibold truncate ${isCurrent ? 'text-fg font-bold' : 'text-fg-muted'}`}>
                            {stage.stage_name}
                          </span>
                          {isCurrent && (
                            <span className="rounded bg-status-review/20 px-1 py-0.2 text-[9px] font-bold uppercase tracking-wider text-status-review">
                              Current
                            </span>
                          )}
                        </div>
                        <div className="font-mono text-[9.5px] text-fg-subtle truncate mt-0.5">
                          {stage.stage_id}
                        </div>
                      </div>
                    </div>
                    <StatusChip status={statusColor}>{stage.state}</StatusChip>
                  </button>
                );
              })}
            </div>
          </Panel>

          {/* Manual Pilot Trail */}
          <Panel
            title="Manual Pilot Trail Timeline"
            subtitle="Deterministic local review trail audit history"
            bodyClassName="p-4"
          >
            <div className="space-y-3">
              {q.local_review_trail_entries.map((entry) => {
                const active = selected?.kind === 'local_review_trail_entry' && selected.id === entry.entry_id;
                return (
                  <button
                    key={entry.entry_id}
                    type="button"
                    id={`operator-trail-entry-${entry.entry_id}`}
                    onClick={() => select(selectTrailEntry(entry))}
                    className={`flex w-full items-start gap-3 rounded-xl border p-3 text-left transition-colors hover:border-line-strong ${
                      active ? 'border-accent/40 bg-accent/5' : 'border-line bg-surface-2'
                    }`}
                  >
                    <StatusDot status={entry.status} />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-mono text-[10.5px] uppercase tracking-wide text-fg-subtle">
                          {entry.entry_type.replace(/_/g, ' ')}
                        </span>
                        <StatusChip status={entry.status}>{entry.status}</StatusChip>
                      </div>
                      <p className="mt-1 text-xs leading-relaxed text-fg-muted">
                        {entry.label}
                      </p>
                    </div>
                  </button>
                );
              })}
            </div>
          </Panel>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Placeholders */}
        <Panel
          title="Manual Publish Placeholders"
          subtitle="Waiting for off-system operator action"
          bodyClassName="p-4 space-y-3"
        >
          {q.manual_publish_placeholders.map((ph, idx) => (
            <div key={idx} className="rounded-xl border border-line bg-surface-2 p-3">
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm font-semibold text-fg">
                  {idx === 0 ? 'Manual Publish URL' : 'Manual Publish Metrics'}
                </span>
                <StatusChip status="review">{ph.status}</StatusChip>
              </div>
              <div className="mt-2 rounded-lg border border-dashed border-line-strong bg-surface-1 px-3 py-2 font-mono text-[12px] text-fg-subtle">
                value: ''
              </div>
              <p className="mt-2 text-[12px] leading-relaxed text-fg-muted">{ph.detail}</p>
            </div>
          ))}
        </Panel>

        {/* Disabled Live Actions */}
        <Panel
          title="Disabled Live Actions"
          subtitle="Visible controls confirm platform APIs are blocked"
          bodyClassName="p-4"
        >
          <div className="mb-4 flex items-start gap-3 rounded-xl border border-status-blocked/30 bg-status-blocked/5 p-3">
            <IconBlock className="mt-0.5 h-4 w-4 shrink-0 text-status-blocked" />
            <p className="text-[12px] leading-relaxed text-fg-muted">
              Live platform interfaces remain locked: publish, send, schedule,
              connect account, verify credentials, sync platform, and live dispatch.
            </p>
          </div>
          <div className="grid gap-2 sm:grid-cols-2">
            {['Publish', 'Send', 'Schedule', 'Connect account', 'Verify credentials', 'Sync platform', 'Live dispatch'].map((label) => (
              <div key={label} id={`operator-queue-disabled-${label.toLowerCase().replace(/\s+/g, '-')}`}>
                <LockedAction
                  label={label}
                  reason={q.disabled_live_action_state.reason}
                />
              </div>
            ))}
          </div>
        </Panel>
      </div>

      {/* Blocked / Missing Proofs */}
      <Panel
        title="Blocked / Missing Proofs"
        subtitle="Verification packets that remain unproven"
        bodyClassName="p-4"
      >
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div className="rounded-xl border border-line bg-surface-2 p-4">
            <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-status-blocked">
              Blocked Reasons
            </div>
            <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-fg-muted">
              {q.blocked_reasons.map((reason) => (
                <li key={reason} className="font-mono text-[12px]">{reason}</li>
              ))}
            </ul>
          </div>
          <div className="rounded-xl border border-line bg-surface-2 p-4">
            <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-status-review">
              Missing Proofs
            </div>
            <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-fg-muted">
              {q.missing_proofs.map((proof) => (
                <li key={proof} className="font-mono text-[12px]">{proof}</li>
              ))}
            </ul>
          </div>
        </div>
      </Panel>
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
