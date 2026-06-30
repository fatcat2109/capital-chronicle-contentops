// Capital Chronicle ContentOps V5 â€” Evidence Vault view.
// Forensic / compliance mode. Always rendered in dark-evidence theme (App
// forces it). Read-only audit surface. No network, storage, or credentials.

import { SubstackArticleStudioCard } from './SubstackArticleStudioCard';
import { useState } from 'react';
import { useApp } from '../state';
import { viewModel } from '../fixtures';
import {
  selectValidation,
  selectManualPilotTrailReconciliationAuditPacket,
  selectAuditInvariant,
  selectAuditContradiction,
} from '../selectors';
import { IconClock, IconFingerprint, IconBlock } from '../ui/icons';
import {
  EvidenceChip,
  Panel,
  SectionLabel,
  StatusChip,
  StatusDot,
  LockedAction,
} from '../ui/primitives';
import { manualPilotTrailReconciliationAuditPacket as auditPacket } from '../data/manualPilotTrailReconciliationAuditPacket';

type VaultTab = 'validation' | 'manual_pilot_audit';

export function EvidenceVault() {
  const { select, selected } = useApp();
  const [activeTab, setActiveTab] = useState<VaultTab>('validation');
  const packet = viewModel.evidence_packets[0];
  const v6Packet = viewModel.v6_operator_approval_evidence;

  const handleTabChange = (tab: VaultTab) => {
    setActiveTab(tab);
    if (tab === 'validation') {
      select(selectValidation(packet.validation_matrix[0], packet.id));
    } else {
      select(selectManualPilotTrailReconciliationAuditPacket(auditPacket));
    }
  };

  return (
    <div className="space-y-6">
      <SubstackArticleStudioCard mode="evidence" />
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
            {activeTab === 'validation' ? packet.task_label : auditPacket.task_label}
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <StatusChip
              status={activeTab === 'validation' ? packet.result : 'verified'}
              icon
            >
              {activeTab === 'validation' ? packet.result_label : 'verified local audit'}
            </StatusChip>
            <EvidenceChip>
              {activeTab === 'validation' ? packet.commit_ref : auditPacket.source_baseline_commit.slice(0, 12)}
            </EvidenceChip>
            <span className="flex items-center gap-1 font-mono text-[11px] text-fg-subtle">
              <IconClock className="h-3.5 w-3.5" />
              {activeTab === 'validation' ? packet.timestamp : 'local-only-audit'}
            </span>
          </div>
        </div>
      </header>

      {/* Tab Switcher */}
      <div role="tablist" aria-label="Evidence Vault sections" className="flex gap-1.5 border-b border-line pb-px">
        <button
          type="button"
          id="vault-tab-validation"
          role="tab"
          aria-selected={activeTab === 'validation'}
          onClick={() => handleTabChange('validation')}
          className={`border-b-2 px-4 py-2.5 text-sm font-medium transition-colors -mb-px ${
            activeTab === 'validation'
              ? 'border-accent text-fg font-semibold'
              : 'border-transparent text-fg-muted hover:text-fg'
          }`}
        >
          System Validation Ledger
        </button>
        <button
          type="button"
          id="vault-tab-audit"
          role="tab"
          aria-selected={activeTab === 'manual_pilot_audit'}
          onClick={() => handleTabChange('manual_pilot_audit')}
          className={`border-b-2 px-4 py-2.5 text-sm font-medium transition-colors -mb-px ${
            activeTab === 'manual_pilot_audit'
              ? 'border-accent text-fg font-semibold'
              : 'border-transparent text-fg-muted hover:text-fg'
          }`}
        >
          Manual Pilot Audit
        </button>
      </div>


      <Panel
        title="V6 operator evidence vault · fixture-only"
        subtitle={`${v6Packet.evidence_vault_items.length} evidence cards · ${v6Packet.sample_scope}`}
        actions={<StatusChip status="review">sample_fixture_only</StatusChip>}
      >
        <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
          {v6Packet.evidence_vault_items.map((item) => (
            <article key={item.evidence_id} className="rounded-lg border border-line bg-surface-2 p-3">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="font-mono text-[11px] uppercase tracking-wide text-fg-subtle">
                    {item.evidence_type}
                  </div>
                  <h3 className="mt-1 truncate text-sm font-semibold text-fg">{item.evidence_id}</h3>
                </div>
                <StatusChip status="verified">{item.display_status}</StatusChip>
              </div>
              <div className="mt-2 break-all font-mono text-[11px] text-fg-muted">
                {item.source_hash_or_preview_hash}
              </div>
              <p className="mt-2 text-xs text-fg-muted">{item.source_file_path}</p>
            </article>
          ))}
        </div>
        <div className="mt-4 rounded-lg border border-status-blocked/30 bg-status-blocked/5 p-3">
          <div className="font-mono text-[11px] font-bold uppercase tracking-wide text-status-blocked">
            Live pilot blocked · no runtime proof
          </div>
          <p className="mt-1 text-xs leading-relaxed text-fg-muted">
            Runtime proof is false; provider, network, browser session, env line,
            raw secret, live send, and dispatch behavior remain disabled.
          </p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {v6Packet.live_pilot_status_card.blockers.map((blocker) => (
              <EvidenceChip key={blocker}>{blocker}</EvidenceChip>
            ))}
          </div>
        </div>
      </Panel>

      {activeTab === 'validation' ? (
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
                        onClick={() => select(selectValidation(v, packet.id))}
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

            <Panel title="Forbidden scope â€” proven absent" subtitle="Static guarantees enforced for V5">
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
                      {e.actor} Â· {e.ref} Â· {e.timestamp}
                    </div>
                  </li>
                ))}
              </ul>
            </Panel>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.2fr_0.8fr]">
          <div className="space-y-6 min-w-0">
            {/* Manual Pilot Audit Overview */}
            <Panel
              title="Manual Pilot Audit Overview"
              subtitle="Verification status, hashes, baseline commit, and reference links"
              bodyClassName="p-4 space-y-4"
              actions={
                <button
                  type="button"
                  id="select-audit-packet-btn"
                  onClick={() => select(selectManualPilotTrailReconciliationAuditPacket(auditPacket))}
                  className={`rounded-lg border px-3 py-1 text-left transition-colors ${
                    selected?.kind === 'manual_pilot_audit_packet'
                      ? 'border-accent/40 bg-accent/5'
                      : 'border-line bg-surface-2 hover:border-line-strong'
                  }`}
                >
                  <span className="block font-mono text-[10.5px] font-semibold text-fg">
                    Audit SHA-256
                  </span>
                  <span className="font-mono text-[11px] text-fg-subtle">
                    {auditPacket.packet_hash.slice(0, 16)}...
                  </span>
                </button>
              }
            >
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                <MetricCard label="Audit Status" value="verified local (blocked/manual-only)" mono status="verified" />
                <MetricCard label="Contract Version" value={auditPacket.contract_version} mono status="neutral" />
                <MetricCard label="Contradictions" value={`${auditPacket.contradiction_results.contradictions_found.length}`} mono status="verified" />
              </div>

              <div className="rounded-xl border border-line bg-surface-2 p-4 space-y-2.5">
                <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle">
                  Compliance Metadata
                </div>
                <div className="grid gap-2">
                  <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-line bg-surface-1 px-3 py-2 text-sm">
                    <span className="font-semibold text-fg">Audit ID</span>
                    <span className="font-mono text-[11.5px] text-fg-muted break-all">{auditPacket.audit_id}</span>
                  </div>
                  <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-line bg-surface-1 px-3 py-2 text-sm">
                    <span className="font-semibold text-fg">Packet Hash</span>
                    <span className="font-mono text-[11.5px] text-fg-muted break-all">{auditPacket.packet_hash}</span>
                  </div>
                  <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-line bg-surface-1 px-3 py-2 text-sm">
                    <span className="font-semibold text-fg">Baseline Commit</span>
                    <span className="font-mono text-[11.5px] text-fg-muted break-all">{auditPacket.source_baseline_commit}</span>
                  </div>
                  <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-line bg-surface-1 px-3 py-2 text-sm">
                    <span className="font-semibold text-fg">Next Recommended Task</span>
                    <span className="font-mono text-[11.5px] text-fg-muted break-all">{auditPacket.next_recommended_task}</span>
                  </div>
                </div>
              </div>
            </Panel>

            {/* Invariants Validation Matrix */}
            <Panel
              title="Audit Invariant Results"
              subtitle="The 14 strict invariants verified against the manual pilot chain"
              bodyClassName="p-0 overflow-x-auto"
            >
              <table className="w-full min-w-[500px] border-collapse text-left text-sm">
                <thead>
                  <tr className="border-b border-line bg-surface-2 font-mono text-[10.5px] uppercase tracking-wider text-fg-muted">
                    <th className="px-4 py-3">Invariant Check</th>
                    <th className="px-4 py-3 text-center">Status</th>
                    <th className="px-4 py-3">Audit Scope</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {Object.entries(auditPacket.invariant_results).map(([name, passed]) => {
                    const isSelected = selected?.kind === 'audit_invariant' && selected.id === name;
                    return (
                      <tr
                        key={name}
                        id={`audit-invariant-row-${name}`}
                        onClick={() => select(selectAuditInvariant(name, passed))}
                        className={`cursor-pointer transition-colors hover:bg-surface-2/60 ${
                          isSelected ? 'bg-accent/5' : ''
                        }`}
                      >
                        <td className="px-4 py-3 font-mono text-[12px] font-semibold text-fg break-all">
                          {name}
                        </td>
                        <td className="px-4 py-3 text-center">
                          <StatusChip status={passed ? 'verified' : 'blocked'} nowrap>
                            {passed ? 'pass' : 'fail'}
                          </StatusChip>
                        </td>
                        <td className="px-4 py-3 text-[12.5px] text-fg-muted">
                          Local compliance audit constraint verification
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </Panel>

            {/* Audited Source Packets */}
            <Panel
              title="Audited Source Packets"
              subtitle="Underlying contract packets reconciled in the chain"
              bodyClassName="p-0 overflow-x-auto"
            >
              <table className="w-full min-w-[500px] border-collapse text-left text-sm">
                <thead>
                  <tr className="border-b border-line bg-surface-2 font-mono text-[10.5px] uppercase tracking-wider text-fg-muted">
                    <th className="px-4 py-3">Pipeline Stage</th>
                    <th className="px-4 py-3">Contract Version</th>
                    <th className="px-4 py-3">Packet Hash SHA-256</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {Object.entries(auditPacket.source_packets).map(([name, meta]) => (
                    <tr key={name} className="transition-colors hover:bg-surface-2/60">
                      <td className="px-4 py-3 font-mono text-[12px] font-semibold text-fg break-all">
                        {name}
                      </td>
                      <td className="px-4 py-3 font-mono text-[11.5px] text-fg-muted break-all">
                        {meta.contract_version}
                      </td>
                      <td className="px-4 py-3 font-mono text-[11.5px] text-fg-subtle break-all">
                        {meta.packet_hash}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Panel>
          </div>

          <div className="space-y-6 min-w-0">
            {/* Contradiction Checker */}
            <Panel
              title="Contradictions Detected"
              subtitle="Exceptions or conflicts found in the compliance chain"
              bodyClassName="p-4 space-y-3"
            >
              {auditPacket.contradiction_results.contradictions_found.length === 0 ? (
                <div className="rounded-xl border border-status-verified/20 bg-status-verified/5 p-4 text-center">
                  <div className="font-mono text-[11px] font-bold uppercase tracking-wider text-status-verified flex items-center justify-center gap-1.5">
                    No Contradictions
                  </div>
                  <p className="mt-1 text-xs text-fg-muted leading-relaxed">
                    Audit chain is internally consistent. All safety flags align.
                  </p>
                </div>
              ) : (
                <div className="space-y-2">
                  {auditPacket.contradiction_results.contradictions_found.map((c, i) => {
                    const active = selected?.kind === 'audit_contradiction' && selected.id === `contradiction-${i}`;
                    return (
                      <button
                        key={i}
                        type="button"
                        onClick={() => select(selectAuditContradiction(c, i))}
                        className={`w-full text-left rounded-lg border p-3 transition-colors ${
                          active ? 'border-accent/40 bg-accent/5' : 'border-status-blocked/20 bg-status-blocked/5'
                        }`}
                      >
                        <div className="font-semibold text-status-blocked text-xs">Contradiction #{i + 1}</div>
                        <p className="mt-1 font-mono text-[11px] text-fg leading-relaxed break-all">{c}</p>
                      </button>
                    );
                  })}
                </div>
              )}
            </Panel>

            {/* Missing Evidence Required */}
            <Panel
              title="Missing Evidence (Pending)"
              subtitle="Prerequisites remaining empty until manual pilot completion"
              bodyClassName="p-4 space-y-3"
            >
              <div className="rounded-xl border border-status-review/20 bg-status-review/5 p-3.5">
                <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-status-review flex items-center gap-1.5">
                  Reconciliation Blocked
                </div>
                <p className="mt-1.5 text-xs text-fg-muted leading-relaxed">
                  Compliance index requires off-system manual entry of verification evidence.
                </p>
              </div>

              <div className="space-y-2">
                {auditPacket.missing_evidence_results.required_missing.map((item) => (
                  <div
                    key={item}
                    className="flex items-center gap-2.5 rounded-lg border border-line bg-surface-2 px-3 py-2"
                  >
                    <StatusDot status="review" />
                    <span className="font-mono text-[12px] text-fg-muted">{item}</span>
                  </div>
                ))}
              </div>
            </Panel>

            {/* Disabled Live Actions */}
            <Panel
              title="Disabled Live Action Proof"
              subtitle="Rigid bounds enforced for manual-only assurance"
              bodyClassName="p-4"
            >
              <div className="mb-4 flex items-start gap-2.5 rounded-xl border border-status-blocked/20 bg-status-blocked/5 p-3">
                <IconBlock className="mt-0.5 h-3.5 w-3.5 shrink-0 text-status-blocked" />
                <p className="text-[12px] leading-relaxed text-fg-muted">
                  Audit confirms all platform publishing, account connection, credential sync, and scheduling endpoints are fully disabled.
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

            {/* Forensic References */}
            <Panel
              title="Evidence References"
              subtitle="Files and JSON targets on local disk"
              bodyClassName="p-4 space-y-3"
            >
              <div>
                <SectionLabel>Forensic MD Report</SectionLabel>
                <div className="font-mono text-[11px] text-fg-muted break-all rounded border border-line bg-surface-2 p-2.5">
                  docs/automation/0175AA/v5_manual_pilot_trail_reconciliation_audit_contract.md
                </div>
              </div>
              <div>
                <SectionLabel>Compliance JSON Packet</SectionLabel>
                <div className="font-mono text-[11px] text-fg-muted break-all rounded border border-line bg-surface-2 p-2.5">
                  docs/automation/0175AA/v5_manual_pilot_trail_reconciliation_audit_contract_packet.json
                </div>
              </div>
            </Panel>
          </div>
        </div>
      )}
    </div>
  );
}

function MetricCard({
  label,
  value,
  mono,
  status,
}: {
  label: string;
  value: string;
  mono?: boolean;
  status?: 'verified' | 'review' | 'blocked' | 'neutral';
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
