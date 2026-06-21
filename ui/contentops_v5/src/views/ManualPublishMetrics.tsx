// Capital Chronicle ContentOps V5 — Manual Publish + Metrics Capture view.
// MANUAL-ONLY recordkeeping. This surface is the bridge from dry-run payload
// preview to operator MANUAL posting: the operator posts off-platform by hand,
// then records the (mock/local) URL, timestamp, and any manually-observed
// metrics here. There is ZERO live posting, scheduling, platform/provider API,
// credential read, metrics fetch, or autonomous behavior. Every record carries
// can_post_live: false (structurally unrepresentable as true). The optional
// "mark manual posted" control is always disabled and fixture-only — it never
// mutates persisted data. Any interactive field is React local state only and
// is labeled a local unsaved draft. No network, no storage, no credentials.

import { useMemo, useState } from 'react';
import { useApp } from '../state';
import { viewModel } from '../fixtures';
import {
  selectManualChecklistItem,
  selectManualPublishRecord,
  selectMetricsSnapshot,
} from '../selectors';
import { IconBlock, IconSend } from '../ui/icons';
import {
  LockedAction,
  Panel,
  SectionLabel,
  StatusChip,
  StatusDot,
} from '../ui/primitives';
import type { ManualPublishRecord, MetricsSnapshot } from '../types';

type StageTab = ManualPublishRecord['stage'];

const STAGE_TABS: { id: StageTab; label: string }[] = [
  { id: 'approved_for_manual', label: 'Verified local (manual)' },
  { id: 'blocked', label: 'Blocked' },
  { id: 'manually_posted', label: 'Manually posted' },
  { id: 'metrics_entered', label: 'Metrics entered' },
];

const POLICY_STATES = [
  'MANUAL_ONLY',
  'NO_PLATFORM_API',
  'NO_CREDENTIAL_READ',
  'NO_SCHEDULER',
  'NO_AUTONOMOUS_POSTING',
  'METRICS_MANUAL_ENTRY_ONLY',
  'HUMAN_REVIEW_REQUIRED',
];

export function ManualPublishMetrics() {
  const { select, selected } = useApp();
  const records = viewModel.manual_publish_records;
  const [activeTab, setActiveTab] = useState<StageTab>('approved_for_manual');

  const counts = useMemo(() => {
    const c: Record<StageTab, number> = {
      approved_for_manual: 0,
      blocked: 0,
      manually_posted: 0,
      metrics_entered: 0,
    };
    for (const r of records) c[r.stage] += 1;
    return c;
  }, [records]);

  const visible = records.filter((r) => r.stage === activeTab);
  const active: ManualPublishRecord | undefined =
    visible.find(
      (r) => selected?.kind === 'manual_publish_record' && selected.id === r.id,
    ) ?? visible[0];

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 font-mono text-[11px] font-bold uppercase tracking-[0.14em] text-fg-subtle">
            Manual publish + metrics capture
            <span className="text-fg-subtle/60">·</span>
            <span className="text-fg-muted">recordkeeping only</span>
          </div>
          <h1 className="mt-2 flex items-center gap-2 text-2xl font-semibold tracking-tight text-fg">
            <IconSend className="h-6 w-6 text-accent" />
            Manual Publish
          </h1>
          <p className="mt-1 text-sm font-medium text-fg-muted">
            Record manual, off-platform posts and hand-entered metrics — no live
            posting, no metrics API.
          </p>
        </div>
        <div className="flex flex-col items-end gap-1.5">
          <StatusChip status="blocked" icon nowrap>
            Manual only · not live
          </StatusChip>
          <span className="font-mono text-[10.5px] text-status-blocked">
            can_post_live: false
          </span>
        </div>
      </header>

      {/* Manual-only policy banner — make the no-live posture unmissable. */}
      <div className="flex items-start gap-2.5 rounded-xl border border-status-blocked/30 bg-status-blocked/5 p-4">
        <IconBlock className="mt-0.5 h-4 w-4 shrink-0 text-status-blocked" />
        <div className="min-w-0">
          <p className="text-sm font-semibold text-fg">
            Manual recordkeeping — the operator posts by hand, off-platform
          </p>
          <p className="mt-1 text-[12px] leading-relaxed text-fg-muted">
            This screen records what a human did: the manual post URL (a local
            mock string, never fetched), a publish timestamp, and any metrics
            typed in by hand. There is no platform API, no provider call, no
            credential or token read, no scheduler, and no metrics fetch or
            sync. Nothing here posts, schedules, or reads live data.
          </p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {POLICY_STATES.map((s) => (
              <span
                key={s}
                className="rounded-md border border-line bg-surface-2 px-1.5 py-0.5 font-mono text-[10.5px] text-fg-muted"
              >
                {s}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Stage tabs */}
      <div
        role="tablist"
        aria-label="Manual publish stages"
        className="flex flex-wrap gap-1.5"
      >
        {STAGE_TABS.map((t) => {
          const isActive = t.id === activeTab;
          return (
            <button
              type="button"
              key={t.id}
              id={`manual-tab-${t.id}`}
              role="tab"
              aria-selected={isActive}
              onClick={() => setActiveTab(t.id)}
              className={`flex items-center gap-2 rounded-lg border px-3 py-1.5 text-sm font-medium transition-colors ${
                isActive
                  ? 'border-accent/40 bg-accent/5 text-fg'
                  : 'border-line bg-surface-2 text-fg-muted hover:border-line-strong hover:text-fg'
              }`}
            >
              {t.label}
              <span className="rounded-full border border-line bg-surface-1 px-1.5 font-mono text-[10.5px] text-fg-subtle">
                {counts[t.id]}
              </span>
            </button>
          );
        })}
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        {/* Candidate / record list */}
        <div className="space-y-3">
          <SectionLabel>{STAGE_TABS.find((t) => t.id === activeTab)?.label}</SectionLabel>
          {visible.length === 0 ? (
            <p className="rounded-lg border border-dashed border-line bg-surface-2 p-4 text-[12px] text-fg-subtle">
              No records in this stage.
            </p>
          ) : (
            visible.map((r) => {
              const isActive =
                selected?.kind === 'manual_publish_record' &&
                selected.id === r.id;
              return (
                <button
                  type="button"
                  key={r.id}
                  id={`manual-record-${r.id}`}
                  onClick={() => select(selectManualPublishRecord(r))}
                  className={`w-full rounded-lg border px-3 py-2.5 text-left transition-colors ${
                    isActive
                      ? 'border-accent/40 bg-accent/5'
                      : 'border-line bg-surface-2 hover:border-line-strong'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="flex items-center gap-2 text-sm font-semibold text-fg">
                      <StatusDot status={r.stage_status} />
                      {r.platform}
                    </span>
                    <StatusChip status={r.stage_status}>
                      {r.stage_label}
                    </StatusChip>
                  </div>
                  <p className="mt-1 font-mono text-[10.5px] text-fg-subtle">
                    {r.id} · {r.source_draft_id}
                  </p>
                </button>
              );
            })
          )}
        </div>

        {/* Selected record detail */}
        <div className="space-y-6 xl:col-span-2">
          {active ? (
            <ManualRecordDetail record={active} />
          ) : (
            <Panel title="No record selected" bodyClassName="p-4">
              <p className="text-[12px] text-fg-subtle">
                Select a record from the list to view its manual publish details.
              </p>
            </Panel>
          )}
        </div>
      </div>
    </div>
  );
}

function ManualRecordDetail({ record }: { record: ManualPublishRecord }) {
  const { select, selected } = useApp();
  const r = record;
  const isBlocked = r.stage === 'blocked';

  return (
    <>
      <Panel
        title={
          <button
            type="button"
            id={`manual-summary-${r.id}`}
            onClick={() => select(selectManualPublishRecord(r))}
            className="text-left text-sm font-semibold text-fg hover:text-accent"
          >
            {r.platform} manual publish
          </button>
        }
        subtitle={`${r.id} · source ${r.source_draft_id}`}
        actions={<StatusChip status={r.stage_status}>{r.stage_label}</StatusChip>}
        bodyClassName="p-4 space-y-3"
      >
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <RefField label="Payload ref" value={r.payload_ref} />
          <RefField label="Payload hash" value={r.payload_hash} />
          <RefField label="Approval packet" value={r.approval_packet_ref} />
          <RefField label="Approval hash" value={r.approval_packet_hash} />
        </div>

        {/* Manual URL — local mock string only, read-only, never fetched. */}
        <div>
          <SectionLabel>Manual post URL (local mock)</SectionLabel>
          <input
            type="text"
            readOnly
            id={`manual-url-${r.id}`}
            value={r.manual_url || '(not posted yet)'}
            aria-label={`${r.platform} manual post URL (local mock, read only)`}
            className="w-full rounded-lg border border-line bg-surface-2 px-3 py-2 font-mono text-[12px] text-fg-muted"
          />
          <p className="mt-1 flex items-center gap-2 text-[11px] text-fg-subtle">
            <StatusDot status="neutral" />
            Local mock string · never fetched or validated against any platform.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <RefField
            label="Published at"
            value={r.published_at || '(not posted)'}
          />
          <RefField label="Audit state" value={r.audit_state} />
        </div>

        {isBlocked && (
          <div className="flex items-start gap-2 rounded-lg border border-status-blocked/30 bg-status-blocked/5 p-3">
            <IconBlock className="mt-0.5 h-3.5 w-3.5 shrink-0 text-status-blocked" />
            <p className="text-[12px] leading-relaxed text-status-blocked">
              {r.blocked_reason}
            </p>
          </div>
        )}
      </Panel>

      {/* Operator checklist */}
      <Panel
        title="Operator checklist"
        subtitle="Select an item to inspect · recordkeeping only"
        bodyClassName="p-3 space-y-2"
      >
        {r.checklist.map((c) => {
          const isActive =
            selected?.kind === 'manual_checklist_item' && selected.id === c.id;
          return (
            <button
              type="button"
              key={c.id}
              id={`manual-checklist-${c.id}`}
              onClick={() => select(selectManualChecklistItem(c, r.platform))}
              className={`w-full rounded-lg border px-3 py-2.5 text-left transition-colors ${
                isActive
                  ? 'border-accent/40 bg-accent/5'
                  : 'border-line bg-surface-2 hover:border-line-strong'
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="flex items-center gap-2 text-sm font-medium text-fg">
                  <StatusDot status={c.status} />
                  {c.label}
                </span>
                <StatusChip status={c.status}>{c.status}</StatusChip>
              </div>
              <p className="mt-1 text-[11px] leading-relaxed text-fg-subtle">
                {c.detail}
              </p>
            </button>
          );
        })}
      </Panel>

      {/* Metrics snapshots — manual entry only */}
      <Panel
        title="Metrics snapshots"
        subtitle="Manually entered only · no metrics API, no sync, no fetch"
        actions={
          <StatusChip status="blocked" nowrap>
            Manual entry only
          </StatusChip>
        }
        bodyClassName="p-4 space-y-3"
      >
        {r.metrics.length === 0 ? (
          <p className="rounded-lg border border-dashed border-line bg-surface-2 p-4 text-[12px] text-fg-subtle">
            No metrics recorded yet. Metrics are typed in by hand from what the
            operator observed on-platform.
          </p>
        ) : (
          r.metrics.map((m) => (
            <MetricsCard
              key={m.id}
              metric={m}
              platform={r.platform}
              active={
                selected?.kind === 'metrics_snapshot' && selected.id === m.id
              }
              onSelect={() => select(selectMetricsSnapshot(m, r.platform))}
            />
          ))
        )}
      </Panel>

      {/* Locked manual-post action — disabled, fixture-only, never mutates. */}
      <Panel
        title="Mark manual posted"
        subtitle="Disabled · fixture-only, does not persist or post"
        bodyClassName="p-4"
      >
        <LockedAction
          label="Mark manual posted"
          reason="Fixture-only. This surface does not persist records and never posts, schedules, or reads live data. Manual posting happens off-platform by a human; this screen only records it."
        />
      </Panel>
    </>
  );
}

function MetricsCard({
  metric,
  platform,
  active,
  onSelect,
}: {
  metric: MetricsSnapshot;
  platform: string;
  active: boolean;
  onSelect: () => void;
}) {
  const m = metric;
  const cells: { label: string; value?: number }[] = [
    { label: 'Impressions', value: m.impressions },
    { label: 'Likes', value: m.likes },
    { label: 'Comments', value: m.comments },
    { label: 'Shares', value: m.shares },
    { label: 'Saves', value: m.saves },
    { label: 'Clicks', value: m.click_count },
  ].filter((c) => c.value !== undefined);

  return (
    <button
      type="button"
      id={`metrics-snapshot-${m.id}`}
      onClick={onSelect}
      aria-label={`Metrics snapshot for ${platform} captured ${m.captured_at}`}
      className={`w-full rounded-lg border px-3 py-3 text-left transition-colors ${
        active
          ? 'border-accent/40 bg-accent/5'
          : 'border-line bg-surface-2 hover:border-line-strong'
      }`}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="font-mono text-[11px] text-fg-muted">
          {m.captured_at}
        </span>
        <span className="rounded-md border border-line bg-surface-1 px-1.5 py-0.5 font-mono text-[10px] text-fg-subtle">
          {m.source}
        </span>
      </div>
      <div className="mt-3 grid grid-cols-3 gap-2">
        {cells.map((c) => (
          <div key={c.label} className="rounded-md border border-line bg-surface-1 px-2 py-1.5">
            <div className="font-mono text-[9.5px] uppercase tracking-wide text-fg-subtle">
              {c.label}
            </div>
            <div className="mt-0.5 text-sm font-semibold tabular-nums text-fg">
              {c.value?.toLocaleString()}
            </div>
          </div>
        ))}
      </div>
      <p className="mt-2 text-[11px] leading-relaxed text-fg-subtle">{m.notes}</p>
    </button>
  );
}

function RefField({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-line bg-surface-2 px-3 py-2">
      <div className="font-mono text-[10px] uppercase tracking-wide text-fg-subtle">
        {label}
      </div>
      <div className="mt-0.5 break-all font-mono text-[12px] text-fg-muted">
        {value}
      </div>
    </div>
  );
}
