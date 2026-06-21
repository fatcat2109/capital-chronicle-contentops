// Capital Chronicle ContentOps V5 — Content Inventory view.
// Local-first content table. No network, no storage, no credentials.

import { useMemo, useState } from 'react';
import { useApp } from '../state';
import { viewModel } from '../fixtures';
import { Panel, SectionLabel, StatusChip, StatusDot } from '../ui/primitives';
import {
  selectContentItem,
  LANE_LABEL,
  selectLaneCArtifactIntakeValidationPacket,
  selectLaneCArtifactIntakeCandidate,
} from '../selectors';
import { IconSearch } from '../ui/icons';
import type { StatusKind } from '../types';
import { laneCArtifactIntakePacket as laneCPacket } from '../data/laneCArtifactIntakePacket';

const LANE_FILTERS: { id: string; label: string }[] = [
  { id: 'all', label: 'All lanes' },
  { id: 'A_pre_alpha', label: 'Pre-alpha' },
  { id: 'B_grounded_news', label: 'Grounded news' },
  { id: 'C_artifact_backed', label: 'Artifact-backed' },
];

export function ContentInventory() {
  const { select, selected } = useApp();
  const items = viewModel.content_items;
  const [lane, setLane] = useState<string>('all');
  const [query, setQuery] = useState('');

  const filtered = useMemo(
    () =>
      items.filter((it) => {
        const laneOk = lane === 'all' || it.lane === lane;
        const q = query.trim().toLowerCase();
        const queryOk =
          !q ||
          it.title.toLowerCase().includes(q) ||
          it.id.toLowerCase().includes(q);
        return laneOk && queryOk;
      }),
    [items, lane, query],
  );

  return (
    <div className="space-y-6">
      <header>
        <div className="font-mono text-[11px] font-bold uppercase tracking-[0.14em] text-fg-subtle">
          Governance · editorial objects
        </div>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight text-fg">
          Content Inventory
        </h1>
        <p className="mt-1 max-w-2xl text-sm leading-relaxed text-fg-muted">
          Status, citations, media, and approval state across all content
          lanes. Select a row to inspect its full provenance.
        </p>
      </header>

      {/* Status summary — lane/status composition at a glance. */}
      <div className="grid grid-cols-3 gap-3">
        {(['verified', 'review', 'blocked'] as StatusKind[]).map((st) => {
          const count = items.filter((i) => i.status === st).length;
          const label =
            st === 'verified'
              ? 'Review passed'
              : st === 'review'
                ? 'Awaiting review'
                : 'Blocked';
          return (
            <div
              key={st}
              className="flex items-center justify-between gap-2 rounded-xl border border-line bg-surface-1 px-4 py-3 shadow-card"
            >
              <span className="flex items-center gap-2 text-[12px] text-fg-muted">
                <StatusDot status={st} />
                {label}
              </span>
              <span className="font-mono text-xl font-semibold text-fg">
                {count}
              </span>
            </div>
          );
        })}
      </div>

      {/* Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-1.5">
          {LANE_FILTERS.map((f) => (
            <button
              key={f.id}
              type="button"
              id={`lane-filter-${f.id}`}
              onClick={() => setLane(f.id)}
              className={`rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${
                lane === f.id
                  ? 'border-accent/50 bg-accent/10 text-accent'
                  : 'border-line bg-surface-1 text-fg-muted hover:border-line-strong hover:text-fg'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
        <label className="relative flex items-center" htmlFor="inventory-search">
          <IconSearch className="pointer-events-none absolute left-2.5 h-4 w-4 text-fg-subtle" />
          <input
            id="inventory-search"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search title or ID…"
            className="w-56 rounded-md border border-line bg-surface-1 py-1.5 pl-8 pr-3 text-sm text-fg placeholder:text-fg-subtle focus:border-accent/50 focus:outline-none"
          />
        </label>
      </div>

      <Panel bodyClassName="p-0">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-line bg-surface-2 text-left">
                {['ID', 'Title', 'Lane', 'Status', 'Cite', 'Media', 'Approval', 'Owner'].map(
                  (h) => (
                    <th
                      key={h}
                      className="whitespace-nowrap px-3 py-2.5 font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle"
                    >
                      {h}
                    </th>
                  ),
                )}
              </tr>
            </thead>
            <tbody>
              {filtered.map((it) => {
                const active =
                  selected?.kind === 'content_item' && selected.id === it.id;
                return (
                  <tr
                    key={it.id}
                    id={`content-row-${it.id}`}
                    onClick={() => select(selectContentItem(it))}
                    className={`cursor-pointer border-b border-line transition-colors ${
                      active
                        ? 'bg-accent/5'
                        : it.status === 'blocked'
                          ? 'bg-status-blocked/[0.04] hover:bg-status-blocked/[0.08]'
                          : 'hover:bg-surface-2'
                    }`}
                  >
                    <td className="whitespace-nowrap px-3 py-3 font-mono text-[12px] text-fg-muted">
                      <span className="flex items-center gap-2">
                        <StatusDot status={it.status} />
                        {it.id}
                      </span>
                    </td>
                    <td className="max-w-xs px-3 py-3">
                      <span className="block truncate font-medium text-fg">
                        {it.title}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-3 py-3 text-xs text-fg-muted">
                      {LANE_LABEL[it.lane]}
                    </td>
                    <td className="whitespace-nowrap px-3 py-3">
                      <StatusChip status={it.status} nowrap>
                        {it.status_label}
                      </StatusChip>
                    </td>
                    <td className="px-3 py-3">
                      <CellDot status={it.citation_state} />
                    </td>
                    <td className="px-3 py-3">
                      <CellDot status={it.media_state} />
                    </td>
                    <td className="whitespace-nowrap px-3 py-3 text-xs text-fg-muted">
                      {it.approval_state}
                    </td>
                    <td className="whitespace-nowrap px-3 py-3 text-xs text-fg-muted">
                      {it.owner}
                    </td>
                  </tr>
                );
              })}
              {filtered.length === 0 && (
                <tr>
                  <td
                    colSpan={8}
                    className="px-3 py-10 text-center text-sm text-fg-subtle"
                  >
                    No content items match the current filter.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Panel>

      <section className="mt-8 border-t border-line pt-6">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <div className="flex items-center gap-3">
            <div>
              <SectionLabel>Lane C Artifact Intake Pipeline</SectionLabel>
              <p className="text-xs text-fg-muted mt-0.5">
                Deterministic local contract checks for artifact-backed macro briefs.
              </p>
            </div>
            <button
              type="button"
              id="btn-inspect-lane-c-packet"
              onClick={() => select(selectLaneCArtifactIntakeValidationPacket(laneCPacket))}
              className="text-[10px] font-mono border border-line hover:border-line-strong hover:bg-surface-2 text-fg-muted px-2 py-0.5 rounded transition-colors"
            >
              Inspect Packet
            </button>
          </div>
          <StatusChip status="review" icon nowrap>
            Lane C artifact intake: review-only
          </StatusChip>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
          <div className="rounded-xl border border-line bg-surface-1 p-4 shadow-card">
            <div className="text-[11px] font-mono font-bold uppercase tracking-wider text-fg-subtle">
              Candidates / Blocked
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-semibold font-mono text-fg">
                {laneCPacket.artifact_candidate_count}
              </span>
              <span className="text-xs text-fg-muted font-medium">candidates /</span>
              <span className="text-2xl font-semibold font-mono text-status-blocked">
                {laneCPacket.candidates.filter(c => c.blocked_reasons.length > 0).length}
              </span>
              <span className="text-xs text-fg-muted font-medium">blocked</span>
            </div>
          </div>

          <div className="rounded-xl border border-line bg-surface-1 p-4 shadow-card">
            <div className="text-[11px] font-mono font-bold uppercase tracking-wider text-fg-subtle">
              Compliance Posture
            </div>
            <div className="mt-2 space-y-1 text-xs text-fg-muted">
              <div className="flex items-center gap-1.5">
                <span className="text-green-500 font-bold">✓</span> DQR / Readiness not cleared
              </div>
              <div className="flex items-center gap-1.5">
                <span className="text-green-500 font-bold">✓</span> Proxy / Degraded labels preserved
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-line bg-surface-1 p-4 shadow-card">
            <div className="text-[11px] font-mono font-bold uppercase tracking-wider text-fg-subtle">
              Security Constraints
            </div>
            <div className="mt-2 space-y-1 text-xs text-fg-muted">
              <div className="flex items-center gap-1.5">
                <span className="text-red-500 font-bold">✗</span> No public-postable
              </div>
              <div className="flex items-center gap-1.5">
                <span className="text-red-500 font-bold">✗</span> No dispatch-ready
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2">
            <Panel bodyClassName="p-0">
              <div className="overflow-x-auto">
                <table className="w-full border-collapse text-sm">
                  <thead>
                    <tr className="border-b border-line bg-surface-2 text-left">
                      {['Candidate ID', 'Family', 'Lineage Ref', 'Freshness', 'DQR Status', 'Status'].map(h => (
                        <th key={h} className="whitespace-nowrap px-3 py-2.5 font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle">
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {laneCPacket.candidates.map((c) => {
                      const active = selected?.kind === 'lane_c_artifact_intake_candidate' && selected.id === c.candidate_id;
                      return (
                        <tr
                          key={c.candidate_id}
                          id={`lane-c-candidate-row-${c.candidate_id}`}
                          onClick={() => select(selectLaneCArtifactIntakeCandidate(c))}
                          className={`cursor-pointer border-b border-line transition-colors ${
                            active ? 'bg-accent/5' : 'hover:bg-surface-2'
                          }`}
                        >
                          <td className="whitespace-nowrap px-3 py-2.5 font-mono text-[11.5px] text-fg font-medium">
                            {c.candidate_id.replace('valid_shape_but_blocked_missing_manual_review', 'missing_manual_review').replace('stale_or_missing_freshness_metadata', 'stale_metadata').replace('degraded_proxy_or_unverified_lineage', 'degraded_proxy')}
                          </td>
                          <td className="whitespace-nowrap px-3 py-2.5 text-xs text-fg-muted">{c.artifact_family}</td>
                          <td className="whitespace-nowrap px-3 py-2.5 font-mono text-[11px] text-fg-muted">{c.lineage_ref}</td>
                          <td className="whitespace-nowrap px-3 py-2.5 text-xs text-fg-muted">{c.freshness_status}</td>
                          <td className="whitespace-nowrap px-3 py-2.5 text-xs text-fg-muted">{c.dqr_status}</td>
                          <td className="whitespace-nowrap px-3 py-2.5">
                            <StatusChip status={c.blocked_reasons.length > 0 ? 'blocked' : 'verified'}>
                              {c.blocked_reasons.length > 0 ? 'Blocked' : 'Review Ready'}
                            </StatusChip>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </Panel>
          </div>

          <div>
            <Panel title="Pipeline Checks">
              <div className="space-y-2 mt-2">
                {laneCPacket.validation_checks.map((check) => (
                  <div key={check.check_id} className="flex items-start gap-2 text-xs">
                    <span className={check.passed ? 'text-green-500 font-bold' : 'text-red-500 font-bold'}>
                      {check.passed ? '✓' : '✗'}
                    </span>
                    <div>
                      <span className="font-mono text-[11px] text-fg break-all block">{check.check_id}</span>
                      <span className="text-[11px] text-fg-muted">{check.description}</span>
                    </div>
                  </div>
                ))}
              </div>
            </Panel>
          </div>
        </div>
      </section>

      <section>
        <SectionLabel>Lane legend</SectionLabel>
        <div className="flex flex-wrap gap-2 font-mono text-[11px] text-fg-muted">
          {Object.values(LANE_LABEL).map((l) => (
            <span
              key={l}
              className="rounded-md border border-line bg-surface-1 px-2 py-1"
            >
              {l}
            </span>
          ))}
        </div>
      </section>
    </div>
  );
}

function CellDot({ status }: { status: StatusKind }) {
  return (
    <span className="flex items-center gap-1.5 text-[11px] text-fg-subtle">
      <StatusDot status={status} />
      {status === 'neutral' ? '—' : status}
    </span>
  );
}
