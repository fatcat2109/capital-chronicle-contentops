// Capital Chronicle ContentOps V5 — local app state.
// In-memory only. No persistence (no localStorage/sessionStorage), no network.

import { createContext, useContext } from 'react';
import type { SelectableObject, ThemeMode, ViewId } from './types';

export interface AppState {
  view: ViewId;
  setView: (v: ViewId) => void;
  theme: ThemeMode;
  setTheme: (t: ThemeMode) => void;
  selected: SelectableObject | null;
  select: (o: SelectableObject | null) => void;
}

export const AppContext = createContext<AppState | null>(null);

export function useApp(): AppState {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used within AppContext provider');
  return ctx;
}

export interface NavItem {
  id: ViewId;
  label: string;
  icon: string;
}

export interface NavGroup {
  title: string;
  items: NavItem[];
}

export const NAV_GROUPS: NavGroup[] = [
  {
    title: 'Core',
    items: [
      { id: 'command_center', label: 'Command Center', icon: 'dashboard' },
      { id: 'content_inventory', label: 'Content Inventory', icon: 'inventory' },
      { id: 'jim_daily_run', label: 'Jim Daily Run', icon: 'shield' },
      { id: 'platform_payload_preview', label: 'Platform Preview', icon: 'layers' },
      { id: 'manual_publish_metrics', label: 'Manual Publish', icon: 'send' },
    ],
  },
  {
    title: 'Editorial',
    items: [
      { id: 'writer_studio', label: 'Writer Studio', icon: 'edit' },
      { id: 'ai_writer_seo_lab', label: 'AI Writer / SEO Lab', icon: 'sparkle' },
      { id: 'draft_inspector', label: 'Draft Inspector', icon: 'fingerprint' },
      { id: 'approval_queue', label: 'Approval & Dispatch', icon: 'shield' },
    ],
  },
  {
    title: 'Pilot Workflow',
    items: [
      { id: 'manual_export_pilot_verification', label: 'Manual Export', icon: 'layers' },
      { id: 'operator_review_queue', label: 'Review Queue', icon: 'inventory' },
      { id: 'manual_pilot_trail_reconciliation', label: 'Reconciliation', icon: 'sparkle' },
    ],
  },
  {
    title: 'Evidence / Safety',
    items: [
      { id: 'preflight_bundle', label: 'Preflight Bundle', icon: 'shield' },
      { id: 'evidence_vault', label: 'Evidence Vault', icon: 'lock' },
      { id: 'operator_runbook_index', label: 'Operator Runbook', icon: 'lock' },
      { id: 'final_product_readiness', label: 'Final Readiness', icon: 'shield' },
      { id: 'v6_command_center', label: 'V6 Command Center', icon: 'dashboard' },
    ],
  },
];

export const NAV_ITEMS = NAV_GROUPS.flatMap((g) => g.items);
