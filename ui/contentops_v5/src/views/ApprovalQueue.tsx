// Capital Chronicle ContentOps V5 â€” Approval Queue + Dispatch Control view.
// Dispatch is visibly future-gated and DISABLED. No live publish/post/
// schedule/API affordance. No network, no storage, no credentials.

import { SubstackArticleStudioCard } from './SubstackArticleStudioCard';
import {
  substackManualApprovalExportEvidencePacket,
  substackManualExportOperatorHandoffPacket,
  substackManualPublicationUrlAuditImportPacket,
  substackPublicationAuditReviewMetricsSummaryPacket,
  linkedinManualApprovalExportEvidencePacket,
  linkedinManualOperatorHandoffPacket,
  linkedinManualPublicationUrlAuditImportPacket,
  linkedinPublicationAuditReviewMetricsSummaryPacket,
  xManualApprovalExportEvidencePacket,
  xManualOperatorHandoffPacket,
  xManualPublicationUrlAuditImportPacket,
  xPublicationAuditReviewMetricsSummaryPacket,
} from '../data/substackManualExportArticleStudioAdapter';
import { ManualDistributionRegistryPanel } from './ManualDistributionRegistryPanel';
import { operatorFeedbackBacklogSummaryPacket } from '../data/operatorFeedbackBacklogAdapter';
import { feedbackBacklogNextArticleBriefPacket } from '../data/feedbackBacklogNextArticleBriefAdapter';
import { nextArticleBriefSourcePackReviewPacket } from '../data/nextArticleBriefSourcePackReviewAdapter';
import { nextArticleSourcePackIntakeValidationPacket } from '../data/nextArticleSourcePackIntakeValidationAdapter';
import { nextArticleDraftAuthorizationReadinessPacket } from '../data/nextArticleDraftAuthorizationReadinessAdapter';
import { localCanonicalDraftPreviewReviewPacket } from '../data/localCanonicalDraftPreviewReviewAdapter';
import { canonicalDraftFinalReviewVariantPreviewPacket } from '../data/canonicalDraftFinalReviewVariantPreviewAdapter';
import { platformVariantApprovalPacketPreviewPacket } from '../data/platformVariantApprovalPacketPreviewAdapter';
import { useApp } from '../state';
import { viewModel } from '../fixtures';
import { selectDispatchGate } from '../selectors';
import {
  LockedAction,
  Panel,
  SectionLabel,
  StatusChip,
  StatusDot,
  EvidenceChip,
} from '../ui/primitives';

export function ApprovalQueue() {
  const { select, selected } = useApp();
  const packet = viewModel.approval_packets[0];
  const v6Packet = viewModel.v6_operator_approval_evidence;
  const clearedCount = packet.gates.filter((g) => g.cleared).length;

  return (
    <div className="space-y-6">

      <ManualDistributionRegistryPanel />

      <Panel
        title="Operator feedback backlog · manual-only"
        subtitle={`${operatorFeedbackBacklogSummaryPacket.candidate_count} backlog candidates · ${operatorFeedbackBacklogSummaryPacket.summary_method}`}
        actions={<StatusChip status="review">{operatorFeedbackBacklogSummaryPacket.backlog_status}</StatusChip>}
      >
        <div className="mb-3 rounded-lg border border-status-blocked/30 bg-status-blocked/5 p-3 text-xs leading-relaxed text-fg-muted">
          Operator-supplied feedback only. No LLM/provider call, public URL fetch, platform API, browser session, publish, send, dispatch, approve, or schedule action.
        </div>
        <div className="grid grid-cols-1 gap-3 lg:grid-cols-3">
          {operatorFeedbackBacklogSummaryPacket.backlog_candidates.map((candidate) => (
            <article key={candidate.candidate_id} className="rounded-lg border border-line bg-surface-2 p-3">
              <div className="flex items-start justify-between gap-2">
                <h3 className="text-sm font-semibold text-fg">{candidate.title}</h3>
                <StatusChip status="review">score {candidate.priority_score}</StatusChip>
              </div>
              <p className="mt-2 text-xs leading-relaxed text-fg-muted">{candidate.article_angle}</p>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {candidate.source_platforms.map((platform) => <EvidenceChip key={platform}>{platform}</EvidenceChip>)}
              </div>
            </article>
          ))}
        </div>
      </Panel>

      <Panel
        title="Next article brief candidate · review-only"
        subtitle={feedbackBacklogNextArticleBriefPacket.next_article_brief_packet_id}
        actions={<StatusChip status="review">{feedbackBacklogNextArticleBriefPacket.candidate_review_status}</StatusChip>}
      >
        <div className="rounded-lg border border-line bg-surface-2 p-3">
          <div className="font-mono text-[11px] uppercase tracking-wide text-fg-subtle">{feedbackBacklogNextArticleBriefPacket.selected_backlog_candidate_id}</div>
          <h3 className="mt-1 text-sm font-semibold text-fg">{feedbackBacklogNextArticleBriefPacket.brief_candidate.working_headline}</h3>
          <p className="mt-2 text-xs leading-relaxed text-fg-muted">{feedbackBacklogNextArticleBriefPacket.brief_candidate.editorial_angle}</p>
        </div>
        <div className="mt-3 rounded-lg border border-status-blocked/30 bg-status-blocked/5 p-3 text-xs leading-relaxed text-fg-muted">
          Operator review required. source_pack_required_before_drafting={String(feedbackBacklogNextArticleBriefPacket.source_pack_required_before_drafting)} · canonical_draft_created={String(feedbackBacklogNextArticleBriefPacket.canonical_draft_created)} · dispatch_readiness_claimed={String(feedbackBacklogNextArticleBriefPacket.non_readiness_claims.dispatch_readiness_claimed)}.
        </div>
      </Panel>

      <Panel
        title="Next article brief source-pack and review"
        subtitle={`${nextArticleBriefSourcePackReviewPacket.source_pack_review_packet_id} · checklist items: ${nextArticleBriefSourcePackReviewPacket.source_pack_checklist.length}`}
        actions={<StatusChip status="review">{nextArticleBriefSourcePackReviewPacket.operator_review_status}</StatusChip>}
      >
        <div className="rounded-lg border border-line bg-surface-2 p-3 font-mono text-[11.5px] text-fg-muted space-y-2">
          <div><span className="font-semibold text-fg">source_pack_review_packet_id:</span> {nextArticleBriefSourcePackReviewPacket.source_pack_review_packet_id}</div>
          <div><span className="font-semibold text-fg">source_next_article_brief_packet_id:</span> {nextArticleBriefSourcePackReviewPacket.source_next_article_brief_packet_id}</div>
          <div><span className="font-semibold text-fg">source_pack_status:</span> {nextArticleBriefSourcePackReviewPacket.source_pack_status}</div>
          <div><span className="font-semibold text-fg">operator_review_status:</span> {nextArticleBriefSourcePackReviewPacket.operator_review_status}</div>
        </div>
        <div className="mt-3 space-y-1">
          {nextArticleBriefSourcePackReviewPacket.source_pack_checklist.map((item) => (
            <div key={item.check_id} className="flex items-center justify-between gap-2 rounded border border-line bg-surface-1 px-2.5 py-1.5 text-xs">
              <span className="font-medium text-fg">{item.label}</span>
              <StatusChip status="review">{item.status}</StatusChip>
            </div>
          ))}
        </div>
        <div className="mt-3 rounded-lg border border-status-blocked/30 bg-status-blocked/5 p-3 text-xs leading-relaxed text-fg-muted">
          Source pack status is source_pack_required_pending_operator_collection. Operator review status is pending_operator_review.
          Drafting and dispatch gates remain locked: ready_for_llm_drafting=false · ready_for_canonical_draft=false · ready_for_auto_publish=false · ready_for_dispatch=false.
          No LLM/provider call is allowed on this local-first review workflow.
        </div>
      </Panel>

      <Panel
        title="Next article source-pack intake and validation"
        subtitle={`${nextArticleSourcePackIntakeValidationPacket.source_pack_intake_packet_id} · coverage: ${nextArticleSourcePackIntakeValidationPacket.checklist_coverage_status}`}
        actions={<StatusChip status="review">{nextArticleSourcePackIntakeValidationPacket.source_pack_collection_status}</StatusChip>}
      >
        <div className="rounded-lg border border-line bg-surface-2 p-3 font-mono text-[11.5px] text-fg-muted space-y-2">
          <div><span className="font-semibold text-fg">source_pack_intake_packet_id:</span> {nextArticleSourcePackIntakeValidationPacket.source_pack_intake_packet_id}</div>
          <div><span className="font-semibold text-fg">checklist_coverage_status:</span> {nextArticleSourcePackIntakeValidationPacket.checklist_coverage_status}</div>
          <div><span className="font-semibold text-fg">source_entry_count:</span> {nextArticleSourcePackIntakeValidationPacket.source_entry_count}</div>
          <div><span className="font-semibold text-fg">source_url_count:</span> {nextArticleSourcePackIntakeValidationPacket.source_url_count}</div>
        </div>
        <div className="mt-3 space-y-1">
          {nextArticleSourcePackIntakeValidationPacket.source_entries.map((entry) => (
            <div key={entry.source_entry_id} className="rounded border border-line bg-surface-1 p-2 text-xs">
              <div className="flex items-center justify-between gap-2">
                <span className="font-medium text-fg">{entry.source_title}</span>
                <StatusChip status="review">{entry.validation_status}</StatusChip>
              </div>
              <p className="mt-1 text-[11px] text-fg-muted">{entry.operator_supplied_summary}</p>
            </div>
          ))}
        </div>
        <div className="mt-3 rounded-lg border border-status-blocked/30 bg-status-blocked/5 p-3 text-xs leading-relaxed text-fg-muted">
          Intake status: operator_source_pack_supplied_for_review. Validation status: local_metadata_validation_pending_operator_review.
          Checklist coverage: source_pack_collection_status={nextArticleSourcePackIntakeValidationPacket.source_pack_collection_status}.
          Verified URLs: network_verified_url_count=0. Verified sources: api_verified_source_count=0.
          Drafting status: ready_for_llm_drafting=false · ready_for_canonical_draft=false · ready_for_auto_publish=false · ready_for_dispatch=false.
          No LLM/provider call is allowed on this local-first review workflow.
        </div>
      </Panel>

      <Panel
        title="Next article draft authorization and readiness"
        subtitle={`${nextArticleDraftAuthorizationReadinessPacket.draft_authorization_packet_id} · ready: ${String(nextArticleDraftAuthorizationReadinessPacket.ready_for_local_canonical_draft_workflow)}`}
        actions={<StatusChip status="verified">{nextArticleDraftAuthorizationReadinessPacket.local_draft_readiness_status}</StatusChip>}
      >
        <div className="rounded-lg border border-line bg-surface-2 p-3 font-mono text-[11.5px] text-fg-muted space-y-2">
          <div><span className="font-semibold text-fg">draft_authorization_packet_id:</span> {nextArticleDraftAuthorizationReadinessPacket.draft_authorization_packet_id}</div>
          <div><span className="font-semibold text-fg">draft_readiness_packet_id:</span> {nextArticleDraftAuthorizationReadinessPacket.draft_readiness_packet_id}</div>
          <div><span className="font-semibold text-fg">source_pack_intake_packet_id:</span> {nextArticleDraftAuthorizationReadinessPacket.source_pack_intake_packet_id}</div>
          <div><span className="font-semibold text-fg">authorization_record_status:</span> {nextArticleDraftAuthorizationReadinessPacket.authorization_record_status}</div>
          <div><span className="font-semibold text-fg">authorization_scope:</span> {nextArticleDraftAuthorizationReadinessPacket.authorization_scope}</div>
          <div><span className="font-semibold text-fg">local_draft_readiness_status:</span> {nextArticleDraftAuthorizationReadinessPacket.local_draft_readiness_status}</div>
          <div><span className="font-semibold text-fg">source_entry_count:</span> {nextArticleDraftAuthorizationReadinessPacket.source_entry_count}</div>
        </div>
        <div className="mt-3 rounded-lg border border-status-blocked/30 bg-status-blocked/5 p-3 text-xs leading-relaxed text-fg-muted">
          Authorization record status is operator_drafting_authorization_recorded. Scope is local_canonical_draft_preparation_only.
          Local draft readiness status: ready_for_local_canonical_draft_workflow=true.
          Drafting/publishing gates remain locked: ready_for_llm_drafting=false · ready_for_provider_drafting=false · canonical_draft_created=false · article_body_created=false · ready_for_auto_publish=false · ready_for_dispatch=false.
          No LLM/provider call is allowed on this local-first review workflow.
        </div>
      </Panel>

      <Panel
        title="Local canonical draft preview and review"
        subtitle={`${localCanonicalDraftPreviewReviewPacket.local_draft_preview_packet_id} · review: ${localCanonicalDraftPreviewReviewPacket.draft_review_status}`}
        actions={<StatusChip status="review">{localCanonicalDraftPreviewReviewPacket.draft_preview_status}</StatusChip>}
      >
        <div className="rounded-lg border border-line bg-surface-2 p-3 font-mono text-[11.5px] text-fg-muted space-y-2">
          <div><span className="font-semibold text-fg">local_draft_preview_packet_id:</span> {localCanonicalDraftPreviewReviewPacket.local_draft_preview_packet_id}</div>
          <div><span className="font-semibold text-fg">draft_review_packet_id:</span> {localCanonicalDraftPreviewReviewPacket.draft_review_packet_id}</div>
          <div><span className="font-semibold text-fg">draft_preview_status:</span> {localCanonicalDraftPreviewReviewPacket.draft_preview_status}</div>
          <div><span className="font-semibold text-fg">draft_review_status:</span> {localCanonicalDraftPreviewReviewPacket.draft_review_status}</div>
          <div><span className="font-semibold text-fg">source_draft_authorization_packet_id:</span> {localCanonicalDraftPreviewReviewPacket.source_draft_authorization_packet_id}</div>
          <div><span className="font-semibold text-fg">draft_generation_method:</span> {localCanonicalDraftPreviewReviewPacket.draft_generation_method}</div>
          <div><span className="font-semibold text-fg">canonical_draft_created:</span> {String(localCanonicalDraftPreviewReviewPacket.canonical_draft_created)}</div>
          <div><span className="font-semibold text-fg">article_body_created:</span> {String(localCanonicalDraftPreviewReviewPacket.article_body_created)}</div>
          <div><span className="font-semibold text-fg">final_article_approved:</span> {String(localCanonicalDraftPreviewReviewPacket.final_article_approved)}</div>
          <div><span className="font-semibold text-fg">working_title:</span> {localCanonicalDraftPreviewReviewPacket.working_title}</div>
        </div>
        <div className="mt-3 rounded-lg border border-status-blocked/30 bg-status-blocked/5 p-3 text-xs leading-relaxed text-fg-muted space-y-1">
          <div>Draft preview status is local_draft_preview_created_for_review. Review status is pending_operator_review.</div>
          <div>Draft generation method: deterministic_template_no_llm.</div>
          <div>Gates: canonical_draft_created=true · article_body_created=true · final_article_approved=false.</div>
          <div>Readiness locks: separate_final_approval_task_required=true · separate_platform_variant_task_required=true · separate_publish_authorization_required=true · public_url_verification_performed=false.</div>
          <div>Drafting/publishing gates remain locked: ready_for_llm_drafting=false · ready_for_provider_drafting=false · ready_for_auto_publish=false · ready_for_dispatch=false.</div>
          <div>No LLM/provider call is allowed on this local-first review workflow.</div>
        </div>
      </Panel>

      <Panel
        title="V6 canonical draft final review and platform variant preview"
        subtitle={`${canonicalDraftFinalReviewVariantPreviewPacket.canonical_draft_final_review_to_platform_variant_preview_packet_id} · status: ${canonicalDraftFinalReviewVariantPreviewPacket.canonical_draft_final_review_status}`}
        actions={<StatusChip status="review">{canonicalDraftFinalReviewVariantPreviewPacket.platform_variant_preview_status}</StatusChip>}
      >
        <div className="rounded-lg border border-line bg-surface-2 p-3 font-mono text-[11.5px] text-fg-muted space-y-2">
          <div><span className="font-semibold text-fg">final_review_packet_id:</span> {canonicalDraftFinalReviewVariantPreviewPacket.canonical_draft_final_review_to_platform_variant_preview_packet_id}</div>
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
          <div><span className="font-semibold text-fg">network_call_made:</span> {String(canonicalDraftFinalReviewVariantPreviewPacket.network_call_made)}</div>
          <div><span className="font-semibold text-fg">public_url_verification_performed:</span> {String(canonicalDraftFinalReviewVariantPreviewPacket.public_url_verification_performed)}</div>
          <div><span className="font-semibold text-fg">forbidden_financial_advice_wording:</span> {String(canonicalDraftFinalReviewVariantPreviewPacket.forbidden_financial_advice_or_signal_wording_present)}</div>
        </div>

        <div className="mt-3 border-t border-line pt-2">
          <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle mb-1">Preview Variants</div>
          <div className="space-y-2">
            {Object.entries(canonicalDraftFinalReviewVariantPreviewPacket.preview_variants).slice(0, 4).map(([platform, preview]) => (
              <div key={platform} className="p-2 border border-line bg-surface-1 rounded text-xs">
                <div className="font-semibold text-accent uppercase text-[10px]">{platform.replace(/_/g, ' ')}</div>
                <div className="font-bold mt-0.5 text-fg">{preview.title}</div>
                <p className="text-fg-muted text-[11px] leading-snug mt-0.5">{preview.body}</p>
              </div>
            ))}
            <div className="text-[10px] text-fg-subtle italic">Showing first 4 of 10 variants. Go to Platform Preview to view all.</div>
          </div>
        </div>

        <div className="mt-3 rounded-lg border border-status-blocked/30 bg-status-blocked/5 p-3 text-xs leading-relaxed text-fg-muted">
          Platform variant preview status is platform_variant_preview_created_for_operator_review.
          Draft final review status is ready_for_operator_final_review.
          Approval record and outbox entries remain uncreated.
          Readiness locks: final_article_approved=false · platform_payloads_approved=false.
          Drafting/publishing gates remain locked: ready_for_auto_publish=false · ready_for_dispatch=false.
          No LLM/provider call is allowed on this local-first review workflow.
        </div>
      </Panel>

      <Panel
        title="V6 platform variant approval packet preview · primary"
        subtitle={`${platformVariantApprovalPacketPreviewPacket.platform_variant_final_review_to_approval_packet_preview_packet_id} · status: ${platformVariantApprovalPacketPreviewPacket.platform_variant_final_review_status}`}
        actions={<StatusChip status="review">{platformVariantApprovalPacketPreviewPacket.approval_packet_preview_status}</StatusChip>}
      >
        <div className="rounded-lg border border-line bg-surface-2 p-3 font-mono text-[11.5px] text-fg-muted space-y-2">
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
          <div><span className="font-semibold text-fg">network_call_made:</span> {String(platformVariantApprovalPacketPreviewPacket.network_call_made)}</div>
          <div><span className="font-semibold text-fg">public_url_verification_performed:</span> {String(platformVariantApprovalPacketPreviewPacket.public_url_verification_performed)}</div>
          <div><span className="font-semibold text-fg">forbidden_financial_advice_or_signal_wording:</span> {String(platformVariantApprovalPacketPreviewPacket.forbidden_financial_advice_or_signal_wording_present)}</div>
        </div>

        <div className="mt-4 border-t border-line pt-3">
          <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle mb-2">Committed Approval Targets (10)</div>
          <div className="space-y-3">
            {Object.entries(platformVariantApprovalPacketPreviewPacket.approval_targets).map(([key, target]) => (
              <div key={key} className="p-3 border border-line bg-surface-1 rounded-lg">
                <div className="flex justify-between items-center">
                  <span className="font-semibold text-xs text-accent uppercase">{target.platform_id}</span>
                  <StatusChip status="review">{target.destination_binding_status}</StatusChip>
                </div>
                <div className="mt-1 font-mono text-[10px] text-fg-subtle">
                  hash: <span className="text-fg">{target.payload_hash.slice(0, 12)}...</span> ·
                  adapter: <span className="text-fg">{target.adapter_class}</span> ·
                  credentials: <span className="text-fg">{target.credential_handle_status}</span>
                </div>
                <div className="mt-1 text-xs text-fg-muted italic line-clamp-2">"{target.exact_preview_text}"</div>
                <div className="mt-1.5 flex gap-3 text-[10.5px]">
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

        <div className="mt-3 rounded-lg border border-status-blocked/30 bg-status-blocked/5 p-3 text-xs leading-relaxed text-fg-muted font-mono">
          <div>platform_variant_final_review_status=ready_for_operator_approval_packet_review</div>
          <div>approval_packet_preview_status=approval_packet_preview_created_for_operator_review</div>
          <div>actual_operator_approval_recorded=false</div>
          <div>approval_ledger_entry_created=false</div>
          <div>platform_payloads_approved=false</div>
          <div>dispatch_outbox_ready=false</div>
          <div>ready_for_dispatch=false</div>
          <div>Locks: no LLM/provider/API/env/credential/public URL/live action</div>
        </div>
      </Panel>
      <SubstackArticleStudioCard mode="approval" />
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="font-mono text-[11px] font-bold uppercase tracking-[0.14em] text-fg-subtle">
            Approval &amp; Dispatch Control
          </div>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight text-fg">
            Manual approval, future-gated dispatch
          </h1>
          <p className="mt-1 max-w-2xl text-sm leading-relaxed text-fg-muted">
            Manual approval packets and a future-gated dispatch hierarchy. No
            live posting, scheduling, or platform/provider API exists.
          </p>
        </div>
        <StatusChip status="blocked" icon>
          Dispatch disabled
        </StatusChip>
      </header>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Panel
          title={`Approval packet Â· ${packet.id}`}
          subtitle={packet.title}
          actions={
            <StatusChip status={packet.approval_status}>
              {packet.approval_state}
            </StatusChip>
          }
        >
          <dl className="space-y-2.5 text-sm">
            <Row label="Approver" value={packet.required_approver} />
            <Row label="Draft hash" value={packet.draft_hash} mono />
            <Row label="Payload hash" value={packet.payload_hash} mono />
            <Row label="Revocation" value={packet.revocation_state} mono />
            <Row label="Redacted audit" value={packet.redacted_audit_state} />
          </dl>

          <div className="mt-4 border-t border-line pt-3">
            <SectionLabel>Evidence sources</SectionLabel>
            <div className="flex flex-wrap gap-1.5">
              {packet.evidence_sources.map((e) => (
                <span
                  key={e}
                  className="rounded-md border border-line bg-surface-2 px-1.5 py-0.5 font-mono text-[10.5px] text-fg-muted"
                >
                  {e}
                </span>
              ))}
            </div>
          </div>

          <div className="mt-4 space-y-2 border-t border-line pt-3">
            {packet.comments.map((c, i) => (
              <p key={i} className="text-xs leading-relaxed text-fg-muted">
                <span className="font-semibold text-fg">{c.author}:</span>{' '}
                {c.note}
              </p>
            ))}
          </div>
        </Panel>

        <Panel
          title="Dispatch gate hierarchy"
          subtitle={`${clearedCount}/${packet.gates.length} gates cleared Â· dispatch globally disabled`}
          actions={<StatusChip status="blocked">Future-gated</StatusChip>}
        >
          <ul className="space-y-1.5">
            {packet.gates.map((g) => {
              const active =
                selected?.kind === 'dispatch_gate' && selected.id === g.id;
              return (
                <li key={g.id}>
                  <button
                    type="button"
                    id={`gate-${g.id}`}
                    onClick={() => select(selectDispatchGate(g))}
                    className={`flex w-full items-center justify-between gap-3 rounded-lg border px-3 py-2.5 text-left transition-colors ${
                      active
                        ? 'border-accent/40 bg-accent/5'
                        : 'border-line bg-surface-2 hover:border-line-strong'
                    }`}
                  >
                    <span className="flex min-w-0 items-center gap-2.5">
                      <StatusDot status={g.cleared ? 'verified' : g.status} />
                      <span className="truncate text-sm text-fg">{g.label}</span>
                    </span>
                    <StatusChip status={g.status}>
                      {g.cleared ? 'cleared' : 'pending'}
                    </StatusChip>
                  </button>
                </li>
              );
            })}
          </ul>

          <div className="mt-4">
            <LockedAction
              label="Dispatch to platform"
              reason="No platform/provider API. Live dispatch is future-gated and globally disabled by policy."
            />
          </div>
        </Panel>
      </div>
      <Panel
        title="Substack manual approval/export evidence"
        subtitle={substackManualApprovalExportEvidencePacket.approval_export_evidence_packet_id}
        actions={<StatusChip status="review">{substackManualApprovalExportEvidencePacket.operator_review_status}</StatusChip>}
      >
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          <Row label="Approval" value={substackManualApprovalExportEvidencePacket.approval_status} />
          <Row label="Manual export" value={substackManualApprovalExportEvidencePacket.manual_export_status} />
          <Row label="Substack API" value={String(substackManualApprovalExportEvidencePacket.substack_api_used)} mono />
        </div>
        <div className="mt-3 rounded-lg border border-status-blocked/30 bg-status-blocked/5 p-3 font-mono text-[11px] text-status-blocked">
          approve/send/publish/dispatch controls enabled={String(substackManualApprovalExportEvidencePacket.enabled_publish_send_dispatch_approve_controls)}
        </div>
      </Panel>
      <Panel
        title="Substack operator handoff pending review"
        subtitle={substackManualExportOperatorHandoffPacket.operator_handoff_packet_id}
        actions={<StatusChip status="review">{substackManualExportOperatorHandoffPacket.operator_handoff_status}</StatusChip>}
      >
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          <Row label="Approval" value={substackManualExportOperatorHandoffPacket.approval_status} />
          <Row label="Manual copy only" value={String(substackManualExportOperatorHandoffPacket.manual_copy_only)} mono />
          <Row label="Live publish" value={String(substackManualExportOperatorHandoffPacket.live_publish_allowed)} mono />
        </div>
        <div className="mt-3 rounded-lg border border-status-blocked/30 bg-status-blocked/5 p-3 font-mono text-[11px] text-status-blocked">
          blocked controls: {substackManualExportOperatorHandoffPacket.blocked_controls.join(', ')} · enabled={String(substackManualExportOperatorHandoffPacket.enabled_publish_send_dispatch_approve_controls)}
        </div>
      </Panel>

      <Panel
        title="Substack manual URL audit import pending review"
        subtitle={substackManualPublicationUrlAuditImportPacket.publication_url_audit_packet_id}
        actions={<StatusChip status="review">{substackManualPublicationUrlAuditImportPacket.operator_review_status}</StatusChip>}
      >
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          <Row label="Audit status" value={substackManualPublicationUrlAuditImportPacket.publication_audit_status} />
          <Row label="URL verified" value={String(substackManualPublicationUrlAuditImportPacket.url_network_verified)} mono />
          <Row label="Operator supplied" value={String(substackManualPublicationUrlAuditImportPacket.manual_publication_claim_operator_supplied)} mono />
        </div>
        <div className="mt-3 rounded-lg border border-status-blocked/30 bg-status-blocked/5 p-3 font-mono text-[11px] text-status-blocked">
          blocked controls: {substackManualPublicationUrlAuditImportPacket.blocked_controls.join(', ')} ? enabled={String(substackManualPublicationUrlAuditImportPacket.enabled_publish_send_dispatch_approve_controls)} ? no URL fetch/scrape
        </div>
      </Panel>


      <Panel
        title="Substack publication audit review pending metrics confirmation"
        subtitle={substackPublicationAuditReviewMetricsSummaryPacket.publication_audit_review_packet_id}
        actions={<StatusChip status="review">{substackPublicationAuditReviewMetricsSummaryPacket.operator_review_status}</StatusChip>}
      >
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          <Row label="Audit review status" value={substackPublicationAuditReviewMetricsSummaryPacket.publication_audit_status} />
          <Row label="Metrics status" value={substackPublicationAuditReviewMetricsSummaryPacket.metrics_summary_status} />
          <Row label="Metrics source" value={substackPublicationAuditReviewMetricsSummaryPacket.metrics_source} />
        </div>
        <div className="mt-3 rounded-lg border border-status-blocked/30 bg-status-blocked/5 p-3 font-mono text-[11px] text-status-blocked">
          blocked controls: {substackPublicationAuditReviewMetricsSummaryPacket.blocked_controls.join(', ')} ? enabled={String(substackPublicationAuditReviewMetricsSummaryPacket.enabled_publish_send_dispatch_approve_controls)} ? no metrics API or URL fetch
        </div>
      </Panel>

      <Panel
        title="LinkedIn manual publication evidence pending review"
        subtitle={linkedinManualApprovalExportEvidencePacket.approval_export_evidence_packet_id}
        actions={<StatusChip status="review">{linkedinManualOperatorHandoffPacket.operator_handoff_status}</StatusChip>}
      >
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          <Row label="Approval" value={linkedinManualApprovalExportEvidencePacket.approval_status} />
          <Row label="Manual export" value={linkedinManualApprovalExportEvidencePacket.manual_export_status} />
          <Row label="LinkedIn API" value={String(linkedinManualApprovalExportEvidencePacket.linkedin_api_used)} mono />
          <Row label="URL verified" value={String(linkedinManualPublicationUrlAuditImportPacket.url_network_verified)} mono />
          <Row label="Metrics verified" value={String(linkedinPublicationAuditReviewMetricsSummaryPacket.metrics_network_verified)} mono />
          <Row label="Controls enabled" value={String(linkedinManualOperatorHandoffPacket.enabled_publish_send_dispatch_approve_controls)} mono />
        </div>
        <div className="mt-3 rounded-lg border border-status-blocked/30 bg-status-blocked/5 p-3 font-mono text-[11px] text-status-blocked">
          blocked controls: {linkedinManualOperatorHandoffPacket.blocked_controls.join(', ')} · no LinkedIn API/browser automation/URL fetch/scrape/post/reaction/comment/DM/scheduler
        </div>
      </Panel>

      <Panel
        title="X manual publication evidence pending review"
        subtitle={xManualApprovalExportEvidencePacket.approval_export_evidence_packet_id}
        actions={<StatusChip status="review">{xManualOperatorHandoffPacket.operator_handoff_status}</StatusChip>}
      >
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          <Row label="Approval" value={xManualApprovalExportEvidencePacket.approval_status} />
          <Row label="Manual export" value={xManualApprovalExportEvidencePacket.manual_export_status} />
          <Row label="X API" value={String(xManualApprovalExportEvidencePacket.x_api_used)} mono />
          <Row label="URL verified" value={String(xManualPublicationUrlAuditImportPacket.url_network_verified)} mono />
          <Row label="Metrics verified" value={String(xPublicationAuditReviewMetricsSummaryPacket.metrics_network_verified)} mono />
          <Row label="Controls enabled" value={String(xManualOperatorHandoffPacket.enabled_publish_send_dispatch_approve_controls)} mono />
        </div>
        <div className="mt-3 rounded-lg border border-status-blocked/30 bg-status-blocked/5 p-3 font-mono text-[11px] text-status-blocked">
          blocked controls: {xManualOperatorHandoffPacket.blocked_controls.join(', ')} ? no X API/browser automation/URL fetch/scrape/post/reply/DM/like/repost/quote/scheduler
        </div>
      </Panel>
      <Panel
        title="V6 operator approval queue · fixture-only"
        subtitle={`${v6Packet.approval_queue_items.length} pending previews · ${v6Packet.sample_scope}`}
        actions={<StatusChip status="review">sample_fixture_only</StatusChip>}
      >
        <div className="mb-3 rounded-lg border border-status-blocked/30 bg-status-blocked/5 p-3 text-xs leading-relaxed text-fg-muted">
          Committed sample packet only. Runtime proof is false; live send, dispatch,
          provider calls, network, browser session use, raw secret serialization,
          and env line serialization are all disabled/false.
        </div>
        <ul className="space-y-2">
          {v6Packet.approval_queue_items.map((item) => (
            <li key={item.queue_item_id} className="rounded-lg border border-line bg-surface-2 p-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="min-w-0">
                  <div className="font-mono text-[11px] font-bold uppercase tracking-wide text-fg-subtle">
                    {item.platform}
                  </div>
                  <div className="mt-1 truncate text-sm font-semibold text-fg">
                    {item.preview_id}
                  </div>
                </div>
                <StatusChip status="review">{item.approval_status}</StatusChip>
              </div>
              <div className="mt-2 break-all font-mono text-[11px] text-fg-muted">
                preview_hash: {item.preview_hash}
              </div>
              <p className="mt-2 text-xs leading-relaxed text-fg-muted">
                {item.required_operator_action}
              </p>
              <StatusChip status="blocked">live blocked</StatusChip>
            </li>
          ))}
        </ul>
      </Panel>
    </div>
  );
}

function Row({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-3">
      <dt className="font-mono text-[10.5px] uppercase tracking-wide text-fg-subtle">
        {label}
      </dt>
      <dd
        className={`truncate text-sm text-fg ${
          mono ? 'font-mono text-[12px]' : ''
        }`}
      >
        {value}
      </dd>
    </div>
  );
}
