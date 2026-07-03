import { finalProductReadinessPacket as p } from '../data/finalProductReadinessPacket';
import { Panel, StatusChip, Metric, LockedAction } from '../ui/primitives';
import { IconShield, IconBlock } from '../ui/icons';

export function FinalProductReadinessPanel() {
  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 font-mono text-[11px] font-bold uppercase tracking-[0.14em] text-fg-subtle">
            Final Product Readiness · {p.task_label}
          </div>
          <h1 className="mt-2 flex items-center gap-2 text-2xl font-semibold tracking-tight text-fg">
            <IconShield className="h-6 w-6 text-accent" />
            Final Product Readiness
          </h1>
          <p className="mt-1 text-sm font-medium text-fg-muted">
            Evidence-grade final packet. Read-only, local-only, no live publish path.
          </p>
        </div>
        <StatusChip status="review" icon>{p.readiness_status}</StatusChip>
      </header>

      <div className="flex items-start gap-3 rounded-xl border border-status-blocked/30 bg-status-blocked/5 p-4">
        <IconBlock className="mt-0.5 h-4 w-4 shrink-0 text-status-blocked" />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold uppercase tracking-wide text-fg">
            LIVE ACTIONS LOCKED
          </p>
          <p className="mt-1 text-[12px] leading-relaxed text-fg-muted">
            Substack success is accepted by committed evidence, but public URL is not verified.
            No browser/CDP, provider, credential, env, or network action happens here.
          </p>
        </div>
      </div>

      <section aria-label="Readiness Verdict" className="rounded-2xl border border-accent/25 bg-accent/10 p-4 shadow-glow">
        <div className="grid gap-3 md:grid-cols-5">
          <p className="rounded-lg border border-line bg-surface-2 px-3 py-2 font-mono text-[12px] font-semibold text-accent">
            Verdict: {p.readiness_status}
          </p>
          <p className="rounded-lg border border-status-blocked/30 bg-status-blocked/10 px-3 py-2 text-sm font-semibold text-status-blocked">
            Dispatch: {p.dispatch_allowed_now ? 'allowed' : 'blocked'}
          </p>
          <p className="rounded-lg border border-status-blocked/30 bg-status-blocked/10 px-3 py-2 text-sm font-semibold text-status-blocked">
            Live write: {p.live_write_allowed_now ? 'allowed' : 'blocked'}
          </p>
          <p className="rounded-lg border border-status-review/30 bg-status-review/10 px-3 py-2 text-sm font-semibold text-status-review">
            Public URL: {p.substack_public_url_verified ? 'verified' : 'not verified'}
          </p>
          <p className="rounded-lg border border-line bg-surface-2 px-3 py-2 text-sm font-semibold text-fg">
            Next: Review V5 Final Product Readiness panel
          </p>
        </div>
      </section>

      <div className="grid gap-4 md:grid-cols-4">
        <Metric label="Lanes" value={String(p.lanes_summarized)} status="verified" hint="matrix rows" />
        <Metric label="Substack" value="accepted" status="verified" hint="TASK_0057 evidence" />
        <Metric label="Public URL" value="not verified" status="review" hint="safe audit pending" />
        <Metric label="Live write" value="locked" status="blocked" hint="dispatch_allowed_now=false" />
      </div>

      <Panel title="Operator Decision" subtitle="Read-only facts; no action enabled">
        <ul className="grid gap-2 text-sm md:grid-cols-2">
          <li className="rounded-lg border border-status-review/30 bg-status-review/10 px-3 py-2 font-semibold text-status-review">
            Ready for local operator review only
          </li>
          <li className="rounded-lg border border-status-verified/30 bg-status-verified/10 px-3 py-2 font-semibold text-status-verified">
            Substack live publish accepted by committed evidence
          </li>
          <li className="rounded-lg border border-status-review/30 bg-status-review/10 px-3 py-2 font-semibold text-status-review">
            Public URL not verified
          </li>
          <li className="rounded-lg border border-status-blocked/30 bg-status-blocked/10 px-3 py-2 font-semibold text-status-blocked">
            Dispatch/live write locked
          </li>
          <li className="rounded-lg border border-status-verified/30 bg-status-verified/10 px-3 py-2 font-semibold text-status-verified md:col-span-2">
            Browser/CDP/network/env/credential action not performed
          </li>
        </ul>
      </Panel>

      <Panel title="Evidence Trail" subtitle="Committed files supporting this verdict; no public/live URL links">
        <dl className="grid gap-3 text-sm md:grid-cols-2">
          {[
            ['TASK_0057 Substack acceptance reconciliation', p.source_substack_acceptance],
            ['V6 readiness evidence bundle', p.source_readiness_bundle],
            ['V6 pipeline status matrix', p.source_pipeline_matrix],
            ['Final readiness packet', 'docs/automation/V6_FINAL_PRODUCT_READINESS/final_product_readiness_packet.json'],
          ].map(([label, path]) => (
            <div key={label} className="rounded-lg border border-line bg-surface-2 p-3">
              <dt className="text-xs font-semibold text-fg">{label}</dt>
              <dd className="mt-1 break-all font-mono text-[12px] text-fg-muted">{path}</dd>
            </div>
          ))}
        </dl>
      </Panel>

      <Panel title="Remaining Blockers" subtitle="Why this is review-only, not dispatch-ready">
        <ul className="grid gap-2 text-sm md:grid-cols-2">
          <li className="rounded-lg border border-status-blocked/30 bg-status-blocked/10 px-3 py-2 font-semibold text-status-blocked">
            This is not dispatch clearance.
          </li>
          <li className="rounded-lg border border-status-review/30 bg-status-review/10 px-3 py-2 font-semibold text-status-review">
            Public URL verification is {p.substack_public_url_verified ? 'complete' : 'pending'}.
          </li>
          <li className="rounded-lg border border-status-blocked/30 bg-status-blocked/10 px-3 py-2 font-semibold text-status-blocked">
            Operator approval/live dispatch gates remain blocked: {p.blocked_lanes.join(', ')}.
          </li>
          <li className="rounded-lg border border-status-review/30 bg-status-review/10 px-3 py-2 font-semibold text-status-review">
            Future public URL audit must use operator-supplied public URL only.
          </li>
          <li className="rounded-lg border border-status-verified/30 bg-status-verified/10 px-3 py-2 font-semibold text-status-verified md:col-span-2">
            No browser/CDP/live/network/env/credential action is enabled here.
          </li>
        </ul>
      </Panel>

      <Panel title="Blocked Lanes" subtitle="Still not dispatch clearance">
        <div className="grid gap-2 md:grid-cols-2">
          {p.blocked_lanes.map((lane) => (
            <div key={lane} className="rounded-lg border border-line bg-surface-2 px-3 py-2 font-mono text-[12px] text-fg-muted">
              {lane}
            </div>
          ))}
        </div>
      </Panel>

      <Panel title="Safety Invariants" subtitle="All values must stay false">
        <div className="grid gap-2 md:grid-cols-2">
          {[
            ['dispatch_allowed_now', p.dispatch_allowed_now],
            ['live_write_allowed_now', p.live_write_allowed_now],
            ['browser_or_cdp_action_performed', p.browser_or_cdp_action_performed],
            ['network_call_performed', p.network_call_performed],
            ['env_or_credential_read_performed', p.env_or_credential_read_performed],
            ['raw_secret_output', p.raw_secret_output],
            ['private_url_or_dom_recorded', p.private_url_or_dom_recorded],
            ['public_postable', p.public_postable]
          ].map(([label, value]) => (
            <div key={String(label)} className="flex items-center justify-between rounded-lg border border-line bg-surface-2 px-3 py-2">
              <span className="font-mono text-[11px] text-fg-muted">{label}</span>
              <StatusChip status={value ? 'blocked' : 'verified'}>{String(value)}</StatusChip>
            </div>
          ))}
        </div>
      </Panel>

      <Panel title="Operator Handoff Checklist" subtitle="Safe next steps only; no dispatch clearance">
        <ul className="grid gap-2 text-sm md:grid-cols-2">
          {[
            'Review Final Readiness verdict',
            'Review Evidence Trail',
            'Confirm public URL is not verified',
            'Do not rerun live publish',
            'Use separate operator-supplied public URL audit only if needed',
            'Keep dispatch/live write locked',
          ].map((item) => (
            <li key={item} className="rounded-lg border border-line bg-surface-2 px-3 py-2 font-semibold text-fg-muted">
              {item}
            </li>
          ))}
        </ul>
      </Panel>

      <LockedAction
        label="Publish / Dispatch / Verify public URL"
        reason="Disabled in TASK_0059. Public URL audit requires a separate operator-supplied URL artifact and no private data capture."
      />
    </div>
  );
}
