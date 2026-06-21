// Capital Chronicle ContentOps V5 — shared UI primitives.
// Presentational only. No network, no storage, no credentials.

import type { ReactNode } from 'react';
import type { StatusKind } from '../types';
import { IconAlert, IconBlock, IconCheck } from './icons';

const STATUS_CLASS: Record<StatusKind, string> = {
  verified:
    'border-status-verified/30 bg-status-verified/10 text-status-verified',
  review: 'border-status-review/30 bg-status-review/10 text-status-review',
  blocked: 'border-status-blocked/30 bg-status-blocked/10 text-status-blocked',
  neutral: 'border-line bg-surface-2 text-fg-muted',
};

const STATUS_DOT: Record<StatusKind, string> = {
  verified: 'bg-status-verified',
  review: 'bg-status-review',
  blocked: 'bg-status-blocked',
  neutral: 'bg-fg-subtle',
};

export function StatusChip({
  status,
  children,
  icon = false,
  nowrap = true,
}: {
  status: StatusKind;
  children: ReactNode;
  icon?: boolean;
  nowrap?: boolean;
}) {
  const Icon =
    status === 'verified'
      ? IconCheck
      : status === 'blocked'
        ? IconBlock
        : status === 'review'
          ? IconAlert
          : null;
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 font-mono text-[10.5px] font-bold uppercase tracking-wide ${
        nowrap ? 'whitespace-nowrap' : 'break-all'
      } ${STATUS_CLASS[status]}`}
    >
      {icon && Icon && <Icon className="h-3 w-3" />}
      {children}
    </span>
  );
}

export function StatusDot({ status }: { status: StatusKind }) {
  return (
    <span
      className={`inline-block h-2 w-2 shrink-0 rounded-full ${STATUS_DOT[status]}`}
      aria-hidden
    />
  );
}

export function EvidenceChip({ children }: { children: ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-md border border-line bg-surface-2 px-1.5 py-0.5 font-mono text-[10.5px] text-fg-muted">
      {children}
    </span>
  );
}

export function Panel({
  title,
  subtitle,
  actions,
  children,
  className = '',
  bodyClassName = 'p-4',
}: {
  title?: ReactNode;
  subtitle?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
}) {
  return (
    <section
      className={`overflow-hidden rounded-xl border border-line bg-surface-1 shadow-card ${className}`}
    >
      {(title || actions) && (
        <header className="flex items-center justify-between gap-3 border-b border-line px-4 py-3">
          <div className="min-w-0">
            {title && (
              <h2 className="truncate text-sm font-semibold text-fg">
                {title}
              </h2>
            )}
            {subtitle && (
              <p className="mt-0.5 truncate text-[12px] text-fg-muted">
                {subtitle}
              </p>
            )}
          </div>
          {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
        </header>
      )}
      <div className={bodyClassName}>{children}</div>
    </section>
  );
}

export function Metric({
  label,
  value,
  status = 'neutral',
  hint,
}: {
  label: string;
  value: string;
  status?: StatusKind;
  hint?: string;
}) {
  return (
    <div className="group relative overflow-hidden rounded-xl border border-line bg-surface-1 px-4 py-3 shadow-card transition-colors hover:border-line-strong">
      <div className="flex items-center justify-between">
        <div className="font-mono text-[10.5px] uppercase tracking-wide text-fg-muted">
          {label}
        </div>
        <StatusDot status={status} />
      </div>
      <div className="mt-2 text-2xl font-semibold tracking-tight text-fg">
        {value}
      </div>
      {hint && (
        <div className="mt-0.5 text-[11px] text-fg-subtle">{hint}</div>
      )}
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
    <div className="rounded-lg border border-dashed border-status-blocked/50 bg-status-blocked/5 p-3">
      <button
        type="button"
        disabled
        aria-disabled="true"
        title={reason}
        className="flex w-full cursor-not-allowed items-center justify-center gap-2 rounded-md border border-line bg-surface-2 px-3 py-2 text-sm font-semibold text-fg-muted opacity-70"
      >
        <IconBlock className="h-4 w-4" />
        {label} (disabled)
      </button>
      <p className="mt-2 font-mono text-[10.5px] leading-relaxed text-status-blocked break-all">
        {reason}
      </p>
    </div>
  );
}

/** Section heading used inside the main workspace above a group of panels. */
export function SectionLabel({ children }: { children: ReactNode }) {
  return (
    <h2 className="mb-3 font-mono text-[11px] font-bold uppercase tracking-[0.14em] text-fg-subtle">
      {children}
    </h2>
  );
}

/** Thin horizontal score/confidence bar (0–100). */
export function ScoreBar({
  value,
  status,
}: {
  value: number;
  status: StatusKind;
}) {
  return (
    <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-3">
      <div
        className={`h-full rounded-full ${STATUS_DOT[status]}`}
        style={{ width: `${Math.max(0, Math.min(100, value))}%` }}
      />
    </div>
  );
}
