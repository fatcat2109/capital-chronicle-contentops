// Capital Chronicle ContentOps V5 — Platform Payload Preview view (PlatformPreview).
// DRY-RUN ONLY. This surface shows the exact LOCAL fixture payload that WOULD
// be assembled for each platform, with zero posting, scheduling, credential
// use, provider call, or platform API behavior. Every preview carries
// dispatchable: false (structurally unrepresentable as true), and the
// live/credential/provider states are always locked. Selecting a platform tab,
// a payload field, or a constraint updates the inspector. No network, no
// storage, no credentials.

import { SubstackArticleStudioCard } from './SubstackArticleStudioCard';
import { useState } from 'react';
import { useApp } from '../state';
import { viewModel } from '../fixtures';
import {
  selectPayloadConstraint,
  selectPlatformPayloadPreview,
} from '../selectors';
import { IconBlock, IconLayers } from '../ui/icons';
import { LockedAction, Panel, SectionLabel, StatusChip, StatusDot } from '../ui/primitives';
import type { PlatformPayloadPreview as Preview } from '../types';
import { canonicalDraftFinalReviewVariantPreviewPacket } from '../data/canonicalDraftFinalReviewVariantPreviewAdapter';
import { platformVariantApprovalPacketPreviewPacket } from '../data/platformVariantApprovalPacketPreviewAdapter';
import { dispatchOutboxDryRunPacket } from '../data/dispatchOutboxDryRunAdapter';
import { dispatchOutboxOperatorRecoveryPacket } from '../data/dispatchOutboxOperatorRecoveryAdapter';
import { explicitLiveScopeGatePacket, normalizedDispatchCandidate } from '../data/explicitLiveScopeGateSourceCandidateAdapter';

export function PlatformPreview() {
  const { select, selected } = useApp();
  const previews = viewModel.platform_payload_previews;
  const [activeKey, setActiveKey] = useState(previews[0].platform_key);
  const active: Preview =
    previews.find((p) => p.platform_key === activeKey) ?? previews[0];

  return (
    <div className="space-y-6">
      <SubstackArticleStudioCard mode="preview" />
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 font-mono text-[11px] font-bold uppercase tracking-[0.14em] text-fg-subtle">
            Platform payload preview
            <span className="text-fg-subtle/60">·</span>
            <span className="text-fg-muted">{active.source_draft_id}</span>
          </div>
          <h1 className="mt-2 flex items-center gap-2 text-2xl font-semibold tracking-tight text-fg">
            <IconLayers className="h-6 w-6 text-accent" />
            Platform Payload Preview
          </h1>
          <p className="mt-1 text-sm font-medium text-fg-muted">
            Exact local fixture payloads per platform — dry-run only, never dispatched.
          </p>
        </div>
        <div className="flex flex-col items-end gap-1.5">
          <StatusChip status="blocked" icon nowrap>
            Dry-run only · not dispatchable
          </StatusChip>
          <span className="font-mono text-[10.5px] text-status-blocked">
            dispatchable: false
          </span>
        </div>
      </header>

      {/* Dry-run policy banner — make the no-live posture unmissable. */}
      <div className="flex items-start gap-2.5 rounded-xl border border-status-blocked/30 bg-status-blocked/5 p-4">
        <IconBlock className="mt-0.5 h-4 w-4 shrink-0 text-status-blocked" />
        <div className="min-w-0">
          <p className="text-sm font-semibold text-fg">
            Dry-run payload preview — no posting, no scheduling, no credentials
          </p>
          <p className="mt-1 text-[12px] leading-relaxed text-fg-muted">
            These previews are assembled from local fixtures to show how a draft
            maps onto each platform&apos;s payload shape and limits. There is no
            platform API, no provider call, no credential or token read, and no
            scheduler. Nothing on this screen can be dispatched.
          </p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            <span className="rounded-md border border-line bg-surface-2 px-1.5 py-0.5 font-mono text-[10.5px] text-fg-muted">
              LIVE_DISABLED
            </span>
            <span className="rounded-md border border-line bg-surface-2 px-1.5 py-0.5 font-mono text-[10.5px] text-fg-muted">
              NO_CREDENTIAL_READ
            </span>
            <span className="rounded-md border border-line bg-surface-2 px-1.5 py-0.5 font-mono text-[10.5px] text-fg-muted">
              NO_PROVIDER_CALL
            </span>
            <span className="rounded-md border border-line bg-surface-2 px-1.5 py-0.5 font-mono text-[10.5px] text-fg-muted">
              NO_SCHEDULER
            </span>
          </div>
        </div>
      </div>

      {/* V6 Canonical Draft Final Review and Platform Variant Preview card */}
      <div className="rounded-lg border border-line bg-surface-2 p-4">
        <div className="flex items-center justify-between">
          <span className="font-mono text-[11px] uppercase tracking-wide text-fg-subtle">
            V6 CANONICAL DRAFT FINAL REVIEW & PLATFORM VARIANT PREVIEW
          </span>
          <StatusChip status="blocked" icon>
            operator_final_approval_required
          </StatusChip>
        </div>
        <h2 className="mt-2 text-base font-bold text-fg">
          {canonicalDraftFinalReviewVariantPreviewPacket.canonical_draft_final_review_to_platform_variant_preview_packet_id}
        </h2>
        <p className="mt-1 text-xs text-fg-muted">
          status: {canonicalDraftFinalReviewVariantPreviewPacket.canonical_draft_final_review_status} · variant status: {canonicalDraftFinalReviewVariantPreviewPacket.platform_variant_preview_status}
        </p>

        {/* Detailed JSON fields */}
        <div className="mt-3 text-xs leading-relaxed text-fg-muted bg-status-blocked/5 p-2 rounded-lg border border-status-blocked/30 space-y-1.5 font-mono">
          <div><span className="font-semibold text-fg">canonical_draft_final_review_to_platform_variant_preview_packet_id:</span> {canonicalDraftFinalReviewVariantPreviewPacket.canonical_draft_final_review_to_platform_variant_preview_packet_id}</div>
          <div><span className="font-semibold text-fg">canonical_draft_final_review_status:</span> {canonicalDraftFinalReviewVariantPreviewPacket.canonical_draft_final_review_status}</div>
          <div><span className="font-semibold text-fg">platform_variant_preview_status:</span> {canonicalDraftFinalReviewVariantPreviewPacket.platform_variant_preview_status}</div>
          <div><span className="font-semibold text-fg">final_article_approved:</span> {String(canonicalDraftFinalReviewVariantPreviewPacket.final_article_approved)}</div>
          <div><span className="font-semibold text-fg">operator_final_approval_required:</span> {String(canonicalDraftFinalReviewVariantPreviewPacket.operator_final_approval_required)}</div>
          <div><span className="font-semibold text-fg">platform_variants_created:</span> {String(canonicalDraftFinalReviewVariantPreviewPacket.platform_variants_created)}</div>
          <div><span className="font-semibold text-fg">platform_variants_are_preview_only:</span> {String(canonicalDraftFinalReviewVariantPreviewPacket.platform_variants_are_preview_only)}</div>
          <div><span className="font-semibold text-fg">platform_payloads_approved:</span> {String(canonicalDraftFinalReviewVariantPreviewPacket.platform_payloads_approved)}</div>
          <div><span className="font-semibold text-fg">ready_for_auto_publish:</span> {String(canonicalDraftFinalReviewVariantPreviewPacket.ready_for_auto_publish)}</div>
          <div><span className="font-semibold text-fg">ready_for_dispatch:</span> {String(canonicalDraftFinalReviewVariantPreviewPacket.ready_for_dispatch)}</div>
          <div><span className="font-semibold text-fg">llm_provider_call_made:</span> {String(canonicalDraftFinalReviewVariantPreviewPacket.llm_provider_call_made)}</div>
          <div><span className="font-semibold text-fg">provider_call_made:</span> {String(canonicalDraftFinalReviewVariantPreviewPacket.provider_call_made)}</div>
          <div><span className="font-semibold text-fg">platform_api_used:</span> {String(canonicalDraftFinalReviewVariantPreviewPacket.platform_api_used)}</div>
          <div><span className="font-semibold text-fg">network_call_made:</span> {String(canonicalDraftFinalReviewVariantPreviewPacket.network_call_made)}</div>
          <div><span className="font-semibold text-fg">public_url_fetch_made:</span> {String(canonicalDraftFinalReviewVariantPreviewPacket.public_url_fetch_made)}</div>
          <div><span className="font-semibold text-fg">env_value_read_made:</span> {String(canonicalDraftFinalReviewVariantPreviewPacket.env_value_read_made)}</div>
          <div><span className="font-semibold text-fg">credential_read_made:</span> {String(canonicalDraftFinalReviewVariantPreviewPacket.credential_read_made)}</div>
          <div><span className="font-semibold text-fg">browser_session_used:</span> {String(canonicalDraftFinalReviewVariantPreviewPacket.browser_session_used)}</div>
          <div><span className="font-semibold text-fg">public_url_verification_performed:</span> {String(canonicalDraftFinalReviewVariantPreviewPacket.public_url_verification_performed)}</div>
          <div><span className="font-semibold text-fg">forbidden_financial_advice_or_signal_wording_present:</span> {String(canonicalDraftFinalReviewVariantPreviewPacket.forbidden_financial_advice_or_signal_wording_present)}</div>
        </div>

        {/* Previews map */}
        <div className="mt-4 border-t border-line pt-3">
          <div className="font-semibold text-sm text-fg mb-2">Committed Preview Variants:</div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {Object.entries(canonicalDraftFinalReviewVariantPreviewPacket.preview_variants).map(([platform, preview]) => (
              <div key={platform} className="p-2 border border-line bg-surface-1 rounded-md">
                <div className="font-semibold text-xs text-accent uppercase">{platform.replace(/_/g, ' ')}</div>
                <div className="font-bold text-xs text-fg mt-1">{preview.title}</div>
                <div className="text-xs text-fg-muted mt-1 leading-relaxed">{preview.body}</div>
                <div className="text-[10px] text-fg-subtle mt-1 font-mono">status: {preview.status}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-3 text-xs leading-relaxed text-fg-muted bg-status-blocked/5 p-2 rounded-lg border border-status-blocked/30">
          Platform variant preview status is platform_variant_preview_created_for_operator_review.
          Draft final review status is ready_for_operator_final_review.
          Approval record and outbox entries remain uncreated.
          Readiness locks: final_article_approved=false · platform_payloads_approved=false.
          Drafting/publishing gates remain locked: ready_for_auto_publish=false · ready_for_dispatch=false.
          No LLM/provider call is allowed on this local-first review workflow.
        </div>
      </div>

      {/* V6 Platform variant final review and approval packet preview card */}
      <div className="rounded-lg border border-line bg-surface-2 p-4">
        <div className="flex items-center justify-between">
          <span className="font-mono text-[11px] uppercase tracking-wide text-fg-subtle">
            V6 PLATFORM VARIANT FINAL REVIEW & APPROVAL PACKET PREVIEW
          </span>
          <StatusChip status="review">
            {platformVariantApprovalPacketPreviewPacket.approval_packet_preview_status}
          </StatusChip>
        </div>
        <h2 className="mt-2 text-base font-bold text-fg">
          {platformVariantApprovalPacketPreviewPacket.platform_variant_final_review_to_approval_packet_preview_packet_id}
        </h2>
        <p className="mt-1 text-xs text-fg-muted">
          status: {platformVariantApprovalPacketPreviewPacket.platform_variant_final_review_status} · variant status: {platformVariantApprovalPacketPreviewPacket.approval_packet_preview_status}
        </p>

        {/* Detailed JSON fields */}
        <div className="mt-3 text-xs leading-relaxed text-fg-muted bg-status-blocked/5 p-2 rounded-lg border border-status-blocked/30 space-y-1.5 font-mono">
          <div><span className="font-semibold text-fg">approval_packet_preview_id:</span> {platformVariantApprovalPacketPreviewPacket.platform_variant_final_review_to_approval_packet_preview_packet_id}</div>
          <div><span className="font-semibold text-fg">platform_variant_final_review_status:</span> {platformVariantApprovalPacketPreviewPacket.platform_variant_final_review_status}</div>
          <div><span className="font-semibold text-fg">approval_packet_preview_status:</span> {platformVariantApprovalPacketPreviewPacket.approval_packet_preview_status}</div>
          <div><span className="font-semibold text-fg">exact_platform_payload_previews_created:</span> {String(platformVariantApprovalPacketPreviewPacket.exact_platform_payload_previews_created)}</div>
          <div><span className="font-semibold text-fg">exact_payload_hashes_created:</span> {String(platformVariantApprovalPacketPreviewPacket.exact_payload_hashes_created)}</div>
          <div><span className="font-semibold text-fg">approval_packet_preview_created:</span> {String(platformVariantApprovalPacketPreviewPacket.approval_packet_preview_created)}</div>
          <div><span className="font-semibold text-fg">actual_operator_approval_recorded:</span> {String(platformVariantApprovalPacketPreviewPacket.actual_operator_approval_recorded)}</div>
          <div><span className="font-semibold text-fg">approval_ledger_entry_created:</span> {String(platformVariantApprovalPacketPreviewPacket.approval_ledger_entry_created)}</div>
          <div><span className="font-semibold text-fg">approval_record_created:</span> {String(platformVariantApprovalPacketPreviewPacket.approval_record_created)}</div>
          <div><span className="font-semibold text-fg">approval_signature_present:</span> {String(platformVariantApprovalPacketPreviewPacket.approval_signature_present)}</div>
          <div><span className="font-semibold text-fg">approval_signature_required:</span> {String(platformVariantApprovalPacketPreviewPacket.approval_signature_required)}</div>
          <div><span className="font-semibold text-fg">outbox_entry_created:</span> {String(platformVariantApprovalPacketPreviewPacket.outbox_entry_created)}</div>
          <div><span className="font-semibold text-fg">dispatch_outbox_ready:</span> {String(platformVariantApprovalPacketPreviewPacket.dispatch_outbox_ready)}</div>
          <div><span className="font-semibold text-fg">platform_payloads_approved:</span> {String(platformVariantApprovalPacketPreviewPacket.platform_payloads_approved)}</div>
          <div><span className="font-semibold text-fg">final_article_approved:</span> {String(platformVariantApprovalPacketPreviewPacket.final_article_approved)}</div>
          <div><span className="font-semibold text-fg">ready_for_auto_publish:</span> {String(platformVariantApprovalPacketPreviewPacket.ready_for_auto_publish)}</div>
          <div><span className="font-semibold text-fg">ready_for_dispatch:</span> {String(platformVariantApprovalPacketPreviewPacket.ready_for_dispatch)}</div>
          <div><span className="font-semibold text-fg">llm_provider_call_made:</span> {String(platformVariantApprovalPacketPreviewPacket.llm_provider_call_made)}</div>
          <div><span className="font-semibold text-fg">provider_call_made:</span> {String(platformVariantApprovalPacketPreviewPacket.provider_call_made)}</div>
          <div><span className="font-semibold text-fg">platform_api_used:</span> {String(platformVariantApprovalPacketPreviewPacket.platform_api_used)}</div>
          <div><span className="font-semibold text-fg">network_call_made:</span> {String(platformVariantApprovalPacketPreviewPacket.network_call_made)}</div>
          <div><span className="font-semibold text-fg">public_url_fetch_made:</span> {String(platformVariantApprovalPacketPreviewPacket.public_url_fetch_made)}</div>
          <div><span className="font-semibold text-fg">env_value_read_made:</span> {String(platformVariantApprovalPacketPreviewPacket.env_value_read_made)}</div>
          <div><span className="font-semibold text-fg">credential_read_made:</span> {String(platformVariantApprovalPacketPreviewPacket.credential_read_made)}</div>
          <div><span className="font-semibold text-fg">browser_session_used:</span> {String(platformVariantApprovalPacketPreviewPacket.browser_session_used)}</div>
          <div><span className="font-semibold text-fg">public_url_verification_performed:</span> {String(platformVariantApprovalPacketPreviewPacket.public_url_verification_performed)}</div>
          <div><span className="font-semibold text-fg">forbidden_financial_advice_or_signal_wording_present:</span> {String(platformVariantApprovalPacketPreviewPacket.forbidden_financial_advice_or_signal_wording_present)}</div>
        </div>

        {/* Pre-platform hash-bound preview rows */}
        <div className="mt-4 border-t border-line pt-3">
          <div className="font-semibold text-sm text-fg mb-2">Per-Platform Hash-Bound Previews (10):</div>
          <div className="space-y-3">
            {Object.entries(platformVariantApprovalPacketPreviewPacket.approval_targets).map(([key, target]) => (
              <div key={key} className="p-3 border border-line bg-surface-1 rounded-lg">
                <div className="flex justify-between items-center">
                  <span className="font-semibold text-xs text-accent uppercase">{target.platform_id}</span>
                  <StatusChip status="review">{target.destination_binding_status}</StatusChip>
                </div>
                <div className="mt-1 font-mono text-[10px] text-fg-subtle">
                  hash: <span className="text-fg">{target.payload_hash}</span> ·
                  adapter: <span className="text-fg">{target.adapter_class}</span> ·
                  credentials: <span className="text-fg">{target.credential_handle_status}</span>
                </div>
                <div className="mt-1.5 p-2 bg-surface-2 border border-line rounded text-xs font-mono text-fg-muted whitespace-pre-wrap">
                  {target.exact_preview_text}
                </div>
                <div className="mt-2 flex gap-3 text-[10.5px]">
                  <span className="text-fg-subtle">Approval required: <strong className="text-fg">true</strong></span>
                  <span className="text-fg-subtle">Approved: <strong className="text-status-blocked">false</strong></span>
                  <span className="text-fg-subtle">Dispatchable: <strong className="text-status-blocked">false</strong></span>
                </div>
                <div className="mt-1 text-[10.5px] text-status-blocked bg-status-blocked/5 p-1 px-2 rounded border border-status-blocked/10 font-mono">
                  blocked_reason: {target.blocked_reason}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-3 text-xs leading-relaxed text-fg-muted bg-status-blocked/5 p-2 rounded-lg border border-status-blocked/30 font-mono">
          <div>platform_variant_final_review_status=ready_for_operator_approval_packet_review</div>
          <div>approval_packet_preview_status=approval_packet_preview_created_for_operator_review</div>
          <div>actual_operator_approval_recorded=false</div>
          <div>approval_ledger_entry_created=false</div>
          <div>platform_payloads_approved=false</div>
          <div>dispatch_outbox_ready=false</div>
          <div>ready_for_dispatch=false</div>
          <div>Locks: no LLM/provider/API/env/credential/public URL/live action</div>
        </div>
      </div>

      <div className="mb-6 p-4 border border-line bg-surface-2 rounded-xl">
        <div className="flex justify-between items-start gap-4 flex-wrap">
          <div>
            <div className="font-mono text-[10.5px] font-bold uppercase tracking-wider text-fg-subtle">
              V6 dispatch outbox dry-run preview (10)
            </div>
            <h2 className="text-base font-bold text-fg mt-1">
              Dry-run outbox rows with hash binding and blocked/deferred states
            </h2>
          </div>
          <StatusChip status="blocked">{dispatchOutboxDryRunPacket.dispatch_outbox_dry_run_status}</StatusChip>
        </div>

        <div className="mt-4">
          <div className="font-semibold text-sm text-fg mb-2">Per-Platform Outbox Dry-Run Rows (10):</div>
          <div className="space-y-3">
            {Object.entries(dispatchOutboxDryRunPacket.dry_run_entries).map(([key, entry]) => (
              <div key={key} className="p-3 border border-line bg-surface-1 rounded-lg">
                <div className="flex justify-between items-center">
                  <span className="font-semibold text-xs text-accent uppercase">{entry.platform_id}</span>
                  <StatusChip status="review">{entry.destination_binding_status}</StatusChip>
                </div>
                <div className="mt-1 font-mono text-[10px] text-fg-subtle">
                  hash: <span className="text-fg">{entry.dry_run_payload_hash}</span> ·
                  adapter: <span className="text-fg">{entry.adapter_class}</span> ·
                  credentials: <span className="text-fg">{entry.credential_handle_status}</span>
                </div>
                <div className="mt-1.5 p-2 bg-surface-2 border border-line rounded text-xs font-mono text-fg-muted whitespace-pre-wrap">
                  {entry.dry_run_payload_text}
                </div>
                <div className="mt-2 flex gap-3 text-[10.5px]">
                  <span className="text-fg-subtle">Approval required: <strong className="text-fg">true</strong></span>
                  <span className="text-fg-subtle">Approved: <strong className="text-status-blocked">false</strong></span>
                  <span className="text-fg-subtle">Dispatchable: <strong className="text-status-blocked">false</strong></span>
                </div>
                <div className="mt-1 text-[10.5px] text-status-blocked bg-status-blocked/5 p-1 px-2 rounded border border-status-blocked/10 font-mono">
                  {entry.blocked_reason ? `blocked_reason: ${entry.blocked_reason}` : `deferred_reason: ${entry.deferred_reason}`}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-3 text-xs leading-relaxed text-fg-muted bg-status-blocked/5 p-2 rounded-lg border border-status-blocked/30 font-mono">
          <div>dispatch_outbox_dry_run_status=dispatch_outbox_dry_run_created_for_operator_review</div>
          <div>executable_outbox_entry_created=false</div>
          <div>real_outbox_entry_created=false</div>
          <div>dispatch_outbox_ready=false</div>
          <div>dispatch_attempted=false</div>
          <div>dispatch_request_count=0</div>
          <div>webhook_request_count=0</div>
          <div>platform_api_request_count=0</div>
          <div>kill_switch_active=true</div>
          <div>ready_for_dispatch=false</div>
          <div>Locks: no LLM/provider/API/env/credential/public URL/live action</div>
        </div>
      </div>

      <div className="mb-6 p-4 border border-line bg-surface-2 rounded-xl">
        <div className="flex justify-between items-start gap-4 flex-wrap">
          <div>
            <div className="font-mono text-[10.5px] font-bold uppercase tracking-wider text-fg-subtle">
              V6 dispatch outbox operator runbook & recovery (10)
            </div>
            <h2 className="text-base font-bold text-fg mt-1">
              Manual fallback steps, rollback conditions, and failure mode matrix
            </h2>
          </div>
          <StatusChip status="blocked">{dispatchOutboxOperatorRecoveryPacket.operator_recovery_status}</StatusChip>
        </div>

        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <div className="font-semibold text-xs text-accent uppercase tracking-wider mb-2 font-mono">Manual Dispatch Fallback Steps</div>
            <div className="space-y-2">
              {dispatchOutboxOperatorRecoveryPacket.manual_dispatch_fallback_steps.map((item) => (
                <div key={item.step_id} className="p-2.5 border border-line bg-surface-1 rounded-lg text-xs">
                  <div className="font-semibold text-fg font-mono uppercase text-[9.5px]">{item.step_id} · target: {item.target}</div>
                  <div className="mt-1 text-fg-muted leading-relaxed">{item.action}</div>
                </div>
              ))}
            </div>
          </div>

          <div>
            <div className="font-semibold text-xs text-accent uppercase tracking-wider mb-2 font-mono">Dry-Run Replay Verification Steps</div>
            <div className="space-y-2">
              {dispatchOutboxOperatorRecoveryPacket.dry_run_replay_steps.map((item) => (
                <div key={item.replay_id} className="p-2.5 border border-line bg-surface-1 rounded-lg text-xs">
                  <div className="flex justify-between items-center font-mono text-[9.5px]">
                    <span className="font-semibold text-fg uppercase">{item.replay_id}</span>
                    <StatusChip status="verified">{item.status}</StatusChip>
                  </div>
                  <div className="mt-1 text-fg-muted leading-relaxed">{item.action}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-4 border-t border-line pt-3">
          <div className="font-semibold text-xs text-accent uppercase tracking-wider mb-2 font-mono">Failure Mode & Recovery Matrix</div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {dispatchOutboxOperatorRecoveryPacket.failure_mode_matrix.map((item, idx) => (
              <div key={idx} className="p-3 border border-line bg-surface-1 rounded-lg text-xs font-mono">
                <div className="font-bold text-fg">Mode: {item.failure_mode}</div>
                <div className="mt-1 text-status-blocked">Impact: {item.impact}</div>
                <div className="mt-1 text-fg-subtle">Action: {item.recovery_action}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-4 border-t border-line pt-3">
          <div className="font-semibold text-xs text-accent uppercase tracking-wider mb-2 font-mono">Platform-Specific Manual Handoff & Recovery Notes</div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {Object.entries(dispatchOutboxOperatorRecoveryPacket.platform_specific_recovery_notes).map(([key, val]) => (
              <div key={key} className="p-2.5 border border-line bg-surface-1 rounded-lg text-xs">
                <div className="font-bold text-accent uppercase text-[10px] font-mono">{key.replace('_', ' ')}</div>
                <div className="mt-1 text-fg-muted leading-relaxed font-mono">{val}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-4 rounded-lg border border-status-blocked/30 bg-status-blocked/5 p-3 text-xs leading-relaxed text-fg-muted font-mono">
          <div>operator_recovery_status=operator_recovery_runbook_created_for_review</div>
          <div>executable_outbox_entry_created=false</div>
          <div>real_outbox_entry_created=false</div>
          <div>dispatch_outbox_ready=false</div>
          <div>dispatch_attempted=false</div>
          <div>dispatch_request_count=0</div>
          <div>webhook_request_count=0</div>
          <div>platform_api_request_count=0</div>
          <div>kill_switch_active=true</div>
          <div>ready_for_dispatch=false</div>
          <div>blocked_until_explicit_live_scope=true</div>
          <div>Locks: no LLM/provider/API/env/credential/public URL/live action</div>
        </div>
      </div>

      <div className="mb-6 p-4 border border-line bg-surface-2 rounded-xl">
        <div className="flex justify-between items-start gap-4 flex-wrap">
          <div>
            <div className="font-mono text-[10.5px] font-bold uppercase tracking-wider text-fg-subtle">
              V6 explicit live scope gate & source candidate (10)
            </div>
            <h2 className="text-base font-bold text-fg mt-1">
              Parsed Discord normalized candidate message or blocked status
            </h2>
          </div>
          <StatusChip status="blocked">{explicitLiveScopeGatePacket.explicit_live_scope_gate_status}</StatusChip>
        </div>

        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <div className="font-semibold text-xs text-accent uppercase tracking-wider mb-2 font-mono">Normalized Message Candidate Body</div>
            <div className="p-3 border border-line bg-surface-1 rounded-lg text-xs leading-relaxed font-mono whitespace-pre-wrap min-h-[100px] text-fg-muted">
              {normalizedDispatchCandidate.normalized_body_text || "No normalized content body available. Operator source draft is missing or blocked."}
            </div>
          </div>

          <div>
            <div className="font-semibold text-xs text-accent uppercase tracking-wider mb-2 font-mono">Safety Compliance Scans</div>
            <div className="space-y-2">
              <div className="p-2.5 border border-line bg-surface-1 rounded-lg text-xs flex justify-between items-center">
                <span className="text-fg-muted font-mono">safety_scan:</span>
                <StatusChip status={normalizedDispatchCandidate.safety_scan === 'passed' ? 'verified' : 'blocked'}>
                  {normalizedDispatchCandidate.safety_scan}
                </StatusChip>
              </div>
              <div className="p-2.5 border border-line bg-surface-1 rounded-lg text-xs font-mono">
                <div className="text-fg-subtle">blocked_reasons:</div>
                <div className="mt-1 text-status-blocked">{JSON.stringify(normalizedDispatchCandidate.blocked_reasons)}</div>
              </div>
              <div className="p-2.5 border border-line bg-surface-1 rounded-lg text-xs flex justify-between items-center font-mono">
                <span className="text-fg-muted">no_secret_material_present:</span>
                <span className="font-semibold text-fg">{String(normalizedDispatchCandidate.no_secret_material_present)}</span>
              </div>
              <div className="p-2.5 border border-line bg-surface-1 rounded-lg text-xs flex justify-between items-center font-mono">
                <span className="text-fg-muted">live_scope_required:</span>
                <span className="font-semibold text-fg">{String(normalizedDispatchCandidate.live_scope_required)}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-4 rounded-lg border border-status-blocked/30 bg-status-blocked/5 p-3 text-xs leading-relaxed text-fg-muted font-mono">
          <div>explicit_live_scope_gate_status=created_for_operator_review</div>
          <div>executable_outbox_entry_created=false</div>
          <div>real_outbox_entry_created=false</div>
          <div>dispatch_outbox_ready=false</div>
          <div>dispatch_attempted=false</div>
          <div>dispatch_request_count=0</div>
          <div>webhook_request_count=0</div>
          <div>platform_api_request_count=0</div>
          <div>kill_switch_active=true</div>
          <div>ready_for_dispatch=false</div>
          <div>blocked_until_explicit_live_scope=true</div>
          <div>Locks: no LLM/provider/API/env/credential/public URL/live action</div>
        </div>
      </div>

      {/* Platform selector tabs */}
      <div
        role="tablist"
        aria-label="Platform payload previews"
        className="flex flex-wrap gap-1.5"
      >
        {previews.map((p) => {
          const isActive = p.platform_key === activeKey;
          return (
            <button
              type="button"
              key={p.platform_key}
              id={`platform-tab-${p.platform_key}`}
              role="tab"
              aria-selected={isActive}
              onClick={() => {
                setActiveKey(p.platform_key);
                select(selectPlatformPayloadPreview(p));
              }}
              className={`flex items-center gap-2 rounded-lg border px-3 py-1.5 text-sm font-medium transition-colors ${
                isActive
                  ? 'border-accent/40 bg-accent/5 text-fg'
                  : 'border-line bg-surface-2 text-fg-muted hover:border-line-strong hover:text-fg'
              }`}
            >
              <StatusDot status={p.fit_status} />
              {p.platform}
            </button>
          );
        })}
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        {/* Compiled payload */}
        <div className="space-y-6 xl:col-span-2">
          <Panel
            title={
              <button
                type="button"
                id={`payload-summary-${active.platform_key}`}
                onClick={() => select(selectPlatformPayloadPreview(active))}
                className="text-left text-sm font-semibold text-fg hover:text-accent"
              >
                {active.platform} payload
              </button>
            }
            subtitle={active.format_label}
            actions={
              <StatusChip status={active.fit_status}>
                {active.fit_status}
              </StatusChip>
            }
            bodyClassName="p-4 space-y-3"
          >
            {active.fields.map((f) => (
              <div key={f.id}>
                <SectionLabel>{f.label}</SectionLabel>
                <p
                  className={`rounded-lg border border-line bg-surface-2 p-3 text-sm leading-relaxed text-fg-muted ${
                    f.mono ? 'break-all font-mono text-[12px]' : ''
                  }`}
                >
                  {f.value}
                </p>
              </div>
            ))}
            <p className="flex items-center gap-2 pt-1 text-[11px] text-fg-subtle">
              <StatusDot status="neutral" />
              {active.media_note}
            </p>
          </Panel>

          {/* Locked dispatch — disabled, future-gated, dry-run only. */}
          <Panel
            title="Dispatch"
            subtitle="Disabled by policy · dry-run preview only"
            bodyClassName="p-4"
          >
            <LockedAction
              label="Dispatch payload"
              reason={active.not_dispatchable_reason}
            />
          </Panel>
        </div>

        {/* Constraints + live status */}
        <div className="space-y-6">
          <Panel
            title="Platform constraints"
            subtitle="Local fit checks · select a row to inspect"
            bodyClassName="p-3 space-y-2"
          >
            {active.constraints.map((c) => {
              const isActive =
                selected?.kind === 'payload_constraint' && selected.id === c.id;
              return (
                <button
                  type="button"
                  key={c.id}
                  id={`constraint-${c.id}`}
                  onClick={() => select(selectPayloadConstraint(c, active.platform))}
                  className={`w-full rounded-lg border px-3 py-2.5 text-left transition-colors ${
                    isActive
                      ? 'border-accent/40 bg-accent/5'
                      : 'border-line bg-surface-2 hover:border-line-strong'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="flex items-center gap-2 text-sm font-medium text-fg">
                      <StatusDot status={c.status} />
                      {c.label}
                    </span>
                    <StatusChip status={c.status}>{c.status}</StatusChip>
                  </div>
                  <p className="mt-1 text-[11px] leading-relaxed text-fg-subtle">
                    <span className="font-mono text-fg-muted">
                      {c.actual} / {c.limit}
                    </span>{' '}
                    · {c.detail}
                  </p>
                </button>
              );
            })}
          </Panel>

          <Panel title="Live status" bodyClassName="p-4 space-y-2">
            <StatusRow label="Live" value={active.live_status} />
            <StatusRow label="Credential" value={active.credential_status} />
            <StatusRow label="Provider" value={active.provider_status} />
            <p className="mt-2 border-t border-line pt-3 font-mono text-[10.5px] leading-relaxed text-status-blocked">
              dispatchable: false · {active.not_dispatchable_reason}
            </p>
          </Panel>
        </div>
      </div>
    </div>
  );
}

function StatusRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-2">
      <span className="flex items-center gap-2 text-sm text-fg-muted">
        <StatusDot status="blocked" />
        {label}
      </span>
      <span className="font-mono text-[11px] text-status-blocked">{value}</span>
    </div>
  );
}
