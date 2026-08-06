// Capital Chronicle ContentOps V5 — app shell + view router (no router dep).
// Local-first. No network, no storage, no credentials.

import { useMemo, useState } from 'react';
import { AppContext, NAV_GROUPS, useApp } from './state';
import type { SelectableObject, ThemeMode, ViewId } from './types';
import { viewModel } from './fixtures';
import { defaultSelectionFor } from './selectors';
import { StatusChip, StatusDot } from './ui/primitives';
import { VIEW_ICONS, IconClose, IconShield, IconSun, IconMoon, IconMenu } from './ui/icons';
import { CommandCenter } from './views/CommandCenter';
import { ContentInventory } from './views/ContentInventory';
import { JimDailyRun } from './views/JimDailyRun';
import { WriterStudio } from './views/WriterStudio';
import { AiWriterSeoLab } from './views/AiWriterSeoLab';
import { DraftInspector } from './views/DraftInspector';
import { PlatformPreview } from './views/PlatformPreview';
import { ManualPublishMetrics } from './views/ManualPublishMetrics';
import { ManualExportPilotVerification } from './views/ManualExportPilotVerification';
import { OperatorReviewQueue } from './views/OperatorReviewQueue';
import { ManualPilotTrailReconciliation } from './views/ManualPilotTrailReconciliation';
import { ApprovalQueue } from './views/ApprovalQueue';
import { EvidenceVault } from './views/EvidenceVault';
import { PreflightBundle } from './views/PreflightBundle';
import { OperatorRunbookIndex } from './views/OperatorRunbookIndex';
import { FinalProductReadinessPanel } from './views/FinalProductReadinessPanel';
import { V6CommandCenter } from './views/V6CommandCenter';
import { CanonicalPackageReviewConsole } from './views/CanonicalPackageReviewConsole';
import { DualLaneCoreV0Shadow } from './views/DualLaneCoreV0Shadow';

export default function App() {
  const [view, setView] = useState<ViewId>('command_center');
  const [theme, setTheme] = useState<ThemeMode>('light');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  // Inspector is never empty on first render: each view has a default object.
  const [selected, setSelected] = useState<SelectableObject | null>(() =>
    defaultSelectionFor('command_center'),
  );

  // Forensic review surfaces force dark-evidence mode; other views use chosen theme.
  const isForensicView =
    view === 'evidence_vault' ||
    view === 'operator_runbook_index' ||
    view === 'final_product_readiness' ||
    view === 'canonical_package_review' ||
    view === 'dual_lane_core_v0_shadow';
  const effectiveTheme: ThemeMode = isForensicView ? 'dark-evidence' : theme;

  const ctx = useMemo(
    () => ({
      view,
      setView: (v: ViewId) => {
        setView(v);
        // Reset the inspector to the new view's primary object.
        setSelected(defaultSelectionFor(v));
      },
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
        <LeftNav isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        <div className="flex min-w-0 flex-1 flex-col">
          <SafetyBar effectiveTheme={effectiveTheme} onMenuClick={() => setSidebarOpen(true)} />
          <div className="flex min-h-0 flex-1">
            <main
              id="v5-workspace"
              className="min-w-0 flex-1 overflow-y-auto"
            >
              <div key={view} className="animate-fade-in mx-auto w-full max-w-container p-6 lg:p-8">
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

function LeftNav({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const { view, setView } = useApp();
  const s = viewModel.system_state;
  return (
    <>
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 z-40 bg-fg/20 backdrop-blur-sm lg:hidden"
        />
      )}
      <nav className={`fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-line bg-surface-1 transition-transform duration-200 lg:static lg:translate-x-0 ${
        isOpen ? 'translate-x-0' : '-translate-x-full'
      }`}>
        <div className="flex items-center justify-between border-b border-line px-5 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-fg font-mono text-sm font-bold text-bg shadow-card">
              CC
            </div>
            <div className="min-w-0">
              <div className="truncate text-sm font-semibold text-fg">
                ContentOps
              </div>
              <div className="font-mono text-[11px] text-fg-subtle">
                V5 · local-first
              </div>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-md border border-line text-fg-muted hover:text-fg lg:hidden"
            title="Close menu"
          >
            <IconClose className="h-4 w-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-4">
          {NAV_GROUPS.map((group) => (
            <div key={group.title} className="space-y-1">
              <h3 className="px-3 text-[10px] font-bold uppercase tracking-wider text-fg-subtle">
                {group.title}
              </h3>
              <ul className="space-y-0.5">
                {group.items.map((item) => {
                  const Icon = VIEW_ICONS[item.icon];
                  const active = view === item.id;
                  return (
                    <li key={item.id}>
                      <button
                        type="button"
                        id={`nav-${item.id}`}
                        onClick={() => {
                          setView(item.id);
                          onClose();
                        }}
                        aria-current={active ? 'page' : undefined}
                        className={`group relative flex w-full items-center gap-3 rounded-lg px-3 py-1.5 text-left text-sm transition-colors ${
                          active
                            ? 'bg-surface-2 font-semibold text-fg'
                            : 'text-fg-muted hover:bg-surface-2 hover:text-fg'
                        }`}
                      >
                        <span
                          className={`absolute left-0 top-1/2 h-5 w-[3px] -translate-y-1/2 rounded-full bg-accent transition-opacity ${
                            active ? 'opacity-100' : 'opacity-0'
                          }`}
                          aria-hidden
                        />
                        <Icon
                          className={`h-[18px] w-[18px] shrink-0 ${
                            active ? 'text-accent' : 'text-fg-subtle group-hover:text-fg-muted'
                          }`}
                        />
                        <span className="truncate">{item.label}</span>
                      </button>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </div>

        <div className="border-t border-line p-3">
          <div className="rounded-lg border border-line bg-surface-2 p-3">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[10.5px] uppercase tracking-wide text-fg-subtle">
                Mode
              </span>
              <StatusDot status="verified" />
            </div>
            <div className="mt-1 font-mono text-[12px] font-semibold text-fg">
              {s.product_mode}
            </div>
            <div className="mt-0.5 text-[11px] text-fg-subtle">
              Review-only · no live posting
            </div>
          </div>
        </div>
      </nav>
    </>
  );
}

function SafetyBar({
  effectiveTheme,
  onMenuClick,
}: {
  effectiveTheme: ThemeMode;
  onMenuClick: () => void;
}) {
  const { theme, setTheme, view } = useApp();
  const s = viewModel.system_state;
  const isDark = effectiveTheme === 'dark-evidence';
  return (
    <header className="flex items-center justify-between gap-4 border-b border-line bg-surface-1 px-6 py-3">
      <div className="flex min-w-0 items-center gap-3">
        <button
          type="button"
          onClick={onMenuClick}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-line text-fg-muted hover:text-fg lg:hidden"
          title="Open menu"
        >
          <IconMenu className="h-4 w-4" />
        </button>
        <IconShield className="h-4 w-4 shrink-0 text-status-verified" />
        <StatusChip status={s.verdict_status} icon>
          {s.verdict}
        </StatusChip>
        <span className="hidden truncate font-mono text-[11px] text-fg-subtle md:inline">
          {s.build_provenance}
        </span>
      </div>
      <div className="flex shrink-0 items-center gap-3">
        <span className="hidden font-mono text-[11px] text-fg-subtle sm:inline">
          {s.baseline_ref}
        </span>
        <button
          type="button"
          id="theme-toggle"
          disabled={
            view === 'evidence_vault' || view === 'canonical_package_review'
          }
          onClick={() => setTheme(theme === 'light' ? 'dark-evidence' : 'light')}
          className="flex items-center gap-1.5 rounded-md border border-line bg-surface-2 px-2.5 py-1.5 font-mono text-[11px] text-fg-muted transition-colors hover:border-line-strong hover:text-fg disabled:cursor-not-allowed disabled:opacity-50"
          title={
            view === 'evidence_vault' || view === 'canonical_package_review'
              ? 'Forensic review surfaces always use dark evidence mode'
              : 'Toggle theme'
          }
        >
          {isDark ? (
            <IconMoon className="h-3.5 w-3.5" />
          ) : (
            <IconSun className="h-3.5 w-3.5" />
          )}
          {isDark ? 'DARK-EVIDENCE' : 'LIGHT'}
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
    case 'jim_daily_run':
      return <JimDailyRun />;
    case 'writer_studio':
      return <WriterStudio />;
    case 'ai_writer_seo_lab':
      return <AiWriterSeoLab />;
    case 'draft_inspector':
      return <DraftInspector />;
    case 'platform_payload_preview':
      return <PlatformPreview />;
    case 'manual_publish_metrics':
      return <ManualPublishMetrics />;
    case 'manual_export_pilot_verification':
      return <ManualExportPilotVerification />;
    case 'operator_review_queue':
      return <OperatorReviewQueue />;
    case 'manual_pilot_trail_reconciliation':
      return <ManualPilotTrailReconciliation />;
    case 'approval_queue':
      return <ApprovalQueue />;
    case 'evidence_vault':
      return <EvidenceVault />;
    case 'preflight_bundle':
      return <PreflightBundle />;
    case 'operator_runbook_index':
      return <OperatorRunbookIndex />;
    case 'final_product_readiness':
      return <FinalProductReadinessPanel />;
    case 'v6_command_center':
      return <V6CommandCenter />;
    case 'canonical_package_review':
      return <CanonicalPackageReviewConsole />;
    case 'dual_lane_core_v0_shadow':
      return <DualLaneCoreV0Shadow />;
    default:
      return null;
  }
}

function InspectorRail() {
  const { selected, select } = useApp();
  return (
    <aside
      id="inspector-rail"
      className="hidden w-80 shrink-0 overflow-y-auto border-l border-line bg-surface-1 xl:block"
    >
      <header className="sticky top-0 z-10 flex items-center justify-between border-b border-line bg-surface-1/95 px-4 py-3 backdrop-blur">
        <h2 className="font-mono text-[11px] font-bold uppercase tracking-[0.14em] text-fg-subtle">
          Inspector
        </h2>
        {selected && (
          <button
            type="button"
            id="inspector-clear"
            onClick={() => select(null)}
            className="flex h-6 w-6 items-center justify-center rounded-md text-fg-subtle transition-colors hover:bg-surface-2 hover:text-fg"
            title="Clear selection"
          >
            <IconClose className="h-3.5 w-3.5" />
          </button>
        )}
      </header>

      {!selected ? (
        <div className="bg-grid flex min-h-[16rem] flex-col items-center justify-center px-6 py-10 text-center">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-dashed border-line-strong text-fg-subtle">
            <IconShield className="h-5 w-5" />
          </div>
          <p className="mt-3 text-sm font-medium text-fg-muted">
            Select an object
          </p>
          <p className="mt-1 text-[12px] leading-relaxed text-fg-subtle">
            Select a card, row, gate, asset, or evidence item to inspect its
            properties and provenance.
          </p>
        </div>
      ) : (
        <div key={`${selected.kind}-${selected.id}`} className="animate-fade-in p-4">
          <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-accent">
            {selected.kind.replace(/_/g, ' ')}
          </div>
          <div className="mt-1 text-base font-semibold leading-snug text-fg break-words">
            {selected.title}
          </div>
          <div className="mt-1 font-mono text-[11px] text-fg-muted break-all">
            {selected.id}
          </div>
          <dl className="mt-4 space-y-3 border-t border-line pt-4">
            {selected.fields.map((f, i) => (
              <div
                key={i}
                className="grid grid-cols-[5.5rem_1fr] items-start gap-3"
              >
                <dt className="font-mono text-[10.5px] font-semibold uppercase leading-5 tracking-wide text-fg-muted">
                  {f.label}
                </dt>
                <dd
                  className={`text-sm font-medium leading-5 text-fg ${
                    f.mono ? 'break-all font-mono text-[12px] font-normal' : ''
                  }`}
                >
                  {f.status ? (
                    <StatusChip status={f.status}>{f.value}</StatusChip>
                  ) : (
                    f.value
                  )}
                </dd>
              </div>
            ))}
          </dl>
        </div>
      )}
    </aside>
  );
}
