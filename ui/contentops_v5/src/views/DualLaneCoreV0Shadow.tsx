import { dualLaneCoreV0ShadowPacket as p } from '../data/dualLaneCoreV0ShadowPacket';
import { Panel, StatusChip, Metric } from '../ui/primitives';
import { IconShield, IconBlock } from '../ui/icons';

/**
 * Read-only operator view of one dual-lane CORE V0 shadow newsroom run.
 * Local-only: no network, no credentials, no dispatch path.
 */
export function DualLaneCoreV0Shadow() {
  const news = p.newsroom_lane;
  const capital = p.capital_chronicle_lane;

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 font-mono text-[11px] font-bold uppercase tracking-[0.14em] text-fg-subtle">
            Dual-Lane CORE V0 · {p.task_label}
          </div>
          <h1 className="mt-2 flex items-center gap-2 text-2xl font-semibold tracking-tight text-fg">
            <IconShield className="h-6 w-6 text-accent" />
            Dual-Lane Shadow Newsroom
          </h1>
          <p className="mt-1 text-sm font-medium text-fg-muted">
            One local run of both input lanes. Zero public writes.
          </p>
        </div>
        <StatusChip status="review" icon>{p.operating_mode}</StatusChip>
      </header>

      <div className="flex items-start gap-3 rounded-xl border border-status-blocked/30 bg-status-blocked/5 p-4">
        <IconBlock className="mt-0.5 h-4 w-4 shrink-0 text-status-blocked" />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold uppercase tracking-wide text-fg">
            LIVE ACTIONS LOCKED — SHADOW_ONLY
          </p>
          <p className="mt-1 text-[12px] leading-relaxed text-fg-muted">
            Publication, dispatch, and public-write authority are all false. No credential
            read, provider call, browser/CDP action, network intake, or scheduler execution
            occurred in this run.
          </p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Metric label="Publication" value="false" status="blocked" hint="no authority" />
        <Metric label="Dispatch" value="false" status="blocked" hint="no authority" />
        <Metric label="Public write" value="false" status="blocked" hint="no authority" />
        <Metric
          label="Replay"
          value={p.replay_verification.all_replays_valid ? 'valid' : 'invalid'}
          status={p.replay_verification.all_replays_valid ? 'verified' : 'blocked'}
          hint={`${p.replay_verification.work_items_replayed} work items`}
        />
      </div>

      <Panel title="Newsroom lane" subtitle={`${news.decision} · ${news.outcome}`}>
        <div className="grid gap-3 md:grid-cols-4">
          <Metric label="Candidates" value={String(news.candidate_count)} status="verified" hint="governed universe" />
          <Metric label="Clusters" value={String(news.cluster_count)} status="verified" hint="dedupe + update chains" />
          <Metric label="Held" value={String(news.held_count)} status="review" hint="gated candidates" />
          <Metric
            label="Review"
            value={String(p.newsroom_review.result)}
            status={p.newsroom_review.result === 'PASS' ? 'verified' : 'blocked'}
            hint={`${p.newsroom_review.role_count} roles`}
          />
        </div>
        <p className="mt-3 text-[12px] leading-relaxed text-fg-muted">
          Selected: <span className="font-mono text-fg">{String(news.selected_candidate_id ?? 'NONE — abstained')}</span>
        </p>
        <p className="mt-1 text-[12px] leading-relaxed text-fg-muted">
          {'why_selected' in p.newsroom_selection_reason
            ? String(p.newsroom_selection_reason.why_selected)
            : String((p.newsroom_selection_reason as { why_abstained?: string }).why_abstained ?? '')}
        </p>
        <p className="mt-2 text-[12px] text-fg-muted">
          Domains covered: <span className="font-mono text-fg">{news.domains_covered.join(', ')}</span>
        </p>
        <ul className="mt-3 space-y-1">
          {p.newsroom_held_candidates.map((row) => (
            <li key={row.candidate_id} className="font-mono text-[11px] text-fg-muted">
              HELD {row.candidate_id} — {row.blockers.join(', ')}
            </li>
          ))}
        </ul>
      </Panel>

      <Panel title="Capital Chronicle lane" subtitle={String(capital.outcome)}>
        <div className="grid gap-3 md:grid-cols-4">
          <Metric label="Packet" value={String(capital.packet_id).slice(0, 18)} status="verified" hint="governed v3" />
          <Metric label="Claims" value={String(capital.authorized_claim_count)} status="verified" hint="authorized only" />
          <Metric
            label="Chart series"
            value={capital.chart_series_status === 'NO_AUTHORIZED_CHART_SERIES' ? 'none' : 'present'}
            status="review"
            hint="never fabricated"
          />
          <Metric
            label="Review"
            value={String(p.capital_chronicle_review.result)}
            status={p.capital_chronicle_review.result === 'PASS' ? 'verified' : 'blocked'}
            hint={`${p.capital_chronicle_review.role_count} roles`}
          />
        </div>
        <p className="mt-3 text-[12px] leading-relaxed text-fg-muted">
          Analytical fidelity: <span className="font-mono text-fg">{String(capital.analytical_fidelity_result)}</span>
        </p>
        <p className="mt-1 text-[12px] leading-relaxed text-fg-muted">{p.capital_chronicle_chart_reason}</p>
      </Panel>

      <Panel title="Package + platform capability" subtitle="Tier-1 destinations">
        <div className="grid gap-3 md:grid-cols-3">
          <Metric label="Tier-1 total" value={String(p.platform_capability.tier1_destination_count)} status="verified" />
          <Metric label="Supported" value={String(p.platform_capability.supported_count)} status="verified" hint="dry-run payloads" />
          <Metric label="Unsupported" value={String(p.platform_capability.unsupported_count)} status="review" hint="reported, not omitted" />
        </div>
        <p className="mt-3 font-mono text-[11px] text-fg-muted">
          Deferred: {p.platform_capability.unsupported_destinations.join(', ')}
        </p>
      </Panel>

      <Panel title="Durable shadow state" subtitle="terminal states and replay">
        <ul className="space-y-1">
          {p.durable_work_item_ids.map((id) => (
            <li key={id} className="font-mono text-[11px] text-fg-muted">
              {id} — <span className="text-fg">{String(
                (p.durable_terminal_states as Record<string, string>)[id],
              )}</span>
            </li>
          ))}
        </ul>
        <p className="mt-3 text-[12px] text-fg-muted">
          Shadow readback: <span className="font-mono text-fg">{p.shadow_readback.readback_kind}</span> ·
          public objects created: <span className="font-mono text-fg">{p.shadow_readback.public_objects_created}</span>
        </p>
      </Panel>
    </div>
  );
}
