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

      <Panel title="Packet Sources" subtitle="Committed local evidence only">
        <dl className="space-y-3 text-sm">
          {[p.source_readiness_bundle, p.source_pipeline_matrix, p.source_substack_acceptance].map((path) => (
            <div key={path} className="rounded-lg border border-line bg-surface-2 p-3">
              <dt className="font-mono text-[10px] uppercase tracking-wide text-fg-subtle">source</dt>
              <dd className="mt-1 break-all font-mono text-[12px] text-fg-muted">{path}</dd>
            </div>
          ))}
        </dl>
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

      <LockedAction
        label="Publish / Dispatch / Verify public URL"
        reason="Disabled in TASK_0059. Public URL audit requires a separate operator-supplied URL artifact and no private data capture."
      />
    </div>
  );
}
