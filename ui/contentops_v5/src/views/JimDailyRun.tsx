import { viewModel } from '../fixtures';
import { Metric, Panel, StatusChip } from '../ui/primitives';
import { IconShield } from '../ui/icons';

export function JimDailyRun() {
  const p = viewModel.jim_daily_content_run;
  const bundle = viewModel.jim_variant_preview_bundle;
  const manualWorkbench = viewModel.jim_manual_export_workbench;
  const auditMetricsLoop = viewModel.jim_redacted_audit_metrics_loop;
  const approvalPreview = viewModel.platform_variant_approval_packet_preview;
  const dryRunOutbox = viewModel.dispatch_outbox_dry_run;
  const operatorRecovery = viewModel.dispatch_outbox_operator_recovery;
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

      <Panel title="Local Canonical Draft Preview + Review" subtitle="Deterministic template output; no LLM, provider, network, or platform action">
        <div className="grid gap-3 md:grid-cols-4">
          <div className="rounded-lg border border-status-review/30 bg-status-review/10 px-3 py-2">
            <div className="font-mono text-[10.5px] uppercase text-fg-muted">Draft status</div>
            <div className="mt-1 text-sm font-semibold text-status-review">{viewModel.local_canonical_draft_preview_review.draft_preview_status}</div>
          </div>
          <div className="rounded-lg border border-status-review/30 bg-status-review/10 px-3 py-2">
            <div className="font-mono text-[10.5px] uppercase text-fg-muted">Review status</div>
            <div className="mt-1 text-sm font-semibold text-status-review">{viewModel.local_canonical_draft_preview_review.draft_review_status}</div>
          </div>
          <div className="rounded-lg border border-line bg-surface-2 px-3 py-2">
            <div className="font-mono text-[10.5px] uppercase text-fg-muted">Generation method</div>
            <div className="mt-1 text-sm font-semibold text-fg">{viewModel.local_canonical_draft_preview_review.draft_generation_method}</div>
          </div>
          <div className="rounded-lg border border-status-blocked/30 bg-status-blocked/10 px-3 py-2">
            <div className="font-mono text-[10.5px] uppercase text-fg-muted">Final approval</div>
            <div className="mt-1 text-sm font-semibold text-status-blocked">final_article_approved=false</div>
          </div>
        </div>
        <article className="mt-4 rounded-xl border border-line bg-surface-2 p-4">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div>
              <h2 className="text-sm font-semibold text-fg">{viewModel.local_canonical_draft_preview_review.working_title}</h2>
              <p className="mt-1 font-mono text-[11px] text-fg-subtle">
                {viewModel.local_canonical_draft_preview_review.source_pack_intake_packet_id} · {viewModel.local_canonical_draft_preview_review.source_draft_authorization_packet_id}
              </p>
            </div>
            <StatusChip status="review">{viewModel.local_canonical_draft_preview_review.packet_kind}</StatusChip>
          </div>
          <div className="mt-3 grid gap-2 md:grid-cols-2">
            {viewModel.local_canonical_draft_preview_review.draft_preview_sections.map((section) => (
              <div key={section.section_title} className="rounded-lg border border-line bg-surface-1 p-3">
                <div className="text-xs font-semibold text-fg">{section.section_title}</div>
                <p className="mt-1 text-xs leading-relaxed text-fg-muted">{section.section_body}</p>
              </div>
            ))}
          </div>
          <ul className="mt-3 grid gap-2 text-xs md:grid-cols-3">
            {viewModel.local_canonical_draft_preview_review.operator_review_questions.map((question) => (
              <li key={question} className="rounded-lg border border-status-review/30 bg-status-review/10 px-3 py-2 text-status-review">
                {question}
              </li>
            ))}
          </ul>
          <p className="mt-3 font-mono text-[10.5px] text-status-blocked">
            ready_for_llm_drafting=false · ready_for_provider_drafting=false · ready_for_dispatch=false · enabled_publish_send_dispatch_approve_controls=false
          </p>
        </article>
      </Panel>

      <Panel title="Canonical Draft Final Review + Platform Variant Preview" subtitle="Preview-only variants for Jim review; no publish, dispatch, network, provider, browser, env, or credential action">
        <div className="grid gap-3 md:grid-cols-4">
          <div className="rounded-lg border border-status-review/30 bg-status-review/10 px-3 py-2">
            <div className="font-mono text-[10.5px] uppercase text-fg-muted">Final review status</div>
            <div className="mt-1 text-sm font-semibold text-status-review">{viewModel.canonical_draft_final_review_variant_preview.canonical_draft_final_review_status}</div>
          </div>
          <div className="rounded-lg border border-status-review/30 bg-status-review/10 px-3 py-2">
            <div className="font-mono text-[10.5px] uppercase text-fg-muted">Variant preview status</div>
            <div className="mt-1 text-sm font-semibold text-status-review">{viewModel.canonical_draft_final_review_variant_preview.platform_variant_preview_status}</div>
          </div>
          <div className="rounded-lg border border-line bg-surface-2 px-3 py-2">
            <div className="font-mono text-[10.5px] uppercase text-fg-muted">Preview variants</div>
            <div className="mt-1 text-sm font-semibold text-fg">{Object.keys(viewModel.canonical_draft_final_review_variant_preview.preview_variants).length}</div>
          </div>
          <div className="rounded-lg border border-status-blocked/30 bg-status-blocked/10 px-3 py-2">
            <div className="font-mono text-[10.5px] uppercase text-fg-muted">Payload approval</div>
            <div className="mt-1 text-sm font-semibold text-status-blocked">platform_payloads_approved=false</div>
          </div>
        </div>
        <article className="mt-4 rounded-xl border border-line bg-surface-2 p-4">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div>
              <h2 className="break-all text-sm font-semibold text-fg">{viewModel.canonical_draft_final_review_variant_preview.canonical_draft_final_review_to_platform_variant_preview_packet_id}</h2>
              <p className="mt-1 font-mono text-[11px] text-fg-subtle">
                {viewModel.canonical_draft_final_review_variant_preview.source_local_draft_preview_packet_id} · {viewModel.canonical_draft_final_review_variant_preview.source_draft_review_packet_id}
              </p>
            </div>
            <StatusChip status="review">{viewModel.canonical_draft_final_review_variant_preview.packet_kind}</StatusChip>
          </div>
          <div className="mt-3 grid gap-2 md:grid-cols-2">
            {Object.entries(viewModel.canonical_draft_final_review_variant_preview.preview_variants).map(([platform, preview]) => (
              <div key={platform} className="rounded-lg border border-line bg-surface-1 p-3">
                <div className="font-mono text-[10.5px] uppercase text-fg-subtle">{platform}</div>
                <div className="mt-1 text-xs font-semibold text-fg">{preview.title}</div>
                <p className="mt-1 text-xs leading-relaxed text-fg-muted">{preview.body}</p>
                <p className="mt-2 font-mono text-[10.5px] text-status-review">status={preview.status}</p>
              </div>
            ))}
          </div>
          <p className="mt-3 font-mono text-[10.5px] text-status-blocked">
            final_article_approved=false · platform_variants_are_preview_only=true · ready_for_auto_publish=false · ready_for_dispatch=false · live_action_allowed=false
          </p>
          <p className="mt-2 font-mono text-[10.5px] text-status-blocked">
            llm_provider_call_made=false · provider_call_made=false · platform_api_used=false · network_call_made=false · browser_session_used=false · env_value_read_made=false · credential_read_made=false · public_url_verification_performed=false
          </p>
        </article>
      </Panel>


      <Panel title="Platform Variant Approval Packet Preview" subtitle="Exact approval targets for Jim review; no approval record, outbox, dispatch, network, provider, browser, env, credential, or public URL action">
        <div className="grid gap-3 md:grid-cols-4">
          <div className="rounded-lg border border-status-review/30 bg-status-review/10 px-3 py-2">
            <div className="font-mono text-[10.5px] uppercase text-fg-muted">Approval preview status</div>
            <div className="mt-1 text-sm font-semibold text-status-review">{approvalPreview.approval_packet_preview_status}</div>
          </div>
          <div className="rounded-lg border border-line bg-surface-2 px-3 py-2">
            <div className="font-mono text-[10.5px] uppercase text-fg-muted">Approval targets</div>
            <div className="mt-1 text-sm font-semibold text-fg">{Object.keys(approvalPreview.approval_targets).length}</div>
          </div>
          <div className="rounded-lg border border-status-blocked/30 bg-status-blocked/10 px-3 py-2">
            <div className="font-mono text-[10.5px] uppercase text-fg-muted">Operator approval</div>
            <div className="mt-1 text-sm font-semibold text-status-blocked">actual_operator_approval_recorded=false</div>
          </div>
          <div className="rounded-lg border border-status-blocked/30 bg-status-blocked/10 px-3 py-2">
            <div className="font-mono text-[10.5px] uppercase text-fg-muted">Dispatch outbox</div>
            <div className="mt-1 text-sm font-semibold text-status-blocked">dispatch_outbox_ready=false</div>
          </div>
        </div>
        <article className="mt-4 rounded-xl border border-line bg-surface-2 p-4">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div>
              <h2 className="break-all text-sm font-semibold text-fg">{approvalPreview.platform_variant_final_review_to_approval_packet_preview_packet_id}</h2>
              <p className="mt-1 font-mono text-[11px] text-fg-subtle">
                {approvalPreview.source_final_review_packet_id} · {approvalPreview.source_local_draft_preview_packet_id}
              </p>
            </div>
            <StatusChip status="review">{approvalPreview.packet_kind}</StatusChip>
          </div>
          <div className="mt-3 grid gap-2 md:grid-cols-2">
            {Object.entries(approvalPreview.approval_targets).map(([targetId, target]) => (
              <div key={targetId} className="rounded-lg border border-line bg-surface-1 p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-mono text-[10.5px] uppercase text-fg-subtle">{target.platform_id}</span>
                  <StatusChip status="blocked">approved={String(target.approved)}</StatusChip>
                </div>
                <p className="mt-2 text-xs leading-relaxed text-fg-muted">{target.exact_preview_text}</p>
                <p className="mt-2 font-mono text-[10.5px] text-status-blocked">
                  dispatchable={String(target.dispatchable)} · approval_required={String(target.approval_required)} · no_public_url_claim={String(target.no_public_url_claim)}
                </p>
              </div>
            ))}
          </div>
          <p className="mt-3 font-mono text-[10.5px] text-status-blocked">
            approval_ledger_entry_created=false · approval_record_created=false · platform_payloads_approved=false · outbox_entry_created=false · ready_for_dispatch=false · live_action_allowed=false
          </p>
          <p className="mt-2 font-mono text-[10.5px] text-status-blocked">
            llm_provider_call_made=false · provider_call_made=false · platform_api_used=false · network_call_made=false · browser_session_used=false · env_value_read_made=false · credential_read_made=false · public_url_verification_performed=false
          </p>
        </article>
      </Panel>


      <Panel title="Dispatch Outbox Dry-Run Preview" subtitle="Review-only dry-run entries; no executable outbox, dispatch attempt, webhook request, platform API request, scheduler, retry, browser, env, credential, network, or public URL action">
        <div className="grid gap-3 md:grid-cols-4">
          <div className="rounded-lg border border-status-review/30 bg-status-review/10 px-3 py-2">
            <div className="font-mono text-[10.5px] uppercase text-fg-muted">Dry-run status</div>
            <div className="mt-1 text-sm font-semibold text-status-review">{dryRunOutbox.dispatch_outbox_dry_run_status}</div>
          </div>
          <div className="rounded-lg border border-line bg-surface-2 px-3 py-2">
            <div className="font-mono text-[10.5px] uppercase text-fg-muted">Dry-run entries</div>
            <div className="mt-1 text-sm font-semibold text-fg">{Object.keys(dryRunOutbox.dry_run_entries).length}</div>
          </div>
          <div className="rounded-lg border border-status-blocked/30 bg-status-blocked/10 px-3 py-2">
            <div className="font-mono text-[10.5px] uppercase text-fg-muted">Executable outbox</div>
            <div className="mt-1 text-sm font-semibold text-status-blocked">executable_outbox_entry_created=false</div>
          </div>
          <div className="rounded-lg border border-status-blocked/30 bg-status-blocked/10 px-3 py-2">
            <div className="font-mono text-[10.5px] uppercase text-fg-muted">Dispatch attempted</div>
            <div className="mt-1 text-sm font-semibold text-status-blocked">dispatch_attempted=false</div>
          </div>
        </div>
        <article className="mt-4 rounded-xl border border-line bg-surface-2 p-4">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div>
              <h2 className="break-all text-sm font-semibold text-fg">{dryRunOutbox.dispatch_outbox_dry_run_packet_id}</h2>
              <p className="mt-1 font-mono text-[11px] text-fg-subtle">
                {dryRunOutbox.source_approval_preview_packet_id} · {dryRunOutbox.source_final_review_packet_id} · {dryRunOutbox.source_local_draft_preview_packet_id}
              </p>
            </div>
            <StatusChip status="blocked">{dryRunOutbox.packet_kind}</StatusChip>
          </div>
          <div className="mt-3 grid gap-2 md:grid-cols-2">
            {Object.entries(dryRunOutbox.dry_run_entries).map(([entryKey, entry]) => (
              <div key={entryKey} className="rounded-lg border border-line bg-surface-1 p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-mono text-[10.5px] uppercase text-fg-subtle">{entry.platform_id}</span>
                  <StatusChip status="blocked">dispatchable={String(entry.dispatchable)}</StatusChip>
                </div>
                <p className="mt-1 break-all font-mono text-[10.5px] text-fg-subtle">{entry.dry_run_entry_id}</p>
                <p className="mt-2 text-xs leading-relaxed text-fg-muted">{entry.dry_run_payload_text}</p>
                <p className="mt-2 font-mono text-[10.5px] text-status-blocked">
                  executable={String(entry.executable)} · approved={String(entry.approved)} · request_method_preview={entry.request_method_preview} · request_url_preview_status={entry.request_url_preview_status}
                </p>
                <p className="mt-1 break-all font-mono text-[10.5px] text-fg-subtle">request_body_hash_preview={entry.request_body_hash_preview}</p>
              </div>
            ))}
          </div>
          <p className="mt-3 font-mono text-[10.5px] text-status-blocked">
            dry_run_outbox_package_created=true · dry_run_entries_created=true · executable_outbox_entry_created=false · real_outbox_entry_created=false · dispatch_outbox_ready=false · dispatch_attempted=false
          </p>
          <p className="mt-2 font-mono text-[10.5px] text-status-blocked">
            dispatch_request_count=0 · webhook_request_count=0 · platform_api_request_count=0 · scheduler_enabled=false · retry_enabled=false · kill_switch_active=true · ready_for_dispatch=false · live_action_allowed=false
          </p>
          <p className="mt-2 font-mono text-[10.5px] text-status-blocked">
            llm_provider_call_made=false · provider_call_made=false · platform_api_used=false · network_call_made=false · browser_session_used=false · env_value_read_made=false · credential_read_made=false · public_url_verification_performed=false
          </p>
        </article>
      </Panel>


      <Panel title="Dispatch Outbox Operator Runbook + Recovery Preview" subtitle="Runbook-only recovery packet for Jim review; no executable outbox, approval record, dispatch, scheduler, retry, webhook, platform API, provider, browser, env, credential, network, or public URL action">
        <div className="grid gap-3 md:grid-cols-4">
          <div className="rounded-lg border border-status-review/30 bg-status-review/10 px-3 py-2">
            <div className="font-mono text-[10.5px] uppercase text-fg-muted">Recovery status</div>
            <div className="mt-1 text-sm font-semibold text-status-review">{operatorRecovery.operator_recovery_status}</div>
          </div>
          <div className="rounded-lg border border-line bg-surface-2 px-3 py-2">
            <div className="font-mono text-[10.5px] uppercase text-fg-muted">Runbook sections</div>
            <div className="mt-1 text-sm font-semibold text-fg">preflight · replay · rollback · matrix</div>
          </div>
          <div className="rounded-lg border border-status-blocked/30 bg-status-blocked/10 px-3 py-2">
            <div className="font-mono text-[10.5px] uppercase text-fg-muted">Executable outbox</div>
            <div className="mt-1 text-sm font-semibold text-status-blocked">executable_outbox_entry_created=false</div>
          </div>
          <div className="rounded-lg border border-status-blocked/30 bg-status-blocked/10 px-3 py-2">
            <div className="font-mono text-[10.5px] uppercase text-fg-muted">Live scope</div>
            <div className="mt-1 text-sm font-semibold text-status-blocked">blocked_until_explicit_live_scope=true</div>
          </div>
        </div>
        <article className="mt-4 rounded-xl border border-line bg-surface-2 p-4">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div>
              <h2 className="break-all text-sm font-semibold text-fg">{operatorRecovery.dispatch_outbox_operator_recovery_packet_id}</h2>
              <p className="mt-1 font-mono text-[11px] text-fg-subtle">
                {operatorRecovery.source_dispatch_outbox_dry_run_packet_id} · {operatorRecovery.source_approval_preview_packet_id} · {operatorRecovery.source_final_review_packet_id}
              </p>
            </div>
            <StatusChip status="blocked">{operatorRecovery.packet_kind}</StatusChip>
          </div>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            <section className="rounded-lg border border-line bg-surface-1 p-3">
              <h3 className="text-xs font-semibold text-fg">Operator preflight checklist</h3>
              <ul className="mt-2 grid gap-2">
                {operatorRecovery.operator_preflight_checklist.map((check) => (
                  <li key={check.check_id} className="rounded-md border border-line bg-surface-2 px-2 py-1.5 text-xs text-fg-muted">
                    <span className="font-semibold text-fg">{check.label}</span>
                    <span className="ml-2 font-mono text-status-review">status={check.status}</span>
                  </li>
                ))}
              </ul>
            </section>
            <section className="rounded-lg border border-line bg-surface-1 p-3">
              <h3 className="text-xs font-semibold text-fg">Dry-run replay plan</h3>
              <ul className="mt-2 grid gap-2">
                {operatorRecovery.dry_run_replay_steps.map((step) => (
                  <li key={step.replay_id} className="rounded-md border border-line bg-surface-2 px-2 py-1.5 text-xs text-fg-muted">
                    <span className="font-semibold text-fg">{step.action}</span>
                    <span className="ml-2 font-mono text-status-review">status={step.status}</span>
                  </li>
                ))}
              </ul>
            </section>
            <section className="rounded-lg border border-line bg-surface-1 p-3">
              <h3 className="text-xs font-semibold text-fg">Rollback and stop conditions</h3>
              <ul className="mt-2 grid gap-2">
                {operatorRecovery.rollback_and_stop_conditions.map((condition) => (
                  <li key={condition.condition_id} className="rounded-md border border-status-blocked/30 bg-status-blocked/10 px-2 py-1.5 text-xs text-status-blocked">
                    <span className="font-semibold">{condition.event}</span>
                    <span className="block text-fg-muted">{condition.action}</span>
                  </li>
                ))}
              </ul>
            </section>
            <section className="rounded-lg border border-line bg-surface-1 p-3">
              <h3 className="text-xs font-semibold text-fg">Failure mode recovery matrix</h3>
              <ul className="mt-2 grid gap-2">
                {operatorRecovery.failure_mode_matrix.map((failure) => (
                  <li key={failure.failure_mode} className="rounded-md border border-line bg-surface-2 px-2 py-1.5 text-xs text-fg-muted">
                    <span className="font-semibold text-fg">{failure.failure_mode}</span>
                    <span className="block">impact={failure.impact}</span>
                    <span className="block text-status-review">recovery={failure.recovery_action}</span>
                  </li>
                ))}
              </ul>
            </section>
          </div>
          <section className="mt-3 rounded-lg border border-line bg-surface-1 p-3">
            <h3 className="text-xs font-semibold text-fg">Evidence collection checklist</h3>
            <div className="mt-2 grid gap-2 md:grid-cols-2">
              {operatorRecovery.evidence_collection_checklist.map((item) => (
                <div key={item.item_id} className="rounded-md border border-line bg-surface-2 px-2 py-1.5 text-xs text-fg-muted">
                  <span className="font-semibold text-fg">{item.label}</span>
                  <span className="ml-2 font-mono text-status-review">status={item.status}</span>
                </div>
              ))}
            </div>
          </section>
          <section className="mt-3 rounded-lg border border-line bg-surface-1 p-3">
            <h3 className="text-xs font-semibold text-fg">Platform-specific recovery notes</h3>
            <div className="mt-2 grid gap-2 md:grid-cols-2">
              {Object.entries(operatorRecovery.platform_specific_recovery_notes).map(([noteKey, note]) => (
                <div key={noteKey} className="rounded-md border border-line bg-surface-2 px-2 py-1.5 text-xs text-fg-muted">
                  <div className="break-all font-mono text-[10.5px] uppercase text-fg-subtle">{noteKey}</div>
                  <p className="mt-1 leading-relaxed">{note}</p>
                </div>
              ))}
            </div>
          </section>
          <p className="mt-3 font-mono text-[10.5px] text-status-blocked">
            recovery_runbook_created={String(operatorRecovery.recovery_runbook_created)} · manual_fallback_plan_created={String(operatorRecovery.manual_fallback_plan_created)} · rollback_plan_created={String(operatorRecovery.rollback_plan_created)} · dry_run_replay_plan_created={String(operatorRecovery.dry_run_replay_plan_created)} · failure_mode_matrix_created={String(operatorRecovery.failure_mode_matrix_created)}
          </p>
          <p className="mt-2 font-mono text-[10.5px] text-status-blocked">
            evidence_collection_checklist_created={String(operatorRecovery.evidence_collection_checklist_created)} · dispatch_preflight_checklist_created={String(operatorRecovery.dispatch_preflight_checklist_created)} · real_outbox_entry_created={String(operatorRecovery.real_outbox_entry_created)} · dispatch_outbox_ready={String(operatorRecovery.dispatch_outbox_ready)} · dispatch_attempted={String(operatorRecovery.dispatch_attempted)}
          </p>
          <p className="mt-2 font-mono text-[10.5px] text-status-blocked">
            dispatch_request_count={operatorRecovery.dispatch_request_count} · webhook_request_count={operatorRecovery.webhook_request_count} · platform_api_request_count={operatorRecovery.platform_api_request_count} · scheduler_enabled={String(operatorRecovery.scheduler_enabled)} · retry_enabled={String(operatorRecovery.retry_enabled)} · kill_switch_active={String(operatorRecovery.kill_switch_active)}
          </p>
          <p className="mt-2 font-mono text-[10.5px] text-status-blocked">
            approval_ledger_entry_created={String(operatorRecovery.approval_ledger_entry_created)} · approval_record_created={String(operatorRecovery.approval_record_created)} · platform_payloads_approved={String(operatorRecovery.platform_payloads_approved)} · ready_for_dispatch={String(operatorRecovery.ready_for_dispatch)} · live_action_allowed={String(operatorRecovery.live_action_allowed)}
          </p>
          <p className="mt-2 font-mono text-[10.5px] text-status-blocked">
            llm_provider_call_made={String(operatorRecovery.llm_provider_call_made)} · provider_call_made={String(operatorRecovery.provider_call_made)} · platform_api_used={String(operatorRecovery.platform_api_used)} · network_call_made={String(operatorRecovery.network_call_made)} · browser_session_used={String(operatorRecovery.browser_session_used)} · env_value_read_made={String(operatorRecovery.env_value_read_made)} · credential_read_made={String(operatorRecovery.credential_read_made)} · public_url_verification_performed={String(operatorRecovery.public_url_verification_performed)}
          </p>
        </article>
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
          Approval records are previews only: valid_for_dispatch=false. No buttons, no inputs, no public reference fields, no platform writes.
        </div>
      </Panel>


      <Panel title="Redacted Audit + Metrics Import Loop" subtitle="Operator-supplied values only; no network collection">
        <div className="grid gap-3 md:grid-cols-4">
          <div className="rounded-lg border border-status-review/30 bg-status-review/10 px-3 py-2">
            <div className="font-mono text-[10.5px] uppercase text-fg-muted">Loop status</div>
            <div className="mt-1 text-sm font-semibold text-status-review">{auditMetricsLoop.loop_status}</div>
          </div>
          <div className="rounded-lg border border-line bg-surface-2 px-3 py-2">
            <div className="font-mono text-[10.5px] uppercase text-fg-muted">Audit cards</div>
            <div className="mt-1 text-sm font-semibold text-fg">{auditMetricsLoop.audit_card_count}</div>
          </div>
          <div className="rounded-lg border border-line bg-surface-2 px-3 py-2">
            <div className="font-mono text-[10.5px] uppercase text-fg-muted">Metrics packets</div>
            <div className="mt-1 text-sm font-semibold text-fg">{auditMetricsLoop.metrics_packet_count}</div>
          </div>
          <div className="rounded-lg border border-status-blocked/30 bg-status-blocked/10 px-3 py-2">
            <div className="font-mono text-[10.5px] uppercase text-fg-muted">Baseline promoted</div>
            <div className="mt-1 text-sm font-semibold text-status-blocked">false</div>
          </div>
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {auditMetricsLoop.metrics_import_packets.slice(0, 4).map((packet) => (
            <article key={packet.metrics_packet_id} className="rounded-xl border border-line bg-surface-2 p-4">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <h2 className="text-sm font-semibold text-fg">{packet.platform} operator metrics</h2>
                  <p className="mt-1 font-mono text-[11px] text-fg-subtle">{packet.metrics_packet_id}</p>
                </div>
                <StatusChip status="review">{packet.metrics_status}</StatusChip>
              </div>
              <div className="mt-3 grid grid-cols-3 gap-2">
                {Object.entries(packet.metrics).slice(0, 6).map(([label, value]) => (
                  <div key={label} className="rounded-lg border border-line bg-surface-1 px-2 py-1.5">
                    <div className="font-mono text-[9.5px] uppercase text-fg-subtle">{label}</div>
                    <div className="mt-0.5 text-sm font-semibold tabular-nums text-fg">{value}</div>
                  </div>
                ))}
              </div>
              <p className="mt-2 font-mono text-[10.5px] text-status-blocked">operator_supplied_values_only=true · network_called=false · baseline_promoted=false</p>
            </article>
          ))}
        </div>
        <div className="mt-4 rounded-lg border border-status-review/30 bg-status-review/10 p-3 text-xs leading-relaxed text-status-review">
          Evidence vault cards and feedback candidates are review-only. Jim decides next content backlog moves; no automatic promotion.
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
