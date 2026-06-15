// Capital Chronicle ContentOps V5 — Draft Inspector view.
// Read-only inspection surface for one grounded draft. Verifies source lineage,
// citation completeness, limitation notes, claim-risk classification, no-signal
// audit, forbidden-language scan, and artifact-backed eligibility. No provider
// call, no network, no autonomous approval. publish_ready is always false.
// Selecting a check/row updates the inspector.

import { useApp } from '../state';
import { viewModel } from '../fixtures';
import {
  selectArtifactEligibility,
  selectCitationCheck,
  selectClaimRiskItem,
  selectDraftInspection,
  selectLimitationCheck,
  selectNoSignalCheck,
} from '../selectors';
import { IconFingerprint } from '../ui/icons';
import { Panel, StatusChip, StatusDot } from '../ui/primitives';
import type { SelectableObject, StatusKind } from '../types';

export function DraftInspector() {
  const { select, selected } = useApp();
  const di = viewModel.draft_inspections[0];

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 font-mono text-[11px] font-bold uppercase tracking-[0.14em] text-fg-subtle">
            Draft inspection
            <span className="text-fg-subtle/60">·</span>
            <span className="text-fg-muted">{di.draft_id}</span>
          </div>
          <h1 className="mt-2 flex items-center gap-2 text-2xl font-semibold tracking-tight text-fg">
            <IconFingerprint className="h-6 w-6 text-accent" />
            Draft Inspector
          </h1>
          <p className="mt-1 text-sm font-medium text-fg-muted">{di.title}</p>
        </div>
        <div className="flex flex-col items-end gap-1.5">
          <StatusChip status={di.approval_readiness_status} icon nowrap>
            {di.approval_readiness}
          </StatusChip>
          <span className="font-mono text-[10.5px] text-status-blocked">
            publish_ready: false
          </span>
        </div>
      </header>

      {/* Source lineage */}
      <Panel
        title="Source lineage"
        subtitle="Traceability of the draft back to official sources — review-only"
        bodyClassName="p-4"
      >
        <ol className="space-y-2">
          {di.source_lineage.map((l) => (
            <li
              key={l.id}
              className="flex items-start gap-2.5 text-sm text-fg-muted"
            >
              <span className="mt-0.5 font-mono text-[11px] text-fg-subtle">
                {l.id}
              </span>
              <span>{l.label}</span>
            </li>
          ))}
        </ol>
      </Panel>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        {/* Citation completeness */}
        <Panel
          title="Citation completeness"
          subtitle="Select a check to inspect"
          bodyClassName="p-3 space-y-2"
        >
          {di.citation_checks.map((c) => (
            <CheckRow
              key={c.id}
              id={`citation-${c.id}`}
              label={c.label}
              detail={c.detail}
              status={c.status}
              meta={c.source_ref}
              active={
                selected?.kind === 'citation_check' && selected.id === c.id
              }
              onSelect={() => select(selectCitationCheck(c))}
            />
          ))}
        </Panel>

        {/* Claim-risk classification */}
        <Panel
          title="Claim-risk classification"
          subtitle="Select an item to inspect"
          bodyClassName="p-3 space-y-2"
        >
          {di.claim_risk_items.map((c) => (
            <CheckRow
              key={c.id}
              id={`claim-risk-${c.id}`}
              label={c.label}
              detail={c.detail}
              status={c.severity}
              meta={c.classification}
              active={
                selected?.kind === 'claim_risk_item' && selected.id === c.id
              }
              onSelect={() => select(selectClaimRiskItem(c))}
            />
          ))}
        </Panel>

        {/* Limitation checks */}
        <Panel
          title="Limitation notes"
          subtitle="Caveats preserved through editing"
          bodyClassName="p-3 space-y-2"
        >
          {di.limitation_checks.map((c) => (
            <CheckRow
              key={c.id}
              id={`limitation-${c.id}`}
              label={c.label}
              detail={c.detail}
              status={c.status}
              active={
                selected?.kind === 'limitation_check' && selected.id === c.id
              }
              onSelect={() => select(selectLimitationCheck(c))}
            />
          ))}
        </Panel>

        {/* No-signal / forbidden-language audit */}
        <Panel
          title="No-signal &amp; forbidden-language audit"
          subtitle="No buy/sell/hold, no target, no advice"
          bodyClassName="p-3 space-y-2"
        >
          {di.no_signal_checks.map((c) => (
            <CheckRow
              key={c.id}
              id={`no-signal-${c.id}`}
              label={c.label}
              detail={c.detail}
              status={c.status}
              active={
                selected?.kind === 'no_signal_check' && selected.id === c.id
              }
              onSelect={() => select(selectNoSignalCheck(c))}
            />
          ))}
        </Panel>
      </div>

      {/* Artifact-backed eligibility */}
      <Panel
        title="Artifact-backed eligibility (Lane C)"
        subtitle="Future-gated · artifact intake not available yet"
        bodyClassName="p-3 space-y-2"
      >
        {di.artifact_eligibility_checks.map((c) => (
          <CheckRow
            key={c.id}
            id={`artifact-${c.id}`}
            label={c.label}
            detail={c.detail}
            status={c.status}
            active={
              selected?.kind === 'artifact_eligibility_check' &&
              selected.id === c.id
            }
            onSelect={() => select(selectArtifactEligibility(c))}
          />
        ))}
      </Panel>

      {/* Approval readiness summary */}
      <Panel title="Approval readiness" bodyClassName="p-4">
        <button
          type="button"
          id="draft-inspection-summary"
          onClick={() => select(selectDraftInspection(di))}
          className={`flex w-full items-start justify-between gap-3 rounded-lg border px-3.5 py-3 text-left transition-colors ${
            selected?.kind === 'draft_inspection'
              ? 'border-accent/40 bg-accent/5'
              : 'border-line bg-surface-2 hover:border-line-strong'
          }`}
        >
          <div className="flex items-start gap-2.5">
            <StatusDot status={di.approval_readiness_status} />
            <div>
              <p className="text-sm font-semibold text-fg">
                {di.approval_readiness}
              </p>
              <p className="mt-0.5 text-[12px] text-fg-muted">
                Human review {di.human_review_required ? 'required' : 'not required'} ·
                AI is never source authority
              </p>
            </div>
          </div>
          <span className="shrink-0 font-mono text-[10.5px] text-status-blocked">
            publish_ready: false
          </span>
        </button>
      </Panel>
    </div>
  );
}

function CheckRow({
  id,
  label,
  detail,
  status,
  meta,
  active,
  onSelect,
}: {
  id: string;
  label: string;
  detail: string;
  status: StatusKind;
  meta?: string;
  active: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      id={id}
      onClick={onSelect}
      className={`w-full rounded-lg border px-3 py-2.5 text-left transition-colors ${
        active
          ? 'border-accent/40 bg-accent/5'
          : 'border-line bg-surface-2 hover:border-line-strong'
      }`}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="flex items-center gap-2 text-sm font-medium text-fg">
          <StatusDot status={status} />
          {label}
        </span>
        <StatusChip status={status}>{status}</StatusChip>
      </div>
      <p className="mt-1 text-[11px] leading-relaxed text-fg-subtle">
        {meta ? (
          <span className="font-mono text-fg-muted">{meta} · </span>
        ) : null}
        {detail}
      </p>
    </button>
  );
}

// Keep SelectableObject import meaningful for type-checking consumers.
export type { SelectableObject };
