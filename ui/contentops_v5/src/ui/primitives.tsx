// Capital Chronicle ContentOps V5 — shared UI primitives.
// Presentational only. No network, no storage, no credentials.

import type { ReactNode } from 'react';
import type { StatusKind } from '../types';

const STATUS_CLASS: Record<StatusKind, string> = {
  verified: 'border-status-verified/40 bg-status-verified/10 text-status-verified',
  review: 'border-status-review/40 bg-status-review/10 text-status-review',
  blocked: 'border-status-blocked/40 bg-status-blocked/10 text-status-blocked',
  neutral: 'border-line bg-surface-2 text-fg-muted',
};

export function StatusChip({
  status,
  children,
}: {
  status: StatusKind;
  children: ReactNode;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded border px-1.5 py-0.5 font-mono text-[11px] font-bold uppercase tracking-wide ${STATUS_CLASS[status]}`}
    >
      {children}
    </span>
  );
}

export function EvidenceChip({ children }: { children: ReactNode }) {
  return (
    <span className="inline-flex items-center rounded border border-line bg-surface-2 px-1.5 py-0.5 font-mono text-[11px] text-fg-muted">
      {children}
    </span>
  );
}

export function Panel({
  title,
  actions,
  children,
  className = '',
}: {
  title?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={`rounded-lg border border-line bg-surface-1 ${className}`}
    >
      {(title || actions) && (
        <header className="flex items-center justify-between border-b border-line px-4 py-3">
          {title && (
            <h2 className="text-sm font-semibold text-fg">{title}</h2>
          )}
          {actions}
        </header>
      )}
      <div className="p-4">{children}</div>
    </section>
  );
}

export function Metric({
  label,
  value,
  status = 'neutral',
}: {
  label: string;
  value: string;
  status?: StatusKind;
}) {
  return (
    <div className="rounded-md border border-line bg-surface-2 px-3 py-2">
      <div className="font-mono text-[11px] uppercase tracking-wide text-fg-muted">
        {label}
      </div>
      <div className="mt-1 flex items-center gap-2">
        <span className="text-lg font-semibold text-fg">{value}</span>
        <span
          className={`inline-block h-2 w-2 rounded-full ${
            status === 'verified'
              ? 'bg-status-verified'
              : status === 'review'
                ? 'bg-status-review'
                : status === 'blocked'
                  ? 'bg-status-blocked'
                  : 'bg-fg-muted'
          }`}
          aria-hidden
        />
      </div>
    </div>
  );
}

export function LockedAction({
  label,
  reason,
}: {
  label: string;
  reason: string;
}) {
  return (
    <div className="rounded-md border border-dashed border-status-blocked/50 bg-status-blocked/5 p-3">
      <button
        type="button"
        disabled
        aria-disabled="true"
        title={reason}
        className="w-full cursor-not-allowed rounded border border-line bg-surface-2 px-3 py-2 text-sm font-semibold text-fg-muted opacity-70"
      >
        🔒 {label} (disabled)
      </button>
      <p className="mt-2 font-mono text-[11px] text-status-blocked">{reason}</p>
    </div>
  );
}
