// Capital Chronicle ContentOps V5 — Writer Studio view.
// Editorial drafting workspace: outline, guardrails, SEO, AI variants, media.
// AI Writer is UI-only and review-only. No provider/network call. Nothing
// here is public-postable. No storage, no credentials.

import { useApp } from '../state';
import { viewModel } from '../fixtures';
import { selectAiVariant, selectMediaAsset, selectCandidateReviewItem, selectEditorialBriefReviewPacket } from '../selectors';
import { editorialBriefReviewAdapter } from '../data/editorialBriefReviewAdapter';
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
          {/* Editorial Brief Review Queue Panel */}
          <Panel
            title="Editorial Brief Review Queue"
            subtitle="Local candidate metadata bridge · no article draft"
            actions={
              <button
                type="button"
                id="btn-inspect-review-packet"
                onClick={() => select(selectEditorialBriefReviewPacket(editorialBriefReviewAdapter.packet))}
                className="rounded-md border border-line bg-surface-2 px-2.5 py-1 font-mono text-[10.5px] text-fg-muted hover:border-line-strong hover:text-fg transition-colors"
              >
                Inspect Packet
              </button>
            }
            bodyClassName="p-4 space-y-4"
          >
            {/* Packet Metadata Grid */}
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
              <div className="rounded-xl border border-line bg-surface-2 p-3">
                <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle">
                  Packet Hash
                </div>
                <div className="mt-1 break-all font-mono text-[11px] font-semibold text-fg">
                  {editorialBriefReviewAdapter.packet.packet_hash}
                </div>
              </div>
              <div className="rounded-xl border border-line bg-surface-2 p-3">
                <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle">
                  Source Bridge Task
                </div>
                <div className="mt-1 break-all font-mono text-[11px] font-semibold text-fg">
                  {editorialBriefReviewAdapter.packet.source_bridge_task_label}
                </div>
              </div>
              <div className="rounded-xl border border-line bg-surface-2 p-3">
                <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle">
                  Ingestion Status
                </div>
                <div className="mt-1 break-all text-xs font-semibold text-fg">
                  <span className="font-mono uppercase text-status-review">{editorialBriefReviewAdapter.packet.ingestion_repo_status}</span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {/* Blocked Reasons */}
              <div className="rounded-xl border border-line bg-surface-2 p-3">
                <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-status-blocked">
                  Blocked reasons
                </div>
                <ul className="mt-2 list-inside list-disc text-xs text-fg-muted space-y-1">
                  {editorialBriefReviewAdapter.blockedReasons.map(r => (
                    <li key={r} className="font-mono text-[11px]">{r}</li>
                  ))}
                </ul>
              </div>

              {/* Checklist */}
              <div className="rounded-xl border border-line bg-surface-2 p-3">
                <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle">
                  Operator Checklist
                </div>
                <ul className="mt-2 list-inside list-disc text-xs text-fg-muted space-y-1">
                  {editorialBriefReviewAdapter.checklist.map(c => (
                    <li key={c}>{c}</li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Candidates Table */}
            <div className="border-t border-line pt-3">
              <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle mb-2">
                Candidate review items ({editorialBriefReviewAdapter.packet.candidate_count})
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs min-w-[500px]">
                  <thead>
                    <tr className="border-b border-line bg-surface-2 font-mono text-[10px] text-fg-subtle">
                      <th className="px-2 py-1.5">Candidate ID</th>
                      <th className="px-2 py-1.5">Evidence Role</th>
                      <th className="px-2 py-1.5">Family</th>
                      <th className="px-2 py-1.5">Records</th>
                      <th className="px-2 py-1.5">Next Step</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-line">
                    {editorialBriefReviewAdapter.candidateReviewItems.map((item) => {
                      const active = selected?.kind === 'candidate_review_item' && selected.id === item.candidate_id;
                      return (
                        <tr
                          key={item.candidate_id}
                          id={`candidate-row-${item.candidate_id}`}
                          onClick={() => select(selectCandidateReviewItem(item))}
                          className={`cursor-pointer transition-colors hover:bg-surface-3 ${
                            active ? 'bg-accent/5' : ''
                          }`}
                        >
                          <td className="px-2 py-2 font-mono font-semibold text-fg">
                            {item.candidate_id}
                          </td>
                          <td className="px-2 py-2 text-fg-muted font-mono">{item.evidence_role}</td>
                          <td className="px-2 py-2 text-fg-muted font-mono">{item.source_family}</td>
                          <td className="px-2 py-2 font-mono text-fg">{item.records_count}</td>
                          <td className="px-2 py-2 text-fg-muted font-mono">{item.allowed_next_step}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Safety & Truth Flags Strip */}
            <div className="border-t border-line pt-3 space-y-2">
              <div className="flex flex-wrap items-center gap-1.5 text-[10.5px] font-mono text-fg-subtle">
                <span className="font-bold uppercase mr-1">Safety Flags:</span>
                {Object.entries(editorialBriefReviewAdapter.safetyFlags).map(([key, val]) => (
                  <span key={key} className={`px-1.5 py-0.5 rounded border border-line bg-surface-2 ${val ? 'text-status-blocked' : 'text-status-verified'}`}>
                    {key}: {String(val)}
                  </span>
                ))}
              </div>
              <div className="flex flex-wrap items-center gap-1.5 text-[10.5px] font-mono text-fg-subtle">
                <span className="font-bold uppercase mr-1">Truth Flags:</span>
                {Object.entries(editorialBriefReviewAdapter.protectedTruthFlags).map(([key, val]) => (
                  <span key={key} className={`px-1.5 py-0.5 rounded border border-line bg-surface-2 ${val ? 'text-status-blocked' : 'text-status-verified'}`}>
                    {key}: {String(val)}
                  </span>
                ))}
              </div>
            </div>
          </Panel>

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
                    onClick={() => select(selectAiVariant(v))}
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
          {/* Compact media quick-access — keeps the Media Tray reachable in the
              first fold at 1440x900. Mock/local assets only: no upload, no file
              picker, no media API. Selecting a chip routes to the inspector. */}
          <Panel
            title={
              <span className="flex items-center gap-2">
                <IconImage className="h-4 w-4 text-fg-subtle" />
                Media Tray
              </span>
            }
            subtitle="Mock only · local assets · no upload, no file picker, no media API"
            actions={
              <span className="rounded-md border border-line bg-surface-2 px-1.5 py-0.5 font-mono text-[10.5px] text-fg-muted">
                {d.media.length} mock
              </span>
            }
            bodyClassName="p-3"
          >
            <div className="flex flex-wrap gap-1.5">
              {d.media.map((m) => {
                const active =
                  selected?.kind === 'media_asset' && selected.id === m.id;
                return (
                  <button
                    type="button"
                    key={m.id}
                    id={`media-chip-${m.id}`}
                    onClick={() => select(selectMediaAsset(m))}
                    className={`flex items-center gap-2 rounded-full border px-2.5 py-1 text-[11px] font-medium transition-colors ${
                      active
                        ? 'border-accent/40 bg-accent/5 text-fg'
                        : 'border-line bg-surface-2 text-fg-muted hover:border-line-strong hover:text-fg'
                    }`}
                  >
                    <IconImage className="h-3.5 w-3.5 shrink-0 text-fg-subtle" />
                    <span className="max-w-[10rem] truncate font-mono">
                      {m.name}
                    </span>
                    <StatusDot status={m.rights_status} />
                  </button>
                );
              })}
            </div>
          </Panel>

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
