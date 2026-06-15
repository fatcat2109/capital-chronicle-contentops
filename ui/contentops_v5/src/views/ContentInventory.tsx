// Capital Chronicle ContentOps V5 — Content Inventory view.
// Local-first content table. No network, no storage, no credentials.

import { useMemo, useState } from 'react';
import { useApp } from '../state';
import { viewModel } from '../fixtures';
import { Panel, SectionLabel, StatusChip, StatusDot } from '../ui/primitives';
import { selectContentItem, LANE_LABEL } from '../selectors';
import { IconSearch } from '../ui/icons';
import type { StatusKind } from '../types';

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
