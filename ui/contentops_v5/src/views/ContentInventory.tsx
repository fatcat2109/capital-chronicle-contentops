// Capital Chronicle ContentOps V5 — Content Inventory view.
// Local-first content table. No network, no storage, no credentials.

import { useApp } from '../state';
import { viewModel } from '../fixtures';
import { Panel, StatusChip } from '../ui/primitives';

const LANE_LABEL: Record<string, string> = {
  A_pre_alpha: 'A · Pre-alpha',
  B_grounded_news: 'B · Grounded news',
  C_artifact_backed: 'C · Artifact-backed',
};

export function ContentInventory() {
  const { select } = useApp();
  const items = viewModel.content_items;

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-fg">
          Content Inventory
        </h1>
        <p className="mt-1 text-sm text-fg-muted">
          Governance view of all editorial objects across content lanes.
          Status, citations, media, and approval state at a glance.
        </p>
      </header>

      <Panel className="overflow-hidden p-0">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-line bg-surface-2 text-left">
                {['ID', 'Title', 'Lane', 'Status', 'Citations', 'Media', 'Approval', 'Owner'].map(
                  (h) => (
                    <th
                      key={h}
                      className="px-3 py-2 font-mono text-[11px] font-bold uppercase tracking-wide text-fg-muted"
                    >
                      {h}
                    </th>
                  ),
                )}
              </tr>
            </thead>
            <tbody>
              {items.map((it) => (
                <tr
                  key={it.id}
                  id={`content-row-${it.id}`}
                  onClick={() =>
                    select({
                      kind: 'content_item',
                      id: it.id,
                      title: it.title,
                      fields: [
                        { label: 'Lane', value: LANE_LABEL[it.lane] },
                        { label: 'Type', value: it.content_type, mono: true },
                        { label: 'Status', value: it.status_label, status: it.status },
                        { label: 'Approval', value: it.approval_state },
                        { label: 'Platform fit', value: it.platform_fit.join(', ') || '—' },
                        { label: 'Owner', value: it.owner },
                        { label: 'Updated', value: it.last_updated, mono: true },
                        { label: 'Evidence', value: it.evidence_id, mono: true },
                      ],
                    })
                  }
                  className="cursor-pointer border-b border-line hover:bg-surface-2"
                >
                  <td className="px-3 py-3 font-mono text-[12px] text-fg-muted">
                    {it.id}
                  </td>
                  <td className="px-3 py-3 font-medium text-fg">{it.title}</td>
                  <td className="px-3 py-3 text-fg-muted">
                    {LANE_LABEL[it.lane]}
                  </td>
                  <td className="px-3 py-3">
                    <StatusChip status={it.status}>{it.status_label}</StatusChip>
                  </td>
                  <td className="px-3 py-3">
                    <StatusChip status={it.citation_state}>cite</StatusChip>
                  </td>
                  <td className="px-3 py-3">
                    <StatusChip status={it.media_state}>media</StatusChip>
                  </td>
                  <td className="px-3 py-3 text-xs text-fg-muted">
                    {it.approval_state}
                  </td>
                  <td className="px-3 py-3 text-xs text-fg-muted">{it.owner}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}
