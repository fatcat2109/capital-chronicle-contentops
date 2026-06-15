// Capital Chronicle ContentOps V5 — Writer Studio view.
// Includes UI-only AI Writer / SEO panels and a mock Media Tray.
// No provider calls. No autonomous approval. No public-ready claim.
// No real file picker/read/upload. No network, no storage, no credentials.

import { useApp } from '../state';
import { viewModel } from '../fixtures';
import { Panel, StatusChip } from '../ui/primitives';

export function WriterStudio() {
  const { select } = useApp();
  const d = viewModel.editorial_draft;

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-fg">
            Writer Studio
          </h1>
          <p className="mt-1 text-sm text-fg-muted">
            Editorial draft <span className="font-mono">{d.id}</span> ·
            review-only. AI Writer and SEO are UI-only assists; no provider
            call, no autonomous approval, not public-ready.
          </p>
        </div>
        <StatusChip status="review">REVIEW ONLY</StatusChip>
      </header>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        {/* Editor lane */}
        <div className="space-y-6 xl:col-span-2">
          <Panel title={d.title}>
            <div className="mb-3 flex flex-wrap gap-2">
              {d.platform_tabs.map((p) => (
                <span
                  key={p}
                  className="rounded border border-line bg-surface-2 px-2 py-0.5 font-mono text-[11px] text-fg-muted"
                >
                  {p}
                </span>
              ))}
            </div>
            <ol className="mb-4 list-decimal space-y-1 pl-5 text-sm text-fg">
              {d.outline.map((o, i) => (
                <li key={i}>{o}</li>
              ))}
            </ol>
            <p className="rounded-md border border-line bg-surface-2 p-3 text-sm text-fg">
              {d.body_excerpt}
            </p>
            <div className="mt-4 rounded-md border border-status-review/40 bg-status-review/10 p-3">
              <div className="font-mono text-[11px] font-bold uppercase tracking-wide text-status-review">
                Limitation note (preserved)
              </div>
              <p className="mt-1 text-sm text-fg">{d.limitation_note}</p>
            </div>
          </Panel>

          {/* Media Tray — mock only */}
          <Panel
            title="Media Tray"
            actions={<StatusChip status="neutral">MOCK ONLY</StatusChip>}
          >
            <p className="mb-3 text-xs text-fg-muted">
              UI mock. No real file picker, read, or upload. Assets are
              local fixtures used for layout and rights/constraints review.
            </p>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {d.media.map((m) => (
                <button
                  type="button"
                  key={m.id}
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
                        { label: 'Constraints', value: m.platform_constraints.join(' · ') },
                      ],
                    })
                  }
                  className={`rounded-md border p-3 text-left transition-colors ${
                    m.selected
                      ? 'border-fg/30 bg-surface-3'
                      : 'border-line bg-surface-2 hover:bg-surface-3'
                  }`}
                >
                  {/* Placeholder swatch — no external image URL */}
                  <div
                    className="mb-2 flex h-24 w-full items-center justify-center rounded border border-line bg-bg font-mono text-[11px] text-fg-muted"
                    aria-hidden
                  >
                    {m.kind}
                  </div>
                  <div className="truncate font-mono text-[12px] text-fg">
                    {m.name}
                  </div>
                  <div className="mt-1 flex items-center justify-between">
                    <StatusChip status={m.rights_status}>
                      {m.rights_label}
                    </StatusChip>
                    {m.selected && (
                      <span className="font-mono text-[11px] text-fg-muted">
                        selected
                      </span>
                    )}
                  </div>
                </button>
              ))}
            </div>
          </Panel>
        </div>

        {/* Assist rail */}
        <div className="space-y-6">
          {/* AI Writer — UI only */}
          <Panel
            title="AI Writer"
            actions={<StatusChip status="review">UI-ONLY</StatusChip>}
          >
            <p className="mb-3 text-xs text-fg-muted">
              No provider call. Variants are illustrative and require human
              review. Not public-postable.
            </p>
            <div className="space-y-3">
              {d.ai_outputs.map((a) => (
                <div
                  key={a.variant_id}
                  className="rounded-md border border-line bg-surface-2 p-3"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[12px] text-fg">
                      {a.variant_id} · {a.platform}
                    </span>
                    <StatusChip status={a.guardrail_status}>
                      guardrail
                    </StatusChip>
                  </div>
                  <div className="mt-1 text-xs text-fg-muted">
                    {a.audience_mode} · {a.style_mode}
                  </div>
                  <div className="mt-2 flex flex-wrap gap-1">
                    <span className="rounded border border-status-blocked/40 bg-status-blocked/10 px-1.5 py-0.5 font-mono text-[11px] text-status-blocked">
                      publish_ready: false
                    </span>
                    <span className="rounded border border-line bg-bg px-1.5 py-0.5 font-mono text-[11px] text-fg-muted">
                      human_review_required
                    </span>
                  </div>
                  <p className="mt-2 font-mono text-[11px] text-fg-muted">
                    {a.not_public_postable_reason}
                  </p>
                </div>
              ))}
            </div>
          </Panel>

          {/* SEO panel — UI only */}
          <Panel
            title="SEO & Editorial Score"
            actions={<StatusChip status="neutral">ADVISORY</StatusChip>}
          >
            <div className="grid grid-cols-3 gap-2">
              <ScoreCell label="Editorial" value={d.seo.editorial_score} />
              <ScoreCell label="SEO" value={d.seo.seo_score} />
              <ScoreCell label="Platform" value={d.seo.platform_fit_score} />
            </div>
            <div className="mt-3">
              <div className="font-mono text-[11px] uppercase text-fg-muted">
                Keywords
              </div>
              <div className="mt-1 flex flex-wrap gap-1">
                {d.seo.keywords.map((k) => (
                  <span
                    key={k}
                    className="rounded border border-line bg-surface-2 px-1.5 py-0.5 font-mono text-[11px] text-fg-muted"
                  >
                    {k}
                  </span>
                ))}
              </div>
            </div>
            <div className="mt-3">
              <div className="font-mono text-[11px] uppercase text-fg-muted">
                Title candidates
              </div>
              <ul className="mt-1 space-y-1 text-sm text-fg">
                {d.seo.title_candidates.map((t, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="font-mono text-[11px] text-fg-muted">
                      {i + 1}.
                    </span>
                    {t}
                  </li>
                ))}
              </ul>
            </div>
            <div className="mt-3">
              <div className="font-mono text-[11px] uppercase text-fg-muted">
                Hook variants
              </div>
              <ul className="mt-1 space-y-1 text-sm text-fg">
                {d.seo.hook_variants.map((h, i) => (
                  <li key={i}>{h}</li>
                ))}
              </ul>
            </div>
            <p className="mt-3 font-mono text-[11px] text-fg-muted">
              Readability: {d.seo.readability}
            </p>
          </Panel>

          {/* Guardrails */}
          <Panel title="Editorial guardrails">
            <ul className="space-y-2">
              {d.guardrails.map((g) => (
                <li
                  key={g.id}
                  className="flex items-center justify-between text-sm"
                >
                  <span className="text-fg-muted">{g.label}</span>
                  <StatusChip status={g.status}>{g.status}</StatusChip>
                </li>
              ))}
            </ul>
          </Panel>
        </div>
      </div>
    </div>
  );
}

function ScoreCell({ label, value }: { label: string; value: number }) {
  const status = value >= 80 ? 'verified' : value >= 60 ? 'review' : 'blocked';
  return (
    <div className="rounded-md border border-line bg-surface-2 px-2 py-2 text-center">
      <div className="font-mono text-[10px] uppercase text-fg-muted">
        {label}
      </div>
      <div
        className={`mt-1 text-lg font-semibold ${
          status === 'verified'
            ? 'text-status-verified'
            : status === 'review'
              ? 'text-status-review'
              : 'text-status-blocked'
        }`}
      >
        {value}
      </div>
    </div>
  );
}
