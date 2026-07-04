import { v6CommandCenter as p } from '../fixtures';
import { LockedAction, Metric, Panel, StatusChip } from '../ui/primitives';
import { IconShield } from '../ui/icons';

export function V6CommandCenter() {
  const flow = p.final_operator_product_flow;

  return (
    <div className="space-y-6">
      <header className="overflow-hidden rounded-3xl border border-accent/25 bg-gradient-to-br from-accent/25 via-surface-1 to-surface-2 p-5 shadow-float">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2 font-mono text-[11px] font-bold uppercase tracking-[0.14em] text-fg-subtle">
              V6 Final Operator Cockpit · {flow.task_label}
            </div>
            <h1 className="mt-2 flex items-center gap-2 text-3xl font-semibold tracking-tight text-fg">
              <IconShield className="h-7 w-7 text-accent" />
              Jim Source-to-Audit Command Center
            </h1>
            <p className="mt-2 max-w-4xl text-sm font-medium leading-relaxed text-fg-muted">
              One local cockpit for source intake, canonical draft review, exact hash approval,
              full-platform variants, source-aware media selection, and manual audit handoff.
              Builder: {flow.builder_version} · packet={flow.packet_id} · hash={flow.packet_hash}
            </p>
          </div>
          <StatusChip status="verified" icon>{p.final_verdict}</StatusChip>
        </div>
      </header>

      <section aria-label="Jim Source-to-Audit Operator Flow" className="rounded-2xl border border-accent/25 bg-accent/10 p-4 shadow-glow">
        <div className="grid gap-3 md:grid-cols-6">
          {flow.flow_stages.map((stage, index) => (
            <article key={stage.stage_id} className="relative rounded-xl border border-line bg-surface-1 p-3 shadow-card">
              <div className="flex items-center justify-between gap-2">
                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-accent font-mono text-[11px] font-bold text-bg">
                  {index + 1}
                </span>
                <StatusChip status={stage.status}>{stage.status}</StatusChip>
              </div>
              <h2 className="mt-3 text-sm font-semibold text-fg">{stage.label}</h2>
              <p className="mt-2 text-[12px] leading-relaxed text-fg-muted">{stage.summary}</p>
              <p className="mt-3 break-all font-mono text-[10.5px] text-fg-subtle">{stage.evidence_ref}</p>
            </article>
          ))}
        </div>
      </section>

      <div className="grid gap-4 md:grid-cols-4">
        <Metric label="Platforms" value={String(flow.platform_universe.length)} status="verified" hint="full north-star universe" />
        <Metric label="Flow stages" value={String(flow.flow_stages.length)} status="review" hint="source → audit" />
        <Metric label="Source classes" value={String(flow.source_classes.length)} status="review" hint={flow.source_classes.join(' / ')} />
        <Metric label="Live dispatch" value="locked" status="blocked" hint="manual remains fallback" />
      </div>

      <Panel title="Full Platform Universe" subtitle="Productized as advisory/manual evidence lanes; no platform API or live execution">
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {flow.platform_universe.map((row) => (
            <article key={row.platform} className="rounded-xl border border-line bg-surface-2 p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h2 className="text-sm font-semibold text-fg">{row.platform}</h2>
                  <p className="mt-1 text-[12px] text-fg-muted">{row.role}</p>
                </div>
                <StatusChip status={row.status}>{row.status}</StatusChip>
              </div>
              <p className="mt-3 font-mono text-[10.5px] font-semibold uppercase text-fg-subtle">{row.posture}</p>
              <p className="mt-2 text-[12px] leading-relaxed text-fg-muted">{row.manual_action}</p>
              <dl className="mt-3 grid gap-1 border-t border-line pt-3 text-[11px]">
                <div><dt className="font-mono uppercase text-fg-subtle">Variant</dt><dd className="break-all text-fg-muted">{row.variant_key}</dd></div>
                <div><dt className="font-mono uppercase text-fg-subtle">Payload hash</dt><dd className="break-all font-mono text-fg-muted">{row.payload_hash}</dd></div>
                <div><dt className="font-mono uppercase text-fg-subtle">Media fit</dt><dd className="text-fg-muted">{row.media_fit}</dd></div>
                <div><dt className="font-mono uppercase text-fg-subtle">Dispatch gate</dt><dd className="font-mono text-fg-muted">{row.dispatch_gate}</dd></div>
              </dl>
            </article>
          ))}
        </div>
      </Panel>

      <div className="grid gap-4 xl:grid-cols-2">
        <Panel title="News Image Candidate Lane" subtitle={flow.media_lane.news_policy}>
          <div className="mb-3 rounded-lg border border-status-review/30 bg-status-review/10 px-3 py-2 font-mono text-[11px] font-bold text-status-review">
            topic={flow.media_lane.news_topic_id} · metadata_only=true · google_scrape=false
          </div>
          <div className="grid gap-3">
            {flow.media_lane.news_candidates.map((candidate) => (
              <article key={candidate.candidate_id} className="rounded-xl border border-line bg-surface-2 p-4">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <h3 className="text-sm font-semibold text-fg">{candidate.title}</h3>
                    <p className="mt-1 font-mono text-[10.5px] text-fg-subtle">{candidate.candidate_id}</p>
                  </div>
                  <StatusChip status={candidate.rights_status}>rights {candidate.rights_status}</StatusChip>
                </div>
                <dl className="mt-3 grid gap-2 text-[12px]">
                  <div><dt className="font-mono text-[10.5px] uppercase text-fg-subtle">Search query</dt><dd className="mt-1 text-fg-muted">{candidate.search_query}</dd></div>
                  <div><dt className="font-mono text-[10.5px] uppercase text-fg-subtle">Source URL metadata</dt><dd className="mt-1 break-all text-fg-muted">{candidate.source_url_metadata}</dd></div>
                  <div><dt className="font-mono text-[10.5px] uppercase text-fg-subtle">Image URL metadata</dt><dd className="mt-1 break-all text-fg-muted">{candidate.image_url_metadata}</dd></div>
                  <div><dt className="font-mono text-[10.5px] uppercase text-fg-subtle">Metadata hash</dt><dd className="mt-1 break-all font-mono text-fg-muted">{candidate.metadata_hash}</dd></div>
                  <div><dt className="font-mono text-[10.5px] uppercase text-fg-subtle">Selected platforms</dt><dd className="mt-1 text-fg-muted">{candidate.selected_for_platforms.join(', ')}</dd></div>
                  <div><dt className="font-mono text-[10.5px] uppercase text-fg-subtle">License notes</dt><dd className="mt-1 text-fg-muted">{candidate.license_notes}</dd></div>
                  <div><dt className="font-mono text-[10.5px] uppercase text-fg-subtle">Relevance</dt><dd className="mt-1 text-fg-muted">{candidate.relevance_notes}</dd></div>
                </dl>
              </article>
            ))}
          </div>
        </Panel>

        <Panel title="Internal Report Chart/Card Lane" subtitle={flow.media_lane.internal_policy}>
          <div className="mb-3 rounded-lg border border-status-verified/30 bg-status-verified/10 px-3 py-2 font-mono text-[11px] font-bold text-status-verified">
            report={flow.media_lane.internal_report_id} · built_in_chart_preferred=true
          </div>
          <div className="grid gap-3">
            {flow.media_lane.internal_chart_candidates.map((chart) => (
              <article key={chart.chart_id} className="rounded-xl border border-line bg-surface-2 p-4">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <h3 className="text-sm font-semibold text-fg">{chart.title}</h3>
                    <p className="mt-1 font-mono text-[10.5px] text-fg-subtle">{chart.chart_id} · {chart.format}</p>
                  </div>
                  <StatusChip status={chart.rights_status}>rights {chart.rights_status}</StatusChip>
                </div>
                <p className="mt-3 text-[12px] text-fg-muted">{chart.source_report}</p>
                <p className="mt-2 text-[12px] leading-relaxed text-fg-muted">{chart.fit_notes}</p>
                <p className="mt-2 font-mono text-[10.5px] text-fg-subtle">media_hash={chart.media_hash} · platforms={chart.selected_for_platforms.join(', ')}</p>
                <p className="mt-3 rounded-lg border border-line bg-surface-1 px-3 py-2 text-[12px] text-fg-muted">alt: {chart.alt_text}</p>
              </article>
            ))}
          </div>
        </Panel>
      </div>

      <Panel title="Operator Decision Intake" subtitle={flow.operator_decision_intake_lane.evidence_policy}>
        <div className="mb-3 rounded-lg border border-status-review/30 bg-status-review/10 px-3 py-2 text-[12px] font-semibold text-status-review">
          {flow.operator_decision_intake_lane.intake_summary}
        </div>
        <div className="overflow-hidden rounded-xl border border-line">
          <div className="grid grid-cols-[1fr_0.8fr_1.4fr_1.7fr_1.7fr] gap-2 border-b border-line bg-surface-2 px-3 py-2 font-mono text-[10.5px] font-bold uppercase text-fg-subtle">
            <span>Platform</span><span>Decision</span><span>Payload hash</span><span>Decision packet hash</span><span>Next action</span>
          </div>
          {flow.operator_decision_intake_lane.decision_packets.map((packet) => (
            <div key={packet.decision_packet_id} className="grid grid-cols-[1fr_0.8fr_1.4fr_1.7fr_1.7fr] gap-2 border-b border-line px-3 py-2 text-[11px] last:border-b-0">
              <span className="text-fg">{packet.platform}</span>
              <StatusChip status={packet.decision_status}>{packet.decision}</StatusChip>
              <span className="break-all font-mono text-fg-muted">{packet.payload_hash}</span>
              <span className="break-all font-mono text-fg-muted">{packet.decision_packet_hash}</span>
              <span className="text-fg-muted">{packet.next_required_action}</span>
            </div>
          ))}
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          {flow.operator_decision_intake_lane.decision_packets.map((packet) => (
            <article key={`${packet.decision_packet_id}_evidence`} className="rounded-xl border border-line bg-surface-2 p-4">
              <div className="flex items-start justify-between gap-2">
                <h3 className="text-sm font-semibold text-fg">{packet.operator_reference}</h3>
                <StatusChip status={packet.decision_status}>{packet.operator_evidence_mode}</StatusChip>
              </div>
              <p className="mt-2 text-[12px] leading-relaxed text-fg-muted">{packet.rationale}</p>
              <p className="mt-3 break-all font-mono text-[10.5px] text-fg-subtle">decision_packet_id={packet.decision_packet_id}</p>
              <p className="mt-2 font-mono text-[10.5px] text-fg-subtle">dispatch_permission_granted={String(packet.dispatch_permission_granted)} · live_write_allowed={String(packet.live_write_allowed)}</p>
            </article>
          ))}
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {flow.operator_decision_intake_lane.forbidden_actions.map((action) => (
            <StatusChip key={action} status="blocked">{action} blocked</StatusChip>
          ))}
        </div>
      </Panel>

      <Panel title="Local Outbox Readiness Reconciliation" subtitle={flow.local_outbox_readiness_lane.safety_policy}>
        <div className="mb-3 rounded-lg border border-status-review/30 bg-status-review/10 px-3 py-2 text-[12px] font-semibold text-status-review">
          {flow.local_outbox_readiness_lane.reconciliation_summary}
        </div>
        <div className="grid gap-3 md:grid-cols-6">
          <Metric label="Manual ready" value={String(flow.local_outbox_readiness_lane.counts.approved_manual_ready)} status="verified" hint="not dispatchable" />
          <Metric label="Held" value={String(flow.local_outbox_readiness_lane.counts.held_for_revision)} status="review" hint="needs revision" />
          <Metric label="Rejected" value={String(flow.local_outbox_readiness_lane.counts.rejected_blocked)} status="blocked" hint="do not use" />
          <Metric label="No decision" value={String(flow.local_outbox_readiness_lane.counts.blocked_no_decision)} status="review" hint="packet required" />
          <Metric label="Live-scope blocked" value={String(flow.local_outbox_readiness_lane.counts.blocked_live_scope_required)} status="blocked" hint="future scope" />
          <Metric label="Dispatchable" value={String(flow.local_outbox_readiness_lane.counts.dispatchable)} status="blocked" hint="always zero" />
        </div>
        <div className="mt-4 overflow-hidden rounded-xl border border-line">
          <div className="grid grid-cols-[1fr_0.8fr_1.1fr_1.5fr_1.5fr_1.7fr] gap-2 border-b border-line bg-surface-2 px-3 py-2 font-mono text-[10.5px] font-bold uppercase text-fg-subtle">
            <span>Platform</span><span>Decision</span><span>Readiness</span><span>Payload hash</span><span>Packet hash</span><span>Manual next action</span>
          </div>
          {flow.local_outbox_readiness_lane.readiness_rows.map((row) => (
            <div key={row.row_id} className="grid grid-cols-[1fr_0.8fr_1.1fr_1.5fr_1.5fr_1.7fr] gap-2 border-b border-line px-3 py-2 text-[11px] last:border-b-0">
              <span className="text-fg">{row.platform}</span>
              <span className="font-mono text-fg-muted">{row.decision ?? 'none'}</span>
              <StatusChip status={row.readiness_status}>{row.readiness_state}</StatusChip>
              <span className="break-all font-mono text-fg-muted">{row.payload_hash}</span>
              <span className="break-all font-mono text-fg-muted">{row.decision_packet_hash ?? 'no_packet'}</span>
              <span className="text-fg-muted">{row.manual_next_action}</span>
            </div>
          ))}
        </div>
        <p className="mt-3 font-mono text-[10.5px] text-fg-subtle">
          outbox_entry_created=false · outbox_dispatchable=false · dispatch_allowed_now=false · live_write_allowed_now=false · scheduler_or_retry_wired=false · approval_ledger_live_write_made=false
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          {flow.local_outbox_readiness_lane.blocked_actions.map((action) => (
            <StatusChip key={action} status="blocked">{action} locked</StatusChip>
          ))}
        </div>
      </Panel>

      <Panel title="Discord/Telegram Operator Bridge" subtitle={flow.operator_bridge_lane.evidence_policy}>
        <div className="mb-3 rounded-lg border border-status-blocked/30 bg-status-blocked/10 px-3 py-2 text-[12px] font-semibold text-status-blocked">
          {flow.operator_bridge_lane.lane_summary}
        </div>
        <div className="grid gap-3 lg:grid-cols-2">
          {flow.operator_bridge_lane.bridge_rows.map((row) => (
            <article key={row.bridge_id} className="rounded-xl border border-line bg-surface-2 p-4">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <h2 className="text-sm font-semibold text-fg">{row.platform} bridge</h2>
                  <p className="mt-1 font-mono text-[10.5px] text-fg-subtle">{row.bridge_id}</p>
                </div>
                <StatusChip status={row.status}>{row.bridge_state}</StatusChip>
              </div>
              <p className="mt-3 text-[12px] leading-relaxed text-fg-muted">{row.source_evidence}</p>
              <p className="mt-2 text-[12px] leading-relaxed text-fg-muted">{row.manual_handoff}</p>
              <dl className="mt-3 grid gap-1 border-t border-line pt-3 text-[11px]">
                <div><dt className="font-mono uppercase text-fg-subtle">Operator surface</dt><dd className="text-fg-muted">{row.operator_surface}</dd></div>
                <div><dt className="font-mono uppercase text-fg-subtle">Payload hash</dt><dd className="break-all font-mono text-fg-muted">{row.payload_hash}</dd></div>
                <div><dt className="font-mono uppercase text-fg-subtle">Redacted status</dt><dd className="text-fg-muted">{row.redacted_status}</dd></div>
              </dl>
              <p className="mt-3 font-mono text-[10.5px] text-fg-subtle">
                message_send_attempted={String(row.message_send_attempted)} · platform_api_called={String(row.platform_api_called)} · webhook_or_bot_token_read={String(row.webhook_or_bot_token_read)}
              </p>
              <p className="mt-1 font-mono text-[10.5px] text-fg-subtle">
                browser_or_cdp_used={String(row.browser_or_cdp_used)} · public_url_fetch_made={String(row.public_url_fetch_made)} · scheduler_or_retry_wired={String(row.scheduler_or_retry_wired)} · live_approval_ledger_written={String(row.live_approval_ledger_written)}
              </p>
            </article>
          ))}
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {flow.operator_bridge_lane.blocked_actions.map((action) => (
            <StatusChip key={action} status="blocked">{action} blocked</StatusChip>
          ))}
        </div>
      </Panel>

      <Panel title="Manual/Deferred Distribution Lanes" subtitle={flow.manual_deferred_distribution_lane.evidence_policy}>
        <div className="mb-3 rounded-lg border border-status-blocked/30 bg-status-blocked/10 px-3 py-2 text-[12px] font-semibold text-status-blocked">
          {flow.manual_deferred_distribution_lane.lane_summary}
        </div>
        <div className="grid gap-3 xl:grid-cols-2">
          {flow.manual_deferred_distribution_lane.rows.map((row) => (
            <article key={row.lane_id} className="rounded-xl border border-line bg-surface-2 p-4">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <h2 className="text-sm font-semibold text-fg">{row.platform} manual/deferred lane</h2>
                  <p className="mt-1 font-mono text-[10.5px] text-fg-subtle">{row.lane_id}</p>
                </div>
                <StatusChip status={row.status}>{row.readiness_state}</StatusChip>
              </div>
              <p className="mt-3 text-[12px] leading-relaxed text-fg-muted">{row.blocker_summary}</p>
              <p className="mt-2 text-[12px] leading-relaxed text-fg-muted">{row.manual_handoff}</p>
              <dl className="mt-3 grid gap-1 border-t border-line pt-3 text-[11px]">
                <div><dt className="font-mono uppercase text-fg-subtle">Variant</dt><dd className="break-all text-fg-muted">{row.source_variant_key}</dd></div>
                <div><dt className="font-mono uppercase text-fg-subtle">Payload hash</dt><dd className="break-all font-mono text-fg-muted">{row.payload_hash}</dd></div>
                <div><dt className="font-mono uppercase text-fg-subtle">Media requirement</dt><dd className="text-fg-muted">{row.media_requirement}</dd></div>
                <div><dt className="font-mono uppercase text-fg-subtle">Audit evidence</dt><dd className="text-fg-muted">{row.audit_evidence_mode}</dd></div>
              </dl>
              <p className="mt-3 font-mono text-[10.5px] text-fg-subtle">
                live_write_allowed={String(row.live_write_allowed)} · platform_api_called={String(row.platform_api_called)} · browser_or_cdp_used={String(row.browser_or_cdp_used)} · public_url_fetch_made={String(row.public_url_fetch_made)}
              </p>
              <p className="mt-1 font-mono text-[10.5px] text-fg-subtle">
                media_download_or_upload_performed={String(row.media_download_or_upload_performed)} · scheduler_or_retry_wired={String(row.scheduler_or_retry_wired)} · credential_or_env_read={String(row.credential_or_env_read)} · approval_ledger_live_write_made={String(row.approval_ledger_live_write_made)}
              </p>
            </article>
          ))}
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {flow.manual_deferred_distribution_lane.blocked_actions.map((action) => (
            <StatusChip key={action} status="blocked">{action} blocked</StatusChip>
          ))}
        </div>
      </Panel>

      <Panel title="Manual Dispatch and Audit Lane" subtitle="Operator-supplied evidence only; no public verification or platform write">
        <div className="grid gap-3 md:grid-cols-3">
          <div className="rounded-xl border border-status-blocked/30 bg-status-blocked/10 p-4">
            <div className="font-mono text-[10.5px] uppercase text-fg-muted">Approval</div>
            <StatusChip status={flow.manual_audit_lane.approval_status}>{flow.manual_audit_lane.approval_status}</StatusChip>
            <p className="mt-2 text-[12px] text-fg-muted">{flow.manual_audit_lane.approval_summary}</p>
          </div>
          <div className="rounded-xl border border-status-blocked/30 bg-status-blocked/10 p-4">
            <div className="font-mono text-[10.5px] uppercase text-fg-muted">Dispatch</div>
            <StatusChip status={flow.manual_audit_lane.dispatch_status}>{flow.manual_audit_lane.dispatch_status}</StatusChip>
            <p className="mt-2 text-[12px] text-fg-muted">{flow.manual_audit_lane.dispatch_summary}</p>
          </div>
          <div className="rounded-xl border border-line bg-surface-2 p-4">
            <div className="font-mono text-[10.5px] uppercase text-fg-muted">Audit</div>
            <p className="mt-2 text-[12px] text-fg-muted">{flow.manual_audit_lane.audit_summary}</p>
          </div>
        </div>
        <div className="mt-4 overflow-hidden rounded-xl border border-line">
          <div className="grid grid-cols-[1fr_1.4fr_1.7fr_0.8fr] gap-2 border-b border-line bg-surface-2 px-3 py-2 font-mono text-[10.5px] font-bold uppercase text-fg-subtle">
            <span>Platform</span><span>Variant</span><span>Payload hash</span><span>Status</span>
          </div>
          {flow.manual_audit_lane.audit_rows.map((row) => (
            <div key={row.row_id} className="grid grid-cols-[1fr_1.4fr_1.7fr_0.8fr] gap-2 border-b border-line px-3 py-2 text-[11px] last:border-b-0">
              <span className="text-fg">{row.platform}</span>
              <span className="break-all font-mono text-fg-muted">{row.source_variant_key}</span>
              <span className="break-all font-mono text-fg-muted">{row.payload_hash}</span>
              <StatusChip status={row.status}>{row.public_url_status}</StatusChip>
            </div>
          ))}
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {flow.manual_audit_lane.locked_actions.map((action) => (
            <StatusChip key={action} status="blocked">{action} locked</StatusChip>
          ))}
        </div>
      </Panel>

      <Panel title="Safety Evidence" subtitle="Existing release evidence plus red-team and local registry readback">
        <div className="grid gap-4 lg:grid-cols-2">
          <div>
            <h2 className="mb-2 font-mono text-[11px] font-bold uppercase text-fg-subtle">Release evidence</h2>
            <ul className="grid gap-2 text-sm">
              {p.release_evidence_paths.map((path) => <li key={path} className="rounded-lg border border-line bg-surface-2 px-3 py-2 font-mono text-[12px] text-fg-muted break-all">{path}</li>)}
            </ul>
          </div>
          <div>
            <h2 className="mb-2 font-mono text-[11px] font-bold uppercase text-fg-subtle">Registry readback</h2>
            <div className="grid gap-3 md:grid-cols-2">
              <Metric label="Rows" value={String(p.publication_registry_audit.row_count)} status={p.publication_registry_audit.status} hint={p.publication_registry_audit.task_label} />
              <Metric label="Duplicate keys" value={String(p.publication_registry_audit.duplicate_natural_key_count)} status={p.publication_registry_audit.duplicate_natural_key_count === 0 ? 'verified' : 'blocked'} hint="natural publication key" />
              <Metric label="Browser/CDP" value={String(p.publication_registry_audit.browser_or_cdp_probe_performed)} status="verified" hint="not probed" />
              <Metric label="X API / fetch" value={`${p.publication_registry_audit.x_api_used}/${p.publication_registry_audit.public_url_fetch_made}`} status="verified" hint="not used" />
            </div>
          </div>
        </div>
      </Panel>

      <Panel title="Forbidden Media/Platform Actions" subtitle="Shown explicitly so the cockpit cannot be mistaken for a live automation surface">
        <div className="flex flex-wrap gap-2">
          {[...flow.media_lane.forbidden_actions, ...flow.manual_audit_lane.locked_actions].map((item) => (
            <StatusChip key={item} status="blocked">{item}</StatusChip>
          ))}
        </div>
      </Panel>

      <LockedAction label="Publish / Dispatch / Scrape / Download / Verify public URL" reason="Disabled in final V6 local release. No network, provider, browser/CDP, credential/env, scraping, media download, webhook, platform API, scheduler, retry, DM/reply/reaction, or live write is enabled." />
    </div>
  );
}
