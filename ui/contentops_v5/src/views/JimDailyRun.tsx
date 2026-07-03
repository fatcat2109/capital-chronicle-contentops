import { viewModel } from '../fixtures';
import { Metric, Panel, StatusChip } from '../ui/primitives';
import { IconShield } from '../ui/icons';

export function JimDailyRun() {
  const p = viewModel.jim_daily_content_run;
  const bundle = viewModel.jim_variant_preview_bundle;
  const manualWorkbench = viewModel.jim_manual_export_workbench;
  const flags = p.safety_flags;

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 font-mono text-[11px] font-bold uppercase tracking-[0.14em] text-fg-subtle">
            {p.surface_label} · {p.contract_version}
          </div>
          <h1 className="mt-2 flex items-center gap-2 text-2xl font-semibold tracking-tight text-fg">
            <IconShield className="h-6 w-6 text-accent" />
            Jim Daily Content Run
          </h1>
          <p className="mt-1 text-sm font-medium text-fg-muted">
            Jim final review required. Local-only daily content run packet; no provider API, no platform dispatch.
          </p>
        </div>
        <StatusChip status="review" icon>{p.run_status}</StatusChip>
      </header>

      <div className="grid gap-4 md:grid-cols-4">
        <Metric label="Operator" value="Jim" status="review" hint="final review required" />
        <Metric label="Ideas" value={String(p.ideas.length)} status="review" hint="lane-classified" />
        <Metric label="Lane C" value="blocked" status="blocked" hint="artifact evidence missing" />
        <Metric label="Dispatch" value="locked" status="blocked" hint="dispatch_ready=false" />
      </div>

      <Panel title="Next Allowed Manual Step" subtitle="Review-only; no execution path">
        <div className="rounded-lg border border-status-review/30 bg-status-review/10 px-3 py-2 text-sm font-semibold text-status-review">
          {p.next_allowed_action}
        </div>
      </Panel>

      <Panel title="Daily Idea Queue" subtitle="Lane, blocker, and manual-step map for Jim">
        <div className="grid gap-3">
          {p.ideas.map((item) => (
            <article key={item.idea_id} className="rounded-xl border border-line bg-surface-2 p-4">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <h2 className="text-sm font-semibold text-fg">{item.title}</h2>
                  <p className="mt-1 font-mono text-[11px] text-fg-subtle">{item.idea_id} · {item.lane}</p>
                </div>
                <StatusChip status={item.status === 'BLOCKED' ? 'blocked' : 'review'}>{item.status}</StatusChip>
              </div>
              <dl className="mt-3 grid gap-2 text-sm md:grid-cols-2">
                <div>
                  <dt className="font-mono text-[10.5px] uppercase text-fg-muted">Source</dt>
                  <dd className="mt-1 text-fg">{item.source_type}</dd>
                </div>
                <div>
                  <dt className="font-mono text-[10.5px] uppercase text-fg-muted">Next manual step</dt>
                  <dd className="mt-1 text-fg">{item.next_allowed_manual_step}</dd>
                </div>
              </dl>
              {item.blockers.length > 0 && (
                <ul className="mt-3 grid gap-2">
                  {item.blockers.map((blocker) => (
                    <li key={blocker} className="rounded-lg border border-status-blocked/30 bg-status-blocked/10 px-3 py-2 text-sm font-semibold text-status-blocked">
                      {blocker}
                    </li>
                  ))}
                </ul>
              )}
            </article>
          ))}
        </div>
      </Panel>


      <Panel title="Content Intent + Platform Variant Preview Bundle" subtitle="Placeholder previews only; no final public copy">
        <div className="grid gap-3 md:grid-cols-3">
          <div className="rounded-lg border border-status-review/30 bg-status-review/10 px-3 py-2">
            <div className="font-mono text-[10.5px] uppercase text-fg-muted">Bundle status</div>
            <div className="mt-1 text-sm font-semibold text-status-review">{bundle.bundle_status}</div>
          </div>
          <div className="rounded-lg border border-line bg-surface-2 px-3 py-2">
            <div className="font-mono text-[10.5px] uppercase text-fg-muted">Platform previews</div>
            <div className="mt-1 text-sm font-semibold text-fg">{bundle.platform_preview_count}</div>
          </div>
          <div className="rounded-lg border border-status-blocked/30 bg-status-blocked/10 px-3 py-2">
            <div className="font-mono text-[10.5px] uppercase text-fg-muted">Manual export</div>
            <div className="mt-1 text-sm font-semibold text-status-blocked">not ready</div>
          </div>
        </div>
        <div className="mt-4 grid gap-3">
          {bundle.content_intents.map((intent) => (
            <article key={intent.intent_id} className="rounded-xl border border-line bg-surface-2 p-4">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <h2 className="text-sm font-semibold text-fg">{intent.title}</h2>
                  <p className="mt-1 font-mono text-[11px] text-fg-subtle">{intent.intent_id} · {intent.claim_risk}</p>
                </div>
                <StatusChip status={intent.status === 'BLOCKED' ? 'blocked' : 'review'}>{intent.status}</StatusChip>
              </div>
              <p className="mt-2 text-sm text-fg-muted">{intent.draft_objective}</p>
              <div className="mt-3 grid gap-2 md:grid-cols-2">
                {bundle.platform_previews.filter((preview) => preview.source_intent_id === intent.intent_id).map((preview) => (
                  <div key={preview.preview_id} className="rounded-lg border border-line bg-surface-1 p-3">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-semibold text-fg">{preview.platform}</span>
                      <StatusChip status={preview.preview_status === 'BLOCKED_WAITING_FOR_INPUTS' ? 'blocked' : 'review'}>{preview.preview_status}</StatusChip>
                    </div>
                    <p className="mt-2 text-xs leading-relaxed text-fg-muted">{preview.preview_text_excerpt}</p>
                    <p className="mt-2 font-mono text-[10.5px] text-status-blocked">manual_export_ready=false · dispatch_ready=false</p>
                  </div>
                ))}
              </div>
            </article>
          ))}
        </div>
      </Panel>


      <Panel title="Manual Export + Approval Packet Workbench" subtitle="Read-only packets; Jim approval required before any manual copy">
        <div className="grid gap-3 md:grid-cols-4">
          <div className="rounded-lg border border-status-review/30 bg-status-review/10 px-3 py-2">
            <div className="font-mono text-[10.5px] uppercase text-fg-muted">Workbench status</div>
            <div className="mt-1 text-sm font-semibold text-status-review">{manualWorkbench.workbench_status}</div>
          </div>
          <div className="rounded-lg border border-line bg-surface-2 px-3 py-2">
            <div className="font-mono text-[10.5px] uppercase text-fg-muted">Export packets</div>
            <div className="mt-1 text-sm font-semibold text-fg">{manualWorkbench.export_packet_count}</div>
          </div>
          <div className="rounded-lg border border-status-review/30 bg-status-review/10 px-3 py-2">
            <div className="font-mono text-[10.5px] uppercase text-fg-muted">Ready after Jim approval</div>
            <div className="mt-1 text-sm font-semibold text-status-review">{manualWorkbench.ready_export_packet_count}</div>
          </div>
          <div className="rounded-lg border border-status-blocked/30 bg-status-blocked/10 px-3 py-2">
            <div className="font-mono text-[10.5px] uppercase text-fg-muted">Valid for dispatch</div>
            <div className="mt-1 text-sm font-semibold text-status-blocked">false</div>
          </div>
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {manualWorkbench.manual_export_packets.slice(0, 6).map((packet) => (
            <article key={packet.export_packet_id} className="rounded-xl border border-line bg-surface-2 p-4">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <h2 className="text-sm font-semibold text-fg">{packet.platform} manual export packet</h2>
                  <p className="mt-1 font-mono text-[11px] text-fg-subtle">{packet.export_packet_id}</p>
                </div>
                <StatusChip status={packet.manual_export_status === 'BLOCKED_WAITING_FOR_INPUTS' ? 'blocked' : 'review'}>{packet.manual_export_status}</StatusChip>
              </div>
              <p className="mt-2 text-xs leading-relaxed text-fg-muted">{packet.title}</p>
              <p className="mt-2 font-mono text-[10.5px] text-status-blocked">public_postable=false · dispatch_ready=false · public_url_verified=false</p>
            </article>
          ))}
        </div>
        <div className="mt-4 rounded-lg border border-status-blocked/30 bg-status-blocked/10 p-3 text-xs leading-relaxed text-status-blocked">
          Approval records are previews only: valid_for_dispatch=false. No buttons, no links, no inputs, no URL fields, no platform writes.
        </div>
      </Panel>

      <Panel title="Variant Preview Safety Flags" subtitle="False keeps bundle non-live and non-public-postable">
        <div className="grid gap-2 md:grid-cols-2">
          {[
            ['final_public_copy_created', bundle.safety_flags.final_public_copy_created],
            ['llm_provider_called', bundle.safety_flags.llm_provider_called],
            ['platform_api_called', bundle.safety_flags.platform_api_called],
            ['public_postable', bundle.safety_flags.public_postable],
            ['publish_ready', bundle.safety_flags.publish_ready],
            ['dispatch_ready', bundle.safety_flags.dispatch_ready],
          ].map(([label, value]) => (
            <div key={String(label)} className="flex items-center justify-between rounded-lg border border-line bg-surface-2 px-3 py-2">
              <span className="font-mono text-[11px] text-fg-muted">{label}</span>
              <StatusChip status={value ? 'blocked' : 'verified'}>{String(value)}</StatusChip>
            </div>
          ))}
        </div>
      </Panel>

      <Panel title="Forbidden Actions" subtitle="Hard boundaries for TASK_0077">
        <ul className="grid gap-2 text-sm md:grid-cols-2">
          {p.forbidden_actions.map((action) => (
            <li key={action} className="rounded-lg border border-status-blocked/30 bg-status-blocked/10 px-3 py-2 font-semibold text-status-blocked">
              {action}
            </li>
          ))}
        </ul>
      </Panel>

      <Panel title="Safety Flags" subtitle="False means no live/provider/platform/browser action occurred">
        <div className="grid gap-2 md:grid-cols-2">
          {[
            ['public_postable', flags.public_postable],
            ['publish_ready', flags.publish_ready],
            ['dispatch_ready', flags.dispatch_ready],
            ['provider_api_called', flags.provider_api_called],
            ['network_called', flags.network_called],
            ['browser_or_cdp_used', flags.browser_or_cdp_used],
            ['credential_or_env_read', flags.credential_or_env_read],
            ['platform_dispatch_performed', flags.platform_dispatch_performed],
          ].map(([label, value]) => (
            <div key={String(label)} className="flex items-center justify-between rounded-lg border border-line bg-surface-2 px-3 py-2">
              <span className="font-mono text-[11px] text-fg-muted">{label}</span>
              <StatusChip status={value ? 'blocked' : 'verified'}>{String(value)}</StatusChip>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}
