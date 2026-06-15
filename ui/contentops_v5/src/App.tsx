// Capital Chronicle ContentOps V5 — app shell + view router (no router dep).
// Local-first. No network, no storage, no credentials.

import { useMemo, useState } from 'react';
import { AppContext, NAV_ITEMS } from './state';
import type { SelectableObject, ThemeMode, ViewId } from './types';
import { viewModel } from './fixtures';
import { StatusChip } from './ui/primitives';
import { CommandCenter } from './views/CommandCenter';
import { ContentInventory } from './views/ContentInventory';
import { WriterStudio } from './views/WriterStudio';
import { ApprovalQueue } from './views/ApprovalQueue';
import { EvidenceVault } from './views/EvidenceVault';

export default function App() {
  const [view, setView] = useState<ViewId>('command_center');
  const [theme, setTheme] = useState<ThemeMode>('light');
  const [selected, setSelected] = useState<SelectableObject | null>(null);

  // Evidence Vault forces dark evidence mode; other views use chosen theme.
  const effectiveTheme: ThemeMode =
    view === 'evidence_vault' ? 'dark-evidence' : theme;

  const ctx = useMemo(
    () => ({
      view,
      setView,
      theme,
      setTheme,
      selected,
      select: setSelected,
    }),
    [view, theme, selected],
  );

  return (
    <AppContext.Provider value={ctx}>
      <div
        data-theme={effectiveTheme}
        className="flex h-screen w-full overflow-hidden bg-bg text-fg"
      >
        <LeftNav />
        <div className="flex min-w-0 flex-1 flex-col">
          <SafetyBar effectiveTheme={effectiveTheme} />
          <div className="flex min-h-0 flex-1">
            <main
              id="v5-workspace"
              className="min-w-[28rem] flex-1 overflow-y-auto p-6"
            >
              <div className="mx-auto w-full max-w-6xl">
                <ActiveView />
              </div>
            </main>
            <InspectorRail />
          </div>
        </div>
      </div>
    </AppContext.Provider>
  );
}

function LeftNav() {
  const [activeView, setView] = [useApp().view, useApp().setView];
  return (
    <nav className="flex w-60 shrink-0 flex-col border-r border-line bg-surface-1">
      <div className="flex items-center gap-2 border-b border-line px-4 py-4">
        <div className="flex h-8 w-8 items-center justify-center rounded bg-fg text-bg font-mono text-sm font-bold">
          CC
        </div>
        <div>
          <div className="text-sm font-semibold text-fg">ContentOps</div>
          <div className="font-mono text-[11px] text-fg-muted">V5 · local</div>
        </div>
      </div>
      <ul className="flex-1 space-y-1 p-2">
        {NAV_ITEMS.map((item) => (
          <li key={item.id}>
            <button
              type="button"
              id={`nav-${item.id}`}
              onClick={() => setView(item.id)}
              className={`flex w-full items-center gap-3 rounded-md px-3 py-2 text-left text-sm transition-colors ${
                activeView === item.id
                  ? 'bg-surface-3 font-semibold text-fg'
                  : 'text-fg-muted hover:bg-surface-2 hover:text-fg'
              }`}
            >
              <span className="font-mono text-[11px] uppercase">
                {item.icon.slice(0, 2)}
              </span>
              {item.label}
            </button>
          </li>
        ))}
      </ul>
      <div className="border-t border-line p-3">
        <div className="rounded-md border border-line bg-surface-2 p-2">
          <div className="font-mono text-[11px] uppercase text-fg-muted">
            Mode
          </div>
          <div className="mt-1 text-xs font-semibold text-fg">
            {viewModel.system_state.product_mode}
          </div>
        </div>
      </div>
    </nav>
  );
}

function SafetyBar({ effectiveTheme }: { effectiveTheme: ThemeMode }) {
  const { theme, setTheme, view } = useApp();
  const s = viewModel.system_state;
  return (
    <header className="flex items-center justify-between gap-4 border-b border-line bg-surface-1 px-6 py-3">
      <div className="flex items-center gap-3">
        <StatusChip status={s.verdict_status}>{s.verdict}</StatusChip>
        <span className="font-mono text-[11px] text-fg-muted">
          {s.build_provenance}
        </span>
      </div>
      <div className="flex items-center gap-3">
        <span className="font-mono text-[11px] text-fg-muted">
          {s.baseline_ref}
        </span>
        <button
          type="button"
          id="theme-toggle"
          disabled={view === 'evidence_vault'}
          onClick={() =>
            setTheme(theme === 'light' ? 'dark-evidence' : 'light')
          }
          className="rounded border border-line bg-surface-2 px-2 py-1 font-mono text-[11px] text-fg-muted disabled:opacity-50"
          title={
            view === 'evidence_vault'
              ? 'Evidence Vault is always dark evidence mode'
              : 'Toggle theme'
          }
        >
          {effectiveTheme === 'light' ? 'LIGHT' : 'DARK-EVIDENCE'}
        </button>
      </div>
    </header>
  );
}

function ActiveView() {
  const { view } = useApp();
  switch (view) {
    case 'command_center':
      return <CommandCenter />;
    case 'content_inventory':
      return <ContentInventory />;
    case 'writer_studio':
      return <WriterStudio />;
    case 'approval_queue':
      return <ApprovalQueue />;
    case 'evidence_vault':
      return <EvidenceVault />;
    default:
      return null;
  }
}

function InspectorRail() {
  const { selected } = useApp();
  return (
    <aside
      id="inspector-rail"
      className="hidden w-80 shrink-0 overflow-y-auto border-l border-line bg-surface-1 p-4 xl:block"
    >
      <h2 className="font-mono text-[11px] uppercase tracking-wide text-fg-muted">
        Inspector
      </h2>
      {!selected ? (
        <p className="mt-4 text-sm text-fg-muted">
          Select an object to view its properties and evidence.
        </p>
      ) : (
        <div className="mt-4">
          <div className="font-mono text-[11px] uppercase text-fg-muted">
            {selected.kind}
          </div>
          <div className="mt-1 text-sm font-semibold text-fg">
            {selected.title}
          </div>
          <div className="mt-1 font-mono text-[11px] text-fg-muted">
            {selected.id}
          </div>
          <dl className="mt-4 space-y-3 border-t border-line pt-4">
            {selected.fields.map((f, i) => (
              <div key={i}>
                <dt className="font-mono text-[11px] uppercase text-fg-muted">
                  {f.label}
                </dt>
                <dd
                  className={`mt-0.5 text-sm text-fg ${
                    f.mono ? 'font-mono text-[12px]' : ''
                  }`}
                >
                  {f.value}
                </dd>
              </div>
            ))}
          </dl>
        </div>
      )}
    </aside>
  );
}

// Local import to avoid circular import ordering issues in some bundlers.
import { useApp } from './state';
