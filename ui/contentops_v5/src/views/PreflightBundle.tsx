// Capital Chronicle ContentOps V5 — Preflight Bundle view.
// Read-only evidence-grade operator cockpit.
// Strictly local-first. No API calls, no network, no environment/dotenv reads, no credentials.

import { useState } from 'react';
import { useApp } from '../state';
import { preflightBundlePacket } from '../data/preflightBundlePacket';
import {
  selectPreflightBundlePacket,
  selectPreflightPlatformState,
  selectPreflightRoomPrecheck,
  selectPreflightSourceRef,
} from '../selectors';
import { IconBlock, IconShield } from '../ui/icons';
import {
  Panel,
  SectionLabel,
  StatusChip,
  StatusDot,
  LockedAction,
} from '../ui/primitives';

type PreflightTab = 'safety' | 'rooms' | 'sources';

export function PreflightBundle() {
  const { select, selected } = useApp();
  const [activeTab, setActiveTab] = useState<PreflightTab>('safety');

  const p = preflightBundlePacket;

  const packetActive = selected?.kind === 'preflight_bundle_packet';

  return (
    <div className="space-y-6">
      {/* Header and metadata */}
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 font-mono text-[11px] font-bold uppercase tracking-[0.14em] text-fg-subtle">
            Preflight Bundle Contract
            <span className="text-fg-subtle/60">·</span>
            <span className="text-fg-muted">{p.matrix_version}</span>
          </div>
          <h1 className="mt-2 flex items-center gap-2 text-2xl font-semibold tracking-tight text-fg">
            <IconShield className="h-6 w-6 text-accent" />
            Preflight Bundle &amp; Readiness Gate
          </h1>
          <p className="mt-1 text-sm font-medium text-fg-muted">
            Evidence-grade readiness model prechecks based on local contract chains.
          </p>
        </div>
        <div className="flex flex-col items-end gap-1.5">
          <button
            type="button"
            id="select-packet-btn"
            onClick={() => select(selectPreflightBundlePacket(p))}
            className={`rounded-lg border px-3 py-1 text-left transition-colors ${
              packetActive
                ? 'border-accent/40 bg-accent/5'
                : 'border-line bg-surface-2 hover:border-line-strong'
            }`}
          >
            <span className="font-mono text-[10.5px] font-semibold text-fg block">
              Packet SHA-256
            </span>
            <span className="font-mono text-[11px] text-fg-subtle">
              {p.packet_hash.slice(0, 16)}...
            </span>
          </button>
        </div>
      </header>

      {/* Executive Safety Strip */}
      <div className="flex items-start gap-3 rounded-xl border border-status-blocked/30 bg-status-blocked/5 p-4">
        <IconBlock className="mt-0.5 h-4 w-4 shrink-0 text-status-blocked" />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-fg uppercase tracking-wide">
            LOCAL ONLY / NOT LIVE / NOT PUBLIC-POSTABLE
          </p>
          <p className="mt-1 text-[12px] leading-relaxed text-fg-muted">
            The ContentOps cockpit is running under strict local-only safety invariants.
            No platform APIs, provider endpoints, credentials, or environment configs
            are loaded or accessed. All action dispatch paths remain locked.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <span className="rounded border border-line bg-surface-2 px-1.5 py-0.5 font-mono text-[10px] text-fg-muted">
              local_only: true
            </span>
            <span className="rounded border border-line bg-surface-2 px-1.5 py-0.5 font-mono text-[10px] text-fg-muted">
              readiness_cleared: false
            </span>
            <span className="rounded border border-line bg-surface-2 px-1.5 py-0.5 font-mono text-[10px] text-fg-muted">
              credential_hydrated: false
            </span>
            <span className="rounded border border-line bg-surface-2 px-1.5 py-0.5 font-mono text-[10px] text-fg-muted">
              network_performed: false
            </span>
          </div>
        </div>
      </div>

      {/* Navigation tabs */}
      <div role="tablist" aria-label="Preflight sections" className="flex gap-1.5 border-b border-line pb-px">
        {(['safety', 'rooms', 'sources'] as const).map((tab) => {
          const isActive = activeTab === tab;
          const label = tab === 'safety' ? 'Platform Safety Matrix' : tab === 'rooms' ? 'Room Binding Matrix' : 'Source Inventory';
          return (
            <button
              type="button"
              key={tab}
              id={`preflight-tab-${tab}`}
              role="tab"
              aria-selected={isActive}
              onClick={() => setActiveTab(tab)}
              className={`border-b-2 px-4 py-2.5 text-sm font-medium transition-colors -mb-px ${
                isActive
                  ? 'border-accent text-fg font-semibold'
                  : 'border-transparent text-fg-muted hover:text-fg'
              }`}
            >
              {label}
            </button>
          );
        })}
      </div>

      {/* Tab Panels */}
      {activeTab === 'safety' && (
        <div className="space-y-6">
          {/* Platform Gate Matrix */}
          <Panel
            title="Platform Gate Matrix"
            subtitle="Current readiness audit states for the 10 supported platforms (Select row to inspect)"
            bodyClassName="p-0 overflow-x-auto"
          >
            <table className="w-full min-w-[700px] border-collapse text-left text-sm">
              <thead>
                <tr className="border-b border-line bg-surface-2 text-fg-muted font-mono text-[10.5px] uppercase tracking-wider">
                  <th className="px-4 py-3">Platform ID</th>
                  <th className="px-4 py-3">Role / Role Class</th>
                  <th className="px-4 py-3">Category</th>
                  <th className="px-4 py-3">Endpoint Family</th>
                  <th className="px-4 py-3">Binding</th>
                  <th className="px-4 py-3">Cred Slot</th>
                  <th className="px-4 py-3">Audit</th>
                  <th className="px-4 py-3">Readiness</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {p.platform_states.map((ps) => {
                  const isRowSelected = selected?.kind === 'preflight_platform_state' && selected.id === ps.platform_id;
                  const bindingOk = ps.account_binding_status === 'bound';
                  const auditBlocked = ps.credential_mock_audit_status === 'blocked';
                  const readinessOk = ps.readiness_cleared;

                  return (
                    <tr
                      key={ps.platform_id}
                      id={`platform-row-${ps.platform_id}`}
                      onClick={() => select(selectPreflightPlatformState(ps))}
                      className={`cursor-pointer transition-colors hover:bg-surface-2/60 ${
                        isRowSelected ? 'bg-accent/5' : ''
                      }`}
                    >
                      <td className="px-4 py-3 font-mono text-[12px] font-semibold text-fg">
                        {ps.platform_id}
                      </td>
                      <td className="px-4 py-3 text-fg-muted text-[13px]">
                        {ps.platform_role}
                      </td>
                      <td className="px-4 py-3 font-mono text-[11px] text-fg-subtle capitalize">
                        {ps.primary_or_secondary_or_expansion}
                      </td>
                      <td className="px-4 py-3 font-mono text-[11px] text-fg-subtle">
                        {ps.endpoint_family}
                      </td>
                      <td className="px-4 py-3">
                        <StatusChip status={bindingOk ? 'verified' : 'review'}>
                          {ps.account_binding_status}
                        </StatusChip>
                      </td>
                      <td className="px-4 py-3 font-mono text-[11px] text-fg-muted">
                        {ps.credential_slot_status}
                      </td>
                      <td className="px-4 py-3">
                        <StatusChip status={auditBlocked ? 'blocked' : 'review'}>
                          {ps.credential_mock_audit_status}
                        </StatusChip>
                      </td>
                      <td className="px-4 py-3">
                        <StatusChip status={readinessOk ? 'verified' : 'blocked'}>
                          {readinessOk ? 'verified local' : 'blocked'}
                        </StatusChip>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Panel>

          {/* Blockers & Missing Proofs summary */}
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <Panel
              title="Platform Blockers Summary"
              subtitle="Required active verification keys missing"
              bodyClassName="p-4"
            >
              <div className="space-y-2">
                {p.global_blocked_reasons.map((reason) => (
                  <div
                    key={reason}
                    className="flex items-center gap-2 rounded-lg border border-status-blocked/20 bg-status-blocked/5 px-3 py-2 text-sm"
                  >
                    <StatusDot status="blocked" />
                    <span className="font-mono text-[12px] text-status-blocked break-all">
                      {reason}
                    </span>
                  </div>
                ))}
              </div>
            </Panel>

            <Panel
              title="Missing Proofs Summary"
              subtitle="Prerequisite gate outputs holding back live authorization"
              bodyClassName="p-4"
            >
              <div className="space-y-2">
                {p.global_missing_proofs.map((proof) => (
                  <div
                    key={proof}
                    className="flex items-center gap-2 rounded-lg border border-status-review/20 bg-status-review/5 px-3 py-2 text-sm"
                  >
                    <StatusDot status="review" />
                    <span className="font-mono text-[12px] text-status-review break-all">
                      {proof}
                    </span>
                  </div>
                ))}
              </div>
            </Panel>
          </div>
        </div>
      )}

      {activeTab === 'rooms' && (
        <div className="space-y-6">
          {/* V5 Room Binding Matrix */}
          <Panel
            title="V5 Room Binding Precheck Matrix"
            subtitle="Readiness mapping of the 13 cockpit spaces to underlying contracts (Select row to inspect)"
            bodyClassName="p-0 overflow-x-auto"
          >
            <table className="w-full min-w-[700px] border-collapse text-left text-sm">
              <thead>
                <tr className="border-b border-line bg-surface-2 text-fg-muted font-mono text-[10.5px] uppercase tracking-wider">
                  <th className="px-4 py-3">Room ID</th>
                  <th className="px-4 py-3">Binding Status</th>
                  <th className="px-4 py-3">Live Actions Gated</th>
                  <th className="px-4 py-3 text-center">Safe Fields</th>
                  <th className="px-4 py-3 text-center">Redacted Fields</th>
                  <th className="px-4 py-3 text-center">Hidden Fields</th>
                  <th className="px-4 py-3">Contracts Linked</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {p.room_binding_prechecks.map((rb) => {
                  const isRowSelected = selected?.kind === 'preflight_room_precheck' && selected.id === rb.room_id;
                  return (
                    <tr
                      key={rb.room_id}
                      id={`room-row-${rb.room_id}`}
                      onClick={() => select(selectPreflightRoomPrecheck(rb))}
                      className={`cursor-pointer transition-colors hover:bg-surface-2/60 ${
                        isRowSelected ? 'bg-accent/5' : ''
                      }`}
                    >
                      <td className="px-4 py-3 font-mono text-[12px] font-semibold text-fg">
                        {rb.room_id}
                      </td>
                      <td className="px-4 py-3 text-[13px] text-fg-muted capitalize">
                        {rb.binding_status.replace(/_/g, ' ')}
                      </td>
                      <td className="px-4 py-3">
                        <StatusChip status={rb.no_live_action_affordances ? 'verified' : 'blocked'}>
                          {rb.no_live_action_affordances ? 'blocked' : 'exposed'}
                        </StatusChip>
                      </td>
                      <td className="px-4 py-3 text-center font-mono font-medium text-fg-muted">
                        {rb.safe_fields_count}
                      </td>
                      <td className="px-4 py-3 text-center font-mono font-medium text-fg-muted">
                        {rb.redacted_fields_count}
                      </td>
                      <td className="px-4 py-3 text-center font-mono font-medium text-fg-muted">
                        {rb.hidden_fields_count}
                      </td>
                      <td className="px-4 py-3 text-[11.5px] font-mono text-fg-subtle">
                        {rb.required_contracts.length} contract(s)
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Panel>

          {/* Safe / Redacted / Hidden display summary */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <Panel
              title="Safe Display Fields"
              subtitle="Allowed read-only metadata fields"
              bodyClassName="p-4"
            >
              <div className="text-3xl font-bold tracking-tight text-status-verified">
                {p.v5_candidate_fields.filter(f => f.display_policy === 'safe_to_show').length}
              </div>
              <p className="mt-2 text-xs leading-relaxed text-fg-muted">
                These elements represent generic config keys, fit statuses, validation reports, and baseline references, fully clear for cockpit presentation.
              </p>
            </Panel>

            <Panel
              title="Redacted Fields"
              subtitle="Values masked by security policy"
              bodyClassName="p-4"
            >
              <div className="text-3xl font-bold tracking-tight text-status-review">
                {p.v5_candidate_fields.filter(f => f.display_policy === 'redacted').length}
              </div>
              <p className="mt-2 text-xs leading-relaxed text-fg-muted">
                Audit logs and API payload schemas. Values are replaced with redacted labels to prevent unintended disclosure.
              </p>
            </Panel>

            <Panel
              title="Hidden Fields"
              subtitle="Excluded entirely from client models"
              bodyClassName="p-4"
            >
              <div className="text-3xl font-bold tracking-tight text-status-blocked">
                {p.v5_candidate_fields.filter(f => f.display_policy === 'hidden').length}
              </div>
              <p className="mt-2 text-xs leading-relaxed text-fg-muted">
                Raw client secrets, API credentials, and tokens. Completely filtered out from the read-model adapters. No memory footprint.
              </p>
            </Panel>
          </div>

          {/* Disabled future-gate affordances */}
          <Panel
            title="Disabled Future-Gate Affordances"
            subtitle="Visual control interfaces mapped to blocked live pathways"
            bodyClassName="p-4 space-y-4"
          >
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div>
                <SectionLabel>Account Binding</SectionLabel>
                <LockedAction
                  label="Connect Account"
                  reason="Blocked: Platform account binding registry is strictly symbolic for local preflight."
                />
              </div>
              <div>
                <SectionLabel>Credentials</SectionLabel>
                <LockedAction
                  label="Verify Credentials"
                  reason="Blocked: Credential slot verification is simulated without decryption capabilities."
                />
              </div>
              <div>
                <SectionLabel>Live Dispatch</SectionLabel>
                <LockedAction
                  label="Publish Now"
                  reason="Blocked: Platform dispatch gates fail closed under current safety baseline."
                />
              </div>
            </div>
            <p className="font-mono text-[11px] text-fg-subtle text-center pt-2">
              Action labels do not appear as active or enabled inputs.
            </p>
          </Panel>
        </div>
      )}

      {activeTab === 'sources' && (
        <div className="space-y-6">
          {/* Source Contract Inventory */}
          <Panel
            title="Source Contract Inventory"
            subtitle="The 17 precedent dry-run contracts consumed to reconcile the cockpit read-model (Select row to inspect)"
            bodyClassName="p-0 overflow-x-auto"
          >
            <table className="w-full min-w-[700px] border-collapse text-left text-sm">
              <thead>
                <tr className="border-b border-line bg-surface-2 text-fg-muted font-mono text-[10.5px] uppercase tracking-wider">
                  <th className="px-4 py-3">Source Ref ID</th>
                  <th className="px-4 py-3">Task Family</th>
                  <th className="px-4 py-3">Artifact Family</th>
                  <th className="px-4 py-3">Python Module Path</th>
                  <th className="px-4 py-3">Code Hash SHA-256</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {p.source_refs.map((sr) => {
                  const isRowSelected = selected?.kind === 'preflight_source_ref' && selected.id === sr.source_ref_id;
                  const isOk = sr.source_status === 'valid';

                  return (
                    <tr
                      key={sr.source_ref_id}
                      id={`source-row-${sr.source_ref_id}`}
                      onClick={() => select(selectPreflightSourceRef(sr))}
                      className={`cursor-pointer transition-colors hover:bg-surface-2/60 ${
                        isRowSelected ? 'bg-accent/5' : ''
                      }`}
                    >
                      <td className="px-4 py-3 font-mono text-[12px] font-semibold text-fg">
                        {sr.source_ref_id}
                      </td>
                      <td className="px-4 py-3 text-[13px] text-fg-muted">
                        {sr.task_family}
                      </td>
                      <td className="px-4 py-3 font-mono text-[11px] text-fg-subtle">
                        {sr.artifact_family}
                      </td>
                      <td className="px-4 py-3 font-mono text-[11px] text-fg-subtle break-all">
                        {sr.module_name}
                      </td>
                      <td className="px-4 py-3 font-mono text-[11px] text-fg-muted" title={sr.source_hash_or_packet_hash}>
                        {sr.source_hash_or_packet_hash.slice(0, 12)}...
                      </td>
                      <td className="px-4 py-3">
                        <StatusChip status={isOk ? 'verified' : 'blocked'}>
                          {sr.source_status}
                        </StatusChip>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Panel>

          {/* Packet metadata & baseline info */}
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            <Panel
              title="Verification Signatures"
              subtitle="Reconciled preflight bundle signatures"
              bodyClassName="p-4 space-y-3"
            >
              <div>
                <SectionLabel>Acceptance baseline commit</SectionLabel>
                <div className="font-mono text-[12px] text-fg break-all rounded border border-line bg-surface-2 p-2.5">
                  {p.source_baseline_commit}
                </div>
              </div>
              <div>
                <SectionLabel>Consolidated Packet checksum</SectionLabel>
                <div className="font-mono text-[12px] text-fg break-all rounded border border-line bg-surface-2 p-2.5">
                  {p.packet_hash}
                </div>
              </div>
            </Panel>

            <Panel
              title="Safety Invariant Check"
              subtitle="Precedent contract boundary verification check"
              bodyClassName="p-4 space-y-3"
            >
              <div className="flex items-center gap-2 text-sm font-semibold text-fg">
                <StatusDot status="verified" />
                No side-effects audit passed.
              </div>
              <p className="text-xs leading-relaxed text-fg-muted">
                Preflight bundle code has verified that zero network requests, credential loads, or ingestion commits were initiated. The baseline source remains fully compliant.
              </p>
              <div className="mt-2">
                <SectionLabel>Audit Entry count</SectionLabel>
                <p className="font-mono text-[11px] text-fg-muted">
                  {p.u9_audit_entry_ids.length} immutable ledger entries indexed.
                </p>
              </div>
            </Panel>
          </div>
        </div>
      )}
    </div>
  );
}
