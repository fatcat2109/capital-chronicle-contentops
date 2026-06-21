import { useApp } from '../state';
import { ViewId } from '../types';
import { selectRunbookStep, getStepLabel } from '../selectors';
import { operatorRunbookIndexPacket as runbook } from '../data/operatorRunbookIndexPacket';
import { Panel, StatusChip, StatusDot, LockedAction, SectionLabel } from '../ui/primitives';
import { IconClock, IconFingerprint, IconBlock } from '../ui/icons';

export function OperatorRunbookIndex() {
  const { select, selected, setView } = useApp();

  function getStatusLabel(status: string) {
    if (status === 'verified') {
      return (
        <StatusChip status="verified" icon>
          verified local
        </StatusChip>
      );
    }
    if (status === 'blocked') {
      return (
        <StatusChip status="blocked" icon>
          blocked
        </StatusChip>
      );
    }
    return (
      <StatusChip status="review" icon>
        review required
      </StatusChip>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header and Title Banner */}
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 font-mono text-[11px] font-bold uppercase tracking-[0.14em] text-fg-subtle">
            <IconFingerprint className="h-4 w-4 text-accent" />
            Forensic Operator Mode
          </div>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight text-fg">
            Local Operator Runbook
          </h1>
          <div className="mt-1 break-all font-mono text-[12px] text-fg-muted">
            {runbook.task_label}
          </div>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-status-review/20 bg-status-review/5 px-2.5 py-1 text-[10.5px] font-mono font-bold uppercase tracking-wider text-status-review">
              LOCAL_PRE_ALPHA
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-full border border-status-verified/20 bg-status-verified/5 px-2.5 py-1 text-[10.5px] font-mono font-bold uppercase tracking-wider text-status-verified">
              LOCAL ONLY
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-full border border-status-blocked/20 bg-status-blocked/5 px-2.5 py-1 text-[10.5px] font-mono font-bold uppercase tracking-wider text-status-blocked">
              NOT LIVE
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-full border border-status-blocked/20 bg-status-blocked/5 px-2.5 py-1 text-[10.5px] font-mono font-bold uppercase tracking-wider text-status-blocked">
              NOT PUBLIC-POSTABLE
            </span>
            <span className="flex items-center gap-1 font-mono text-[11px] text-fg-subtle ml-1">
              <IconClock className="h-3.5 w-3.5" />
              local-only-audit
            </span>
          </div>
        </div>
      </header>

      {/* Main Grid View */}
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        {/* Left Column: Map and Cards */}
        <div className="space-y-6 min-w-0">
          {/* Workflow Map */}
          <Panel
            title="Local Pilot Workflow Map"
            subtitle="Sequential validation pipeline of ContentOps V5"
            bodyClassName="p-4"
          >
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between overflow-x-auto">
              {runbook.runbook_steps.map((s, index) => {
                const isActive = selected?.kind === 'runbook_step' && selected.id === s.step_id;
                return (
                  <div key={s.step_id} className="flex flex-1 items-center gap-2">
                    <button
                      type="button"
                      id={`runbook-map-step-${s.step_id}`}
                      onClick={() => select(selectRunbookStep(s))}
                      className={`flex flex-col items-start gap-1 p-3 rounded-lg border text-left transition-all w-full ${
                        isActive
                          ? 'border-accent bg-accent/5 ring-1 ring-accent/30'
                          : 'border-line bg-surface-2 hover:border-line-strong'
                      }`}
                    >
                      <span className="font-mono text-[9.5px] font-bold text-fg-subtle uppercase">
                        Step 0{index + 1}
                      </span>
                      <span className="text-[11.5px] font-semibold text-fg leading-tight">
                        {getStepLabel(s.step_id)}
                      </span>
                      <span className="font-mono text-[9px] text-fg-subtle break-all">
                        ({s.step_id})
                      </span>
                      <span className="mt-0.5 font-mono text-[9px] uppercase font-bold">
                        {s.status === 'verified' ? (
                          <span className="text-status-verified">verified local</span>
                        ) : s.status === 'blocked' ? (
                          <span className="text-status-blocked">blocked</span>
                        ) : (
                          <span className="text-status-review">review</span>
                        )}
                      </span>
                    </button>
                    {index < runbook.runbook_steps.length - 1 && (
                      <span className="hidden text-fg-subtle font-bold text-lg md:block">→</span>
                    )}
                  </div>
                );
              })}
            </div>
          </Panel>

          {/* Step Detail Cards */}
          <div className="space-y-6">
            <h2 className="text-base font-semibold tracking-tight text-fg font-mono uppercase">
              Pipeline Stage Specifications
            </h2>
            {runbook.runbook_steps.map((s, index) => {
              const isSelected = selected?.kind === 'runbook_step' && selected.id === s.step_id;
              return (
                <div
                  key={s.step_id}
                  id={`runbook-step-card-${s.step_id}`}
                  className={`rounded-xl border p-5 transition-all space-y-4 ${
                    isSelected ? 'border-accent bg-accent/5' : 'border-line bg-surface-1'
                  }`}
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <div className="font-mono text-[10.5px] font-bold text-fg-subtle uppercase">
                        Step 0{index + 1} · {s.step_id}
                      </div>
                      <h3 className="mt-1 text-base font-semibold text-fg leading-snug">
                        {getStepLabel(s.step_id)}
                      </h3>
                    </div>
                    <div className="flex items-center gap-2">
                      {getStatusLabel(s.status)}
                    </div>
                  </div>

                  <p className="text-sm text-fg-muted leading-relaxed">
                    {s.operator_meaning}
                  </p>

                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="rounded-lg bg-surface-2 p-3.5 border border-line">
                      <div className="font-mono text-[10px] font-bold uppercase tracking-wider text-fg-subtle">
                        Human Capabilities
                      </div>
                      <p className="mt-1.5 text-xs text-fg-muted leading-relaxed">
                        {s.what_human_can_do}
                      </p>
                    </div>
                    <div className="rounded-lg bg-surface-2 p-3.5 border border-line">
                      <div className="font-mono text-[10px] font-bold uppercase tracking-wider text-fg-subtle">
                        System Limitations
                      </div>
                      <p className="mt-1.5 text-xs text-fg-muted leading-relaxed">
                        {s.what_system_cannot_do}
                      </p>
                    </div>
                  </div>

                  {s.blocked_reasons.length > 0 && (
                    <div className="rounded-lg border border-status-blocked/20 bg-status-blocked/5 p-3.5 space-y-1.5">
                      <div className="font-mono text-[10px] font-bold uppercase text-status-blocked tracking-wide">
                        Blockers Detected
                      </div>
                      <ul className="space-y-1">
                        {s.blocked_reasons.map((r) => (
                          <li key={r} className="font-mono text-[11.5px] text-fg-muted break-all">
                            • {r}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {s.missing_evidence.length > 0 && (
                    <div className="rounded-lg border border-status-review/20 bg-status-review/5 p-3.5 space-y-1.5">
                      <div className="font-mono text-[10px] font-bold uppercase text-status-review tracking-wide">
                        Missing Evidence
                      </div>
                      <ul className="space-y-1">
                        {s.missing_evidence.map((m) => (
                          <li key={m} className="font-mono text-[11.5px] text-fg-muted break-all">
                            • {m}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-line">
                    <div className="min-w-0">
                      <span className="font-mono text-[10px] uppercase text-fg-subtle">Next Safe Step: </span>
                      <span className="font-mono text-[11.5px] text-fg break-all font-semibold">{s.next_safe_step}</span>
                    </div>
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => select(selectRunbookStep(s))}
                        className={`rounded-lg border px-3 py-1.5 text-xs font-semibold transition-colors ${
                          isSelected
                            ? 'border-accent bg-accent/10 text-fg'
                            : 'border-line bg-surface-2 text-fg hover:border-line-strong'
                        }`}
                      >
                        Inspect evidence
                      </button>
                      <button
                        type="button"
                        onClick={() => setView(s.view_id as ViewId)}
                        className="rounded-lg bg-fg px-3 py-1.5 text-xs font-semibold text-bg hover:opacity-90 transition-opacity"
                      >
                        Open local view
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: Blocker Summary, references, locked actions */}
        <div className="space-y-6 min-w-0">
          {/* Operations Blocker Summary */}
          <Panel
            title="Operational Blocker Summary"
            subtitle="Local execution constraints and pending items"
            bodyClassName="p-4 space-y-3"
          >
            <div className="rounded-xl border border-status-blocked/20 bg-status-blocked/5 p-3.5">
              <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-status-blocked">
                Reconciliation Blocked
              </div>
              <p className="mt-1 text-xs text-fg-muted leading-relaxed">
                Step 4 (manual_pilot_reconciliation) is currently blocked from resolving until manual publish indicators are populated.
              </p>
            </div>
            <div className="rounded-xl border border-status-review/20 bg-status-review/5 p-3.5 space-y-2">
              <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-status-review">
                Pending Offline Evidence
              </div>
              <ul className="space-y-1.5">
                {['manual_publish_url', 'manual_publish_timestamp', 'manual_metrics_snapshot'].map((e) => (
                  <li key={e} className="flex items-center gap-2">
                    <StatusDot status="review" />
                    <span className="font-mono text-[11.5px] text-fg-muted break-all">{e}</span>
                  </li>
                ))}
              </ul>
            </div>
          </Panel>

          {/* References */}
          <Panel
            title="Artifact Evidence References"
            subtitle="Local compliance documents on disk"
            bodyClassName="p-4 space-y-3"
          >
            <div>
              <SectionLabel>Forensic MD Runbook Report</SectionLabel>
              <div className="font-mono text-[11px] text-fg-muted break-all rounded border border-line bg-surface-2 p-2.5">
                docs/automation/0175AD/v5_local_operator_runbook_index_contract.md
              </div>
            </div>
            <div>
              <SectionLabel>Compliance JSON Packet</SectionLabel>
              <div className="font-mono text-[11px] text-fg-muted break-all rounded border border-line bg-surface-2 p-2.5">
                docs/automation/0175AD/v5_local_operator_runbook_index_contract_packet.json
              </div>
            </div>
            <div>
              <SectionLabel>Baseline Commit SHA</SectionLabel>
              <div className="font-mono text-[11px] text-fg-muted break-all rounded border border-line bg-surface-2 p-2.5">
                {runbook.source_baseline_commit}
              </div>
            </div>
          </Panel>

          {/* Enforced Boundary Lock */}
          <Panel
            title="Enforced Execution Boundary"
            subtitle="Verification of blocked live platform actions"
            bodyClassName="p-4"
          >
            <div className="mb-4 flex items-start gap-2.5 rounded-xl border border-status-blocked/20 bg-status-blocked/5 p-3">
              <IconBlock className="mt-0.5 h-3.5 w-3.5 shrink-0 text-status-blocked" />
              <p className="text-[12px] leading-relaxed text-fg-muted">
                Runbook index confirms all automated publishing, scheduler execution, credentials hydration, and platform sync capabilities are locked.
              </p>
            </div>
            <div className="grid gap-2 sm:grid-cols-2">
              {['Publish', 'Send', 'Schedule', 'Connect account', 'Verify credentials', 'Sync platform', 'Live dispatch'].map((label) => (
                <div key={label}>
                  <LockedAction
                    label={label}
                    reason="Audit boundary lock: live dispatch forbidden"
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
