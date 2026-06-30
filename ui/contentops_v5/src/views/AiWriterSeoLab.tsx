// Capital Chronicle ContentOps V5 — AI Writer / SEO Lab view.
// AI is UI-only and review-only: NEVER source authority. No provider call,
// no model execution, no network, no autonomous approval, no public-ready
// output. All variants/keywords/metrics are local fixtures. publish_ready is
// always the literal false. Selecting an object updates the inspector.

import { SubstackArticleStudioCard } from './SubstackArticleStudioCard';
import { useApp } from '../state';
import { viewModel } from '../fixtures';
import { selectAiVariant, selectSeoKeywordGroup } from '../selectors';
import { IconSparkle } from '../ui/icons';
import {
  Panel,
  ScoreBar,
  SectionLabel,
  StatusChip,
  StatusDot,
} from '../ui/primitives';
import type { StatusKind } from '../types';

export function AiWriterSeoLab() {
  const { select, selected } = useApp();
  const lab = viewModel.ai_writer_lab;

  return (
    <div className="space-y-6">
      <SubstackArticleStudioCard mode="seo" />
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 font-mono text-[11px] font-bold uppercase tracking-[0.14em] text-fg-subtle">
            AI assist
            <span className="text-fg-subtle/60">·</span>
            <span className="text-fg-muted">{lab.source_draft_id}</span>
          </div>
          <h1 className="mt-2 flex items-center gap-2 text-2xl font-semibold tracking-tight text-fg">
            <IconSparkle className="h-6 w-6 text-accent" />
            AI Writer / SEO Lab
          </h1>
          <p className="mt-1 text-sm font-medium text-fg-muted">
            Draft variants, platform fit, and SEO advisory for the selected
            grounded draft.
          </p>
        </div>
        <div className="flex flex-col items-end gap-1.5">
          <StatusChip status="review" icon nowrap>
            UI-only · review only
          </StatusChip>
          <span className="font-mono text-[10.5px] text-status-blocked">
            publish_ready: false
          </span>
        </div>
      </header>

      {/* Safety banner — explicit about what this surface does NOT do. */}
      <div className="rounded-xl border border-status-review/30 bg-status-review/10 p-4">
        <div className="flex items-start gap-2.5">
          <StatusDot status="review" />
          <div>
            <p className="text-sm font-semibold text-fg">
              AI assist is advisory only and never source authority
            </p>
            <p className="mt-1 text-[12px] leading-relaxed text-fg-muted">
              No provider call · no model execution · no autonomous approval ·
              no public-ready output · no invented facts, source IDs, metrics,
              URLs, or market numbers · no financial advice · no signal
              language. Every variant requires human review and remains
              not-public-postable.
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        {/* Draft variants */}
        <div className="space-y-6 xl:col-span-2">
          <Panel
            title={
              <span className="flex items-center gap-2">
                <IconSparkle className="h-4 w-4 text-accent" />
                Draft variants
              </span>
            }
            subtitle="Local fixtures · provider gate closed · human review required"
            actions={
              <span className="rounded-md border border-line bg-surface-2 px-1.5 py-0.5 font-mono text-[10.5px] text-fg-muted">
                {lab.outputs.length} variants
              </span>
            }
            bodyClassName="p-3 space-y-2.5"
          >
            {lab.outputs.map((v) => {
              const active =
                selected?.kind === 'ai_variant' &&
                selected.id === v.variant_id;
              return (
                <button
                  type="button"
                  key={v.variant_id}
                  id={`lab-variant-${v.variant_id}`}
                  onClick={() => select(selectAiVariant(v))}
                  className={`w-full rounded-lg border px-3.5 py-3 text-left transition-colors ${
                    active
                      ? 'border-accent/40 bg-accent/5'
                      : 'border-line bg-surface-2 hover:border-line-strong'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="flex items-center gap-2 text-sm font-semibold text-fg">
                      <span className="font-mono text-[11px] text-fg-subtle">
                        {v.variant_id}
                      </span>
                      {v.platform} · {v.audience_mode}
                    </span>
                    <StatusChip status={v.guardrail_status}>
                      {v.guardrail_status}
                    </StatusChip>
                  </div>
                  <p className="mt-1.5 line-clamp-2 text-[12px] leading-relaxed text-fg-muted">
                    {v.body}
                  </p>
                  <div className="mt-2 flex flex-wrap items-center gap-1.5">
                    <span className="rounded-md border border-line bg-surface-1 px-1.5 py-0.5 font-mono text-[10.5px] text-fg-subtle">
                      {v.style_mode}
                    </span>
                    <span className="rounded-md border border-line bg-surface-1 px-1.5 py-0.5 font-mono text-[10.5px] text-fg-subtle">
                      hook: {v.hook_type}
                    </span>
                    {v.hashtags.map((h) => (
                      <span
                        key={h}
                        className="font-mono text-[10.5px] text-accent"
                      >
                        {h}
                      </span>
                    ))}
                  </div>
                  <div className="mt-2.5 grid grid-cols-3 gap-2">
                    <MiniScore label="Editorial" value={v.editorial_score} />
                    <MiniScore label="SEO" value={v.seo_score} />
                    <MiniScore label="Platform" value={v.platform_fit_score} />
                  </div>
                  <div className="mt-2.5 flex items-center justify-between gap-2 border-t border-line pt-2">
                    <span className="text-[11px] text-fg-subtle">
                      {v.not_public_postable_reason}
                    </span>
                    <span className="shrink-0 font-mono text-[10.5px] text-status-blocked">
                      publish_ready: false
                    </span>
                  </div>
                </button>
              );
            })}
          </Panel>

          {/* Title & hook candidates from the selected/first variant */}
          <Panel
            title="Title & hook candidates"
            subtitle="Advisory suggestions · not a publish gate"
            bodyClassName="p-4 space-y-4"
          >
            <div>
              <SectionLabel>Title candidates</SectionLabel>
              <ul className="space-y-1.5">
                {lab.outputs[0].title_candidates.map((t, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2 text-sm text-fg-muted"
                  >
                    <span className="mt-0.5 font-mono text-[11px] text-fg-subtle">
                      {String(i + 1).padStart(2, '0')}
                    </span>
                    {t}
                  </li>
                ))}
              </ul>
            </div>
            <div className="border-t border-line pt-3">
              <SectionLabel>Audience &amp; style modes</SectionLabel>
              <div className="flex flex-wrap gap-1.5">
                {lab.audience_modes.map((a) => (
                  <span
                    key={a}
                    className="rounded-full border border-line bg-surface-2 px-2.5 py-0.5 text-[11px] text-fg-muted"
                  >
                    {a}
                  </span>
                ))}
                {lab.style_modes.map((s) => (
                  <span
                    key={s}
                    className="rounded-full border border-accent/30 bg-accent/5 px-2.5 py-0.5 text-[11px] text-accent"
                  >
                    {s}
                  </span>
                ))}
              </div>
            </div>
          </Panel>
        </div>

        {/* Right: SEO keyword groups */}
        <div className="space-y-6">
          <Panel
            title="SEO keyword groups"
            subtitle="Advisory only · select a group to inspect"
            bodyClassName="p-3 space-y-2"
          >
            {lab.keyword_groups.map((g) => {
              const active =
                selected?.kind === 'seo_keyword_group' &&
                selected.id === g.id;
              return (
                <button
                  type="button"
                  key={g.id}
                  id={`seo-group-${g.id}`}
                  onClick={() => select(selectSeoKeywordGroup(g))}
                  className={`w-full rounded-lg border px-3 py-2.5 text-left transition-colors ${
                    active
                      ? 'border-accent/40 bg-accent/5'
                      : 'border-line bg-surface-2 hover:border-line-strong'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm font-medium text-fg">
                      {g.label}
                    </span>
                    <StatusChip status={g.status}>{g.status}</StatusChip>
                  </div>
                  <p className="mt-0.5 text-[11px] text-fg-subtle">
                    {g.intent}
                  </p>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {g.keywords.map((k) => (
                      <span
                        key={k}
                        className="rounded border border-line bg-surface-1 px-1.5 py-0.5 text-[10.5px] text-fg-muted"
                      >
                        {k}
                      </span>
                    ))}
                  </div>
                </button>
              );
            })}
          </Panel>

          <Panel title="Guardrail status" bodyClassName="p-4">
            <ul className="space-y-2 text-sm">
              <GuardLine label="Provider call" value="none" />
              <GuardLine label="Model execution" value="none" />
              <GuardLine label="Autonomous approval" value="disabled" />
              <GuardLine label="Public-ready output" value="never" />
              <GuardLine label="Invented facts / IDs / URLs" value="forbidden" />
              <GuardLine label="Financial advice" value="forbidden" />
              <GuardLine label="Signal language" value="forbidden" />
            </ul>
          </Panel>
        </div>
      </div>
    </div>
  );
}

function MiniScore({ label, value }: { label: string; value: number }) {
  const status: StatusKind =
    value >= 80 ? 'verified' : value >= 60 ? 'review' : 'blocked';
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-[10.5px]">
        <span className="text-fg-subtle">{label}</span>
        <span className="font-mono font-semibold text-fg">{value}</span>
      </div>
      <ScoreBar value={value} status={status} />
    </div>
  );
}

function GuardLine({ label, value }: { label: string; value: string }) {
  return (
    <li className="flex items-center justify-between gap-2">
      <span className="flex items-center gap-2 text-fg-muted">
        <StatusDot status="verified" />
        {label}
      </span>
      <span className="font-mono text-[11px] text-status-verified">
        {value}
      </span>
    </li>
  );
}
