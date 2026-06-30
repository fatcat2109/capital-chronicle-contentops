import { substackManualExportArticleStudioPacket as packet } from '../data/substackManualExportArticleStudioAdapter';
import { StatusChip } from '../ui/primitives';

export function SubstackArticleStudioCard({ mode }: { mode: 'writer' | 'seo' | 'preview' | 'manual' | 'approval' | 'evidence' }) {
  const labels = packet.manual_copy_payload.safety_labels;
  return (
    <section id={`v6-substack-article-studio-${mode}`} className="rounded-2xl border border-line bg-surface-1 p-4 shadow-card">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="font-mono text-[10.5px] font-bold uppercase tracking-[0.14em] text-accent">
            V6 Substack manual export · {mode}
          </div>
          <h2 className="mt-1 text-lg font-semibold tracking-tight text-fg">Canonical article studio lane</h2>
          <p className="mt-1 max-w-3xl text-sm text-fg-muted">{packet.article_title}</p>
        </div>
        <StatusChip status="review" icon>{packet.approval_status}</StatusChip>
      </div>

      <div className="mt-4 flex flex-wrap gap-1.5">
        {labels.map((label) => (
          <span key={label} className="rounded-md border border-line bg-surface-2 px-2 py-1 font-mono text-[10.5px] text-fg-muted">
            {label}
          </span>
        ))}
      </div>

      <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-3">
        <div className="rounded-xl border border-line bg-surface-2 p-3">
          <div className="font-mono text-[10px] font-bold uppercase text-fg-subtle">Export packet</div>
          <div className="mt-1 break-all font-mono text-[11px] text-fg">{packet.export_packet_id}</div>
        </div>
        <div className="rounded-xl border border-line bg-surface-2 p-3">
          <div className="font-mono text-[10px] font-bold uppercase text-fg-subtle">Exact preview hash</div>
          <div className="mt-1 break-all font-mono text-[11px] text-fg">{packet.exact_payload_hash}</div>
        </div>
        <div className="rounded-xl border border-line bg-surface-2 p-3">
          <div className="font-mono text-[10px] font-bold uppercase text-fg-subtle">Live state</div>
          <div className="mt-1 font-mono text-[11px] text-status-blocked">live_publish_allowed={String(packet.live_publish_allowed)}</div>
          <div className="font-mono text-[11px] text-status-blocked">provider_call_made={String(packet.provider_call_made)}</div>
        </div>
      </div>

      {mode === 'seo' && (
        <div className="mt-4 rounded-xl border border-line bg-surface-2 p-3">
          <div className="font-mono text-[10px] font-bold uppercase text-fg-subtle">SEO metadata</div>
          <div className="mt-2 text-sm font-semibold text-fg">{packet.seo_title}</div>
          <p className="mt-1 text-sm text-fg-muted">{packet.seo_description}</p>
        </div>
      )}

      {(mode === 'preview' || mode === 'manual') && (
        <pre className="mt-4 max-h-72 overflow-auto whitespace-pre-wrap rounded-xl border border-line bg-surface-2 p-3 font-mono text-[11px] leading-relaxed text-fg-muted">
          {packet.article_body_markdown}
        </pre>
      )}

      {(mode === 'approval' || mode === 'evidence') && (
        <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2">
          {packet.blockers.map((blocker) => (
            <div key={blocker} className="rounded-xl border border-status-blocked/30 bg-status-blocked/5 p-3 font-mono text-[11px] text-status-blocked">
              {blocker}
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
