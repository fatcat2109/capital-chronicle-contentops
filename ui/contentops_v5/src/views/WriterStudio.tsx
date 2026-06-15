// Capital Chronicle ContentOps V5 — Writer Studio view.
// Editorial drafting workspace: outline, guardrails, SEO, AI variants, media.
// AI Writer is UI-only and review-only. No provider/network call. Nothing
// here is public-postable. No storage, no credentials.

import { useApp } from '../state';
import { viewModel } from '../fixtures';
import { IconImage, IconSparkle } from '../ui/icons';
import {
  EvidenceChip,
  Panel,
  ScoreBar,
  SectionLabel,
  StatusChip,
  StatusDot,
} from '../ui/primitives';
import type { StatusKind } from '../types';

export function WriterStudio() {
  const { select, selected } = useApp();
  const d = viewModel.editorial_draft;

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 font-mono text-[11px] font-bold uppercase tracking-[0.14em] text-fg-subtle">
            Editorial drafting
            <span className="text-fg-subtle/60">·</span>
            <span className="text-fg-muted">{d.id}</span>
          </div>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight text-fg">
            Writer Studio
          </h1>
          <p className="mt-1 text-sm font-medium text-fg-muted">{d.title}</p>
          <div className="mt-2 flex flex-wrap items-center gap-1.5">
            {d.platform_tabs.map((p, i) => (
              <span
                key={p}
                className={`rounded-md px-2 py-0.5 font-mono text-[11px] ${
                  i === 0
                    ? 'bg-fg text-bg'
                    : 'border border-line bg-surface-2 text-fg-muted'
                }`}
              >
                {p}
              </span>
            ))}
          </div>
        </div>
        <StatusChip status="review" icon>
          Review only · not postable
        </StatusChip>
      </header>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        {/* Draft + outline */}
        <div className="space-y-6 xl:col-span-2">
          <Panel
            title="Draft"
            subtitle="Local working copy · no auto-publish"
            actions={<EvidenceChip>{viewModel.content_items[1].evidence_id}</EvidenceChip>}
          >
            <ol className="mb-4 space-y-1.5">
              {d.outline.map((o, i) => (
                <li key={i} className="flex gap-2.5 text-sm text-fg-muted">
                  <span className="font-mono text-[11px] text-fg-subtle">
                    {String(i + 1).padStart(2, '0')}
                  </span>
                  <span>{o}</span>
                </li>
              ))}
            </ol>
            <p className="rounded-lg border border-line bg-surface-2 p-3 text-sm leading-relaxed text-fg-muted">
              {d.body_excerpt}
            </p>
            <div className="mt-3 flex items-start gap-2 rounded-lg border border-status-review/30 bg-status-review/10 p-3">
              <StatusDot status="review" />
              <p className="text-[12px] leading-relaxed text-fg">
                <span className="font-semibold">Limitation note:</span>{' '}
                {d.limitation_note}
              </p>
            </div>
          </Panel>

          {/* AI variants */}
          <Panel
            title={
              <span className="flex items-center gap-2">
                <IconSparkle className="h-4 w-4 text-accent" />
                AI Writer
              </span>
            }
            subtitle="UI-only · draft variants · provider gate closed · human review required"
          >
            <div className="space-y-2">
              {d.ai_outputs.map((v) => {
                const active =
                  selected?.kind === 'ai_variant' && selected.id === v.variant_id;
                return (
                  <button
                    type="button"
                    key={v.variant_id}
                    id={`ai-${v.variant_id}`}
                    onClick={() =>
                      select({
                        kind: 'ai_variant',
                        id: v.variant_id,
                        title: `${v.platform} · ${v.style_mode}`,
                        fields: [
                          { label: 'Platform', value: v.platform },
                          { label: 'Audience', value: v.audience_mode },
                          { label: 'Style', value: v.style_mode },
                          { label: 'Guardrail', value: v.guardrail_status, status: v.guardrail_status },
                          { label: 'Review', value: v.human_review_required ? 'required' : 'no', status: 'review' },
                          { label: 'Postable', value: 'no', status: 'blocked' },
                          { label: 'Reason', value: v.not_public_postable_reason },
                        ],
                      })
                    }
                    className={`w-full rounded-lg border px-3 py-2.5 text-left transition-colors ${
                      active
                        ? 'border-accent/40 bg-accent/5'
                        : 'border-line bg-surface-2 hover:border-line-strong'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="flex items-center gap-2 text-sm font-medium text-fg">
                        <span className="font-mono text-[11px] text-fg-subtle">
                          {v.variant_id}
                        </span>
                        {v.platform} · {v.style_mode}
                      </span>
                      <StatusChip status={v.guardrail_status}>
                        {v.guardrail_status}
                      </StatusChip>
                    </div>
                    <p className="mt-1 text-[11px] leading-relaxed text-fg-subtle">
                      {v.not_public_postable_reason}
                    </p>
                    <p className="mt-1 font-mono text-[10.5px] text-status-blocked">
                      publish_ready: false
                    </p>
                  </button>
                );
              })}
            </div>
          </Panel>
        </div>

        {/* Right: guardrails, SEO, media */}
        <div className="space-y-6">
          <Panel title="Guardrails &amp; claim risk" bodyClassName="p-4 space-y-4">
            <div>
              <SectionLabel>Guardrails</SectionLabel>
              <ul className="space-y-1.5">
                {d.guardrails.map((g) => (
                  <li
                    key={g.id}
                    className="flex items-center justify-between gap-2 text-sm"
                  >
                    <span className="flex items-center gap-2 text-fg-muted">
                      <StatusDot status={g.status} />
                      {g.label}
                    </span>
                    <StatusChip status={g.status}>{g.status}</StatusChip>
                  </li>
                ))}
              </ul>
            </div>
            <div className="border-t border-line pt-3">
              <SectionLabel>Claim risks</SectionLabel>
              <ul className="space-y-1.5">
                {d.claim_risks.map((c) => (
                  <li
                    key={c.id}
                    className="flex items-center gap-2 text-[12px] text-fg-muted"
                  >
                    <StatusDot status={c.severity} />
                    {c.label}
                  </li>
                ))}
              </ul>
            </div>
            <div className="border-t border-line pt-3">
              <SectionLabel>Citations</SectionLabel>
              <ul className="space-y-1.5">
                {d.citations.map((c) => (
                  <li
                    key={c.id}
                    className="flex items-center justify-between gap-2 text-[12px]"
                  >
                    <span className="text-fg-muted">{c.label}</span>
                    <StatusChip status={c.status}>{c.status}</StatusChip>
                  </li>
                ))}
              </ul>
            </div>
          </Panel>

          <Panel
            title="SEO &amp; Editorial Score"
            subtitle="Advisory only · not a publish gate"
          >
            <div className="space-y-3">
              <Score label="Editorial" value={d.seo.editorial_score} />
              <Score label="SEO" value={d.seo.seo_score} />
              <Score label="Platform fit" value={d.seo.platform_fit_score} />
            </div>
            <div className="mt-4 border-t border-line pt-3">
              <SectionLabel>Keywords</SectionLabel>
              <div className="flex flex-wrap gap-1.5">
                {d.seo.keywords.map((k) => (
                  <span
                    key={k}
                    className="rounded-md border border-line bg-surface-2 px-1.5 py-0.5 text-[11px] text-fg-muted"
                  >
                    {k}
                  </span>
                ))}
              </div>
            </div>
            <p className="mt-3 font-mono text-[11px] text-fg-subtle">
              Readability: {d.seo.readability}
            </p>
          </Panel>

          <Panel
            title={
              <span className="flex items-center gap-2">
                <IconImage className="h-4 w-4 text-fg-subtle" />
                Media Tray
              </span>
            }
            subtitle="Mock only · no upload, no file picker"
          >
            <ul className="space-y-2">
              {d.media.map((m) => {
                const active =
                  selected?.kind === 'media_asset' && selected.id === m.id;
                return (
                  <li key={m.id}>
                    <button
                      type="button"
                      id={`media-${m.id}`}
                      onClick={() =>
                        select({
                          kind: 'media_asset',
                          id: m.id,
                          title: m.name,
                          fields: [
                            { label: 'Kind', value: m.kind, mono: true },
                            { label: 'Alt text', value: m.alt_text },
                            { label: 'Rights', value: m.rights_label, status: m.rights_status },
                            { label: 'Selected', value: m.selected ? 'yes' : 'no' },
                            { label: 'Constraints', value: m.platform_constraints.join(' · ') },
                          ],
                        })
                      }
                      className={`flex w-full items-center gap-3 rounded-lg border px-3 py-2.5 text-left transition-colors ${
                        active
                          ? 'border-accent/40 bg-accent/5'
                          : m.selected
                            ? 'border-line-strong bg-surface-2'
                            : 'border-line bg-surface-2 hover:border-line-strong'
                      }`}
                    >
                      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-line bg-surface-3 text-fg-subtle">
                        <IconImage className="h-4 w-4" />
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="block truncate font-mono text-[12px] text-fg">
                          {m.name}
                        </span>
                        <span className="block truncate text-[11px] text-fg-subtle">
                          {m.alt_text}
                        </span>
                      </span>
                      <StatusChip status={m.rights_status}>
                        {m.rights_status}
                      </StatusChip>
                    </button>
                  </li>
                );
              })}
            </ul>
          </Panel>
        </div>
      </div>
    </div>
  );
}

function Score({ label, value }: { label: string; value: number }) {
  const status: StatusKind =
    value >= 80 ? 'verified' : value >= 60 ? 'review' : 'blocked';
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-[12px]">
        <span className="text-fg-muted">{label}</span>
        <span className="font-mono font-semibold text-fg">{value}</span>
      </div>
      <ScoreBar value={value} status={status} />
    </div>
  );
}
