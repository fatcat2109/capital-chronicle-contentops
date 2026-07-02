// Capital Chronicle ContentOps V5 â€” Evidence Vault view.
// Forensic / compliance mode. Always rendered in dark-evidence theme (App
// forces it). Read-only audit surface. No network, storage, or credentials.

import { SubstackArticleStudioCard } from './SubstackArticleStudioCard';
import {
  substackManualApprovalExportEvidencePacket,
  substackManualExportOperatorHandoffPacket,
  substackManualPublicationUrlAuditImportPacket,
  substackPublicationAuditReviewMetricsSummaryPacket,
  linkedinManualExportPacket,
  linkedinManualApprovalExportEvidencePacket,
  linkedinManualOperatorHandoffPacket,
  linkedinManualPublicationUrlAuditImportPacket,
  linkedinPublicationAuditReviewMetricsSummaryPacket,
  xManualExportPacket,
  xManualApprovalExportEvidencePacket,
  xManualOperatorHandoffPacket,
  xManualPublicationUrlAuditImportPacket,
  xPublicationAuditReviewMetricsSummaryPacket,
} from '../data/substackManualExportArticleStudioAdapter';
import { ManualDistributionRegistryPanel } from './ManualDistributionRegistryPanel';
import { operatorSuppliedFeedbackIntakePacket, operatorFeedbackBacklogSummaryPacket } from '../data/operatorFeedbackBacklogAdapter';
import { feedbackBacklogNextArticleBriefPacket } from '../data/feedbackBacklogNextArticleBriefAdapter';
import { nextArticleBriefSourcePackReviewPacket } from '../data/nextArticleBriefSourcePackReviewAdapter';
import { nextArticleSourcePackIntakeValidationPacket } from '../data/nextArticleSourcePackIntakeValidationAdapter';
import { nextArticleDraftAuthorizationReadinessPacket } from '../data/nextArticleDraftAuthorizationReadinessAdapter';
import { localCanonicalDraftPreviewReviewPacket } from '../data/localCanonicalDraftPreviewReviewAdapter';
import { canonicalDraftFinalReviewVariantPreviewPacket } from '../data/canonicalDraftFinalReviewVariantPreviewAdapter';
import { platformVariantApprovalPacketPreviewPacket } from '../data/platformVariantApprovalPacketPreviewAdapter';
import { dispatchOutboxDryRunPacket } from '../data/dispatchOutboxDryRunAdapter';
import { dispatchOutboxOperatorRecoveryPacket } from '../data/dispatchOutboxOperatorRecoveryAdapter';
import { explicitLiveScopeGatePacket } from '../data/explicitLiveScopeGateSourceCandidateAdapter';
import { discordSupervisedLivePreflightPacket, requestEnvelopePreview } from '../data/discordSupervisedLivePreflightAdapter';
import { useState } from 'react';
import { useApp } from '../state';
import { viewModel } from '../fixtures';
import {
  selectValidation,
  selectManualPilotTrailReconciliationAuditPacket,
  selectAuditInvariant,
  selectAuditContradiction,
} from '../selectors';
import { IconClock, IconFingerprint, IconBlock } from '../ui/icons';
import {
  EvidenceChip,
  Panel,
  SectionLabel,
  StatusChip,
  StatusDot,
  LockedAction,
} from '../ui/primitives';
import { manualPilotTrailReconciliationAuditPacket as auditPacket } from '../data/manualPilotTrailReconciliationAuditPacket';

type VaultTab = 'validation' | 'manual_pilot_audit';

export function EvidenceVault() {
  const { select, selected } = useApp();
  const [activeTab, setActiveTab] = useState<VaultTab>('validation');
  const packet = viewModel.evidence_packets[0];
  const v6Packet = viewModel.v6_operator_approval_evidence;

  const handleTabChange = (tab: VaultTab) => {
    setActiveTab(tab);
    if (tab === 'validation') {
      select(selectValidation(packet.validation_matrix[0], packet.id));
    } else {
      select(selectManualPilotTrailReconciliationAuditPacket(auditPacket));
    }
  };

  return (
    <div className="space-y-6">

      <ManualDistributionRegistryPanel />

      <Panel
        title="Operator feedback intake and backlog evidence"
        subtitle={`${operatorSuppliedFeedbackIntakePacket.feedback_intake_packet_id} · ${operatorFeedbackBacklogSummaryPacket.backlog_summary_packet_id}`}
        actions={<StatusChip status="review">manual-only</StatusChip>}
      >
        <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
          {operatorSuppliedFeedbackIntakePacket.feedback_items.map((item) => (
            <article key={item.feedback_item_id} className="rounded-lg border border-line bg-surface-2 p-3">
              <div className="font-mono text-[11px] uppercase tracking-wide text-fg-subtle">{item.source_platform} · {item.source_kind}</div>
              <h3 className="mt-1 break-all text-sm font-semibold text-fg">{item.feedback_item_id}</h3>
              <p className="mt-2 text-xs leading-relaxed text-fg-muted">{item.operator_supplied_text}</p>
              <div className="mt-2 break-all font-mono text-[11px] text-fg-muted">url_hash={item.source_url_hash_optional || 'none'} · verified={String(item.source_url_network_verified)}</div>
            </article>
          ))}
        </div>
        <div className="mt-4 rounded-lg border border-status-blocked/30 bg-status-blocked/5 p-3 text-xs leading-relaxed text-fg-muted">
          Backlog summary: {operatorFeedbackBacklogSummaryPacket.summary_method} · candidates={operatorFeedbackBacklogSummaryPacket.candidate_count} · llm_provider_call_made={String(operatorFeedbackBacklogSummaryPacket.llm_provider_call_made)} · platform_api_used={String(operatorFeedbackBacklogSummaryPacket.platform_api_used)} · public_url_fetch_made={String(operatorFeedbackBacklogSummaryPacket.public_url_fetch_made)}
        </div>
        <div className="mt-4 rounded-lg border border-line bg-surface-2 p-3">
          <div className="font-mono text-[11px] uppercase tracking-wide text-fg-subtle">Next article brief candidate packet</div>
          <h3 className="mt-1 break-all text-sm font-semibold text-fg">{feedbackBacklogNextArticleBriefPacket.next_article_brief_packet_id}</h3>
          <p className="mt-2 text-xs leading-relaxed text-fg-muted">{feedbackBacklogNextArticleBriefPacket.brief_candidate.brief_title} · {feedbackBacklogNextArticleBriefPacket.selection_method}</p>
          <div className="mt-2 break-all font-mono text-[11px] text-fg-muted">source_backlog_hash={feedbackBacklogNextArticleBriefPacket.source_backlog_summary_hash} · canonical_draft_created={String(feedbackBacklogNextArticleBriefPacket.canonical_draft_created)} · public_url_fetch_made={String(feedbackBacklogNextArticleBriefPacket.public_url_fetch_made)}</div>
        </div>
        <div className="mt-4 rounded-lg border border-line bg-surface-2 p-3">
          <div className="font-mono text-[11px] uppercase tracking-wide text-fg-subtle">Next article brief source-pack and review packet</div>
          <h3 className="mt-1 break-all text-sm font-semibold text-fg">{nextArticleBriefSourcePackReviewPacket.source_pack_review_packet_id}</h3>
          <p className="mt-2 text-xs leading-relaxed text-fg-muted">{nextArticleBriefSourcePackReviewPacket.source_pack_status} · {nextArticleBriefSourcePackReviewPacket.operator_review_status}</p>
          <div className="mt-2 space-y-1">
            {nextArticleBriefSourcePackReviewPacket.source_pack_checklist.map((item) => (
              <div key={item.check_id} className="flex items-center justify-between gap-2 rounded border border-line bg-surface-1 px-2.5 py-1.5 text-xs">
                <span className="font-medium text-fg">{item.label}</span>
                <StatusChip status="review">{item.status}</StatusChip>
              </div>
            ))}
          </div>
          <div className="mt-2 text-xs leading-relaxed text-fg-muted bg-status-blocked/5 p-2 rounded-lg border border-status-blocked/30">
            Source pack status is source_pack_required_pending_operator_collection. Operator review status is pending_operator_review.
            Drafting and dispatch gates remain locked: ready_for_llm_drafting=false · ready_for_canonical_draft=false · ready_for_auto_publish=false · ready_for_dispatch=false.
            No LLM/provider call is allowed on this local-first review workflow.
          </div>
        </div>
        <div className="mt-4 rounded-lg border border-line bg-surface-2 p-3">
          <div className="font-mono text-[11px] uppercase tracking-wide text-fg-subtle">Next article source-pack intake and validation packet</div>
          <h3 className="mt-1 break-all text-sm font-semibold text-fg">{nextArticleSourcePackIntakeValidationPacket.source_pack_intake_packet_id}</h3>
          <p className="mt-2 text-xs leading-relaxed text-fg-muted">coverage: {nextArticleSourcePackIntakeValidationPacket.checklist_coverage_status} · entries: {nextArticleSourcePackIntakeValidationPacket.source_entry_count}</p>
          <div className="mt-2 space-y-1">
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
          <div className="mt-2 text-xs leading-relaxed text-fg-muted bg-status-blocked/5 p-2 rounded-lg border border-status-blocked/30">
            Intake status: operator_source_pack_supplied_for_review. Validation status: local_metadata_validation_pending_operator_review.
            Checklist coverage: source_pack_collection_status={nextArticleSourcePackIntakeValidationPacket.source_pack_collection_status}.
            Verified URLs: network_verified_url_count=0. Verified sources: api_verified_source_count=0.
            Drafting status: ready_for_llm_drafting=false · ready_for_canonical_draft=false · ready_for_auto_publish=false · ready_for_dispatch=false.
            No LLM/provider call is allowed on this local-first review workflow.
          </div>
        </div>
        <div className="mt-4 rounded-lg border border-line bg-surface-2 p-3">
          <div className="font-mono text-[11px] uppercase tracking-wide text-fg-subtle">Next article draft authorization and readiness packet</div>
          <h3 className="mt-1 break-all text-sm font-semibold text-fg">{nextArticleDraftAuthorizationReadinessPacket.draft_authorization_packet_id}</h3>
          <p className="mt-2 text-xs leading-relaxed text-fg-muted">readiness: {nextArticleDraftAuthorizationReadinessPacket.local_draft_readiness_status} · entries: {nextArticleDraftAuthorizationReadinessPacket.source_entry_count}</p>
          <div className="mt-2 text-xs leading-relaxed text-fg-muted bg-status-blocked/5 p-2 rounded-lg border border-status-blocked/30 space-y-1.5">
            <div><span className="font-semibold text-fg">authorization_record_status:</span> {nextArticleDraftAuthorizationReadinessPacket.authorization_record_status}</div>
            <div><span className="font-semibold text-fg">authorization_scope:</span> {nextArticleDraftAuthorizationReadinessPacket.authorization_scope}</div>
            <div><span className="font-semibold text-fg">local_draft_readiness_status:</span> {nextArticleDraftAuthorizationReadinessPacket.local_draft_readiness_status}</div>
            <div><span className="font-semibold text-fg">ready_for_local_canonical_draft_workflow:</span> {String(nextArticleDraftAuthorizationReadinessPacket.ready_for_local_canonical_draft_workflow)}</div>
            <div><span className="font-semibold text-fg">ready_for_llm_drafting:</span> {String(nextArticleDraftAuthorizationReadinessPacket.ready_for_llm_drafting)}</div>
            <div><span className="font-semibold text-fg">ready_for_provider_drafting:</span> {String(nextArticleDraftAuthorizationReadinessPacket.ready_for_provider_drafting)}</div>
            <div><span className="font-semibold text-fg">canonical_draft_created:</span> {String(nextArticleDraftAuthorizationReadinessPacket.canonical_draft_created)}</div>
            <div><span className="font-semibold text-fg">article_body_created:</span> {String(nextArticleDraftAuthorizationReadinessPacket.article_body_created)}</div>
            <div><span className="font-semibold text-fg">ready_for_auto_publish:</span> {String(nextArticleDraftAuthorizationReadinessPacket.ready_for_auto_publish)}</div>
            <div><span className="font-semibold text-fg">ready_for_dispatch:</span> {String(nextArticleDraftAuthorizationReadinessPacket.ready_for_dispatch)}</div>
          </div>
          <div className="mt-2 text-xs leading-relaxed text-fg-muted bg-status-blocked/5 p-2 rounded-lg border border-status-blocked/30">
            Authorization record status is operator_drafting_authorization_recorded. Scope is local_canonical_draft_preparation_only.
            Local draft readiness status: ready_for_local_canonical_draft_workflow=true.
            Drafting/publishing gates remain locked: ready_for_llm_drafting=false · ready_for_provider_drafting=false · canonical_draft_created=false · article_body_created=false · ready_for_auto_publish=false · ready_for_dispatch=false.
            No LLM/provider call is allowed on this local-first review workflow.
          </div>
        </div>
        <div className="mt-4 rounded-lg border border-line bg-surface-2 p-3">
          <div className="font-mono text-[11px] uppercase tracking-wide text-fg-subtle">Local canonical draft preview and review packet</div>
          <h3 className="mt-1 break-all text-sm font-semibold text-fg">{localCanonicalDraftPreviewReviewPacket.local_draft_preview_packet_id}</h3>
          <p className="mt-2 text-xs leading-relaxed text-fg-muted">status: {localCanonicalDraftPreviewReviewPacket.draft_preview_status} · review: {localCanonicalDraftPreviewReviewPacket.draft_review_status}</p>
          <div className="mt-2 text-xs leading-relaxed text-fg-muted bg-status-blocked/5 p-2 rounded-lg border border-status-blocked/30 space-y-1.5 font-mono">
            <div><span className="font-semibold text-fg">local_draft_preview_packet_id:</span> {localCanonicalDraftPreviewReviewPacket.local_draft_preview_packet_id}</div>
            <div><span className="font-semibold text-fg">draft_review_packet_id:</span> {localCanonicalDraftPreviewReviewPacket.draft_review_packet_id}</div>
            <div><span className="font-semibold text-fg">draft_preview_status:</span> {localCanonicalDraftPreviewReviewPacket.draft_preview_status}</div>
            <div><span className="font-semibold text-fg">draft_review_status:</span> {localCanonicalDraftPreviewReviewPacket.draft_review_status}</div>
            <div><span className="font-semibold text-fg">draft_generation_method:</span> {localCanonicalDraftPreviewReviewPacket.draft_generation_method}</div>
            <div><span className="font-semibold text-fg">canonical_draft_created:</span> {String(localCanonicalDraftPreviewReviewPacket.canonical_draft_created)}</div>
            <div><span className="font-semibold text-fg">article_body_created:</span> {String(localCanonicalDraftPreviewReviewPacket.article_body_created)}</div>
            <div><span className="font-semibold text-fg">final_article_approved:</span> {String(localCanonicalDraftPreviewReviewPacket.final_article_approved)}</div>
            <div><span className="font-semibold text-fg">ready_for_llm_drafting:</span> {String(localCanonicalDraftPreviewReviewPacket.ready_for_llm_drafting)}</div>
            <div><span className="font-semibold text-fg">ready_for_provider_drafting:</span> {String(localCanonicalDraftPreviewReviewPacket.ready_for_provider_drafting)}</div>
            <div><span className="font-semibold text-fg">ready_for_auto_publish:</span> {String(localCanonicalDraftPreviewReviewPacket.ready_for_auto_publish)}</div>
            <div><span className="font-semibold text-fg">ready_for_dispatch:</span> {String(localCanonicalDraftPreviewReviewPacket.ready_for_dispatch)}</div>
            <div><span className="font-semibold text-fg">public_url_verification_performed:</span> {String(localCanonicalDraftPreviewReviewPacket.public_url_verification_performed)}</div>
          </div>
          <div className="mt-2 text-xs leading-relaxed text-fg-muted bg-status-blocked/5 p-2 rounded-lg border border-status-blocked/30">
            Draft preview status is local_draft_preview_created_for_review. Review status is pending_operator_review.
            Draft generation method: deterministic_template_no_llm.
            Gates: canonical_draft_created=true · article_body_created=true · final_article_approved=false.
            Readiness locks: separate_final_approval_task_required=true · separate_platform_variant_task_required=true · separate_publish_authorization_required=true · public_url_verification_performed=false.
            Drafting/publishing gates remain locked: ready_for_llm_drafting=false · ready_for_provider_drafting=false · ready_for_auto_publish=false · ready_for_dispatch=false.
            No LLM/provider call is allowed on this local-first review workflow.
          </div>
        </div>
        <div className="mt-4 rounded-lg border border-line bg-surface-2 p-3">
          <div className="font-mono text-[11px] uppercase tracking-wide text-fg-subtle">V6 canonical draft final review and platform variant preview</div>
          <h3 className="mt-1 break-all text-sm font-semibold text-fg">{canonicalDraftFinalReviewVariantPreviewPacket.canonical_draft_final_review_to_platform_variant_preview_packet_id}</h3>
          <p className="mt-2 text-xs leading-relaxed text-fg-muted">status: {canonicalDraftFinalReviewVariantPreviewPacket.canonical_draft_final_review_status} · variant status: {canonicalDraftFinalReviewVariantPreviewPacket.platform_variant_preview_status}</p>
          <div className="mt-2 text-xs leading-relaxed text-fg-muted bg-status-blocked/5 p-2 rounded-lg border border-status-blocked/30 space-y-1.5 font-mono">
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
          <div className="mt-2 border-t border-line pt-2">
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
          <div className="mt-2 text-xs leading-relaxed text-fg-muted bg-status-blocked/5 p-2 rounded-lg border border-status-blocked/30">
            Platform variant preview status is platform_variant_preview_created_for_operator_review.
            Draft final review status is ready_for_operator_final_review.
            Approval record and outbox entries remain uncreated.
            Readiness locks: final_article_approved=false · platform_payloads_approved=false.
            Drafting/publishing gates remain locked: ready_for_auto_publish=false · ready_for_dispatch=false.
            No LLM/provider call is allowed on this local-first review workflow.
          </div>
        </div>
        <div className="mt-4 rounded-lg border border-line bg-surface-2 p-3">
          <div className="font-mono text-[11px] uppercase tracking-wide text-fg-subtle">V6 platform variant approval packet preview</div>
          <h3 className="mt-1 break-all text-sm font-semibold text-fg">{platformVariantApprovalPacketPreviewPacket.platform_variant_final_review_to_approval_packet_preview_packet_id}</h3>
          <p className="mt-2 text-xs leading-relaxed text-fg-muted">status: {platformVariantApprovalPacketPreviewPacket.platform_variant_final_review_status} · variant status: {platformVariantApprovalPacketPreviewPacket.approval_packet_preview_status}</p>
          <div className="mt-2 text-xs leading-relaxed text-fg-muted bg-status-blocked/5 p-2 rounded-lg border border-status-blocked/30 space-y-1.5 font-mono">
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
          <div className="mt-2 border-t border-line pt-2">
            <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle mb-1 font-mono">Committed Preview Targets (10)</div>
            <div className="space-y-2">
              {Object.entries(platformVariantApprovalPacketPreviewPacket.approval_targets).slice(0, 4).map(([key, target]) => (
                <div key={key} className="p-2 border border-line bg-surface-1 rounded text-xs">
                  <div className="font-semibold text-accent uppercase text-[10px]">{target.platform_id}</div>
                  <div className="text-fg-muted text-[11px] leading-snug mt-0.5 italic">"{target.exact_preview_text.slice(0, 60)}..."</div>
                  <div className="mt-1 font-mono text-[10px] text-fg-subtle">
                    hash: {target.payload_hash.slice(0, 16)}...
                  </div>
                </div>
              ))}
              <div className="text-[10px] text-fg-subtle italic">Showing first 4 of 10 targets. Go to Platform Preview to view all.</div>
            </div>
          </div>
          <div className="mt-2 text-xs leading-relaxed text-fg-muted bg-status-blocked/5 p-2 rounded-lg border border-status-blocked/30 font-mono">
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

        <div className="mt-4 rounded-lg border border-line bg-surface-2 p-3 font-mono">
          <div className="font-mono text-[11px] uppercase tracking-wide text-fg-subtle">V6 dispatch outbox dry-run preview</div>
          <h3 className="mt-1 break-all text-sm font-semibold text-fg">{dispatchOutboxDryRunPacket.task_label}</h3>
          <p className="mt-2 text-xs leading-relaxed text-fg-muted">status: {dispatchOutboxDryRunPacket.dispatch_outbox_dry_run_status}</p>
          <div className="mt-2 text-xs leading-relaxed text-fg-muted bg-status-blocked/5 p-2 rounded-lg border border-status-blocked/30 space-y-1.5 font-mono">
            <div><span className="font-semibold text-fg">dispatch_outbox_dry_run_status:</span> {dispatchOutboxDryRunPacket.dispatch_outbox_dry_run_status}</div>
            <div><span className="font-semibold text-fg">dry_run_outbox_package_created:</span> {String(dispatchOutboxDryRunPacket.dry_run_outbox_package_created)}</div>
            <div><span className="font-semibold text-fg">dry_run_entries_created:</span> {String(dispatchOutboxDryRunPacket.dry_run_entries_created)}</div>
            <div><span className="font-semibold text-fg">executable_outbox_entry_created:</span> {String(dispatchOutboxDryRunPacket.executable_outbox_entry_created)}</div>
            <div><span className="font-semibold text-fg">real_outbox_entry_created:</span> {String(dispatchOutboxDryRunPacket.real_outbox_entry_created)}</div>
            <div><span className="font-semibold text-fg">dispatch_outbox_ready:</span> {String(dispatchOutboxDryRunPacket.dispatch_outbox_ready)}</div>
            <div><span className="font-semibold text-fg">dispatch_attempted:</span> {String(dispatchOutboxDryRunPacket.dispatch_attempted)}</div>
            <div><span className="font-semibold text-fg">dispatch_request_count:</span> {dispatchOutboxDryRunPacket.dispatch_request_count}</div>
            <div><span className="font-semibold text-fg">webhook_request_count:</span> {dispatchOutboxDryRunPacket.webhook_request_count}</div>
            <div><span className="font-semibold text-fg">platform_api_request_count:</span> {dispatchOutboxDryRunPacket.platform_api_request_count}</div>
            <div><span className="font-semibold text-fg">kill_switch_active:</span> {String(dispatchOutboxDryRunPacket.kill_switch_active)}</div>
            <div><span className="font-semibold text-fg">ready_for_dispatch:</span> {String(dispatchOutboxDryRunPacket.ready_for_dispatch)}</div>
          </div>
          <div className="mt-2 border-t border-line pt-2">
            <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle mb-1 font-mono">Dry-Run Outbox Entries (10)</div>
            <div className="space-y-2">
              {Object.entries(dispatchOutboxDryRunPacket.dry_run_entries).slice(0, 4).map(([key, entry]) => (
                <div key={key} className="p-2 border border-line bg-surface-1 rounded text-xs">
                  <div className="font-semibold text-accent uppercase text-[10px]">{entry.platform_id}</div>
                  <div className="text-fg-muted text-[11px] leading-snug mt-0.5 italic">"{entry.dry_run_payload_text.slice(0, 60)}..."</div>
                  <div className="mt-1 font-mono text-[10px] text-fg-subtle">
                    hash: {entry.dry_run_payload_hash.slice(0, 16)}...
                  </div>
                </div>
              ))}
              <div className="text-[10px] text-fg-subtle italic">Showing first 4 of 10 targets. Go to Platform Preview to view all.</div>
            </div>
          </div>
          <div className="mt-2 text-xs leading-relaxed text-fg-muted bg-status-blocked/5 p-2 rounded-lg border border-status-blocked/30 font-mono font-mono">
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

        <div className="mt-4 rounded-lg border border-line bg-surface-2 p-3 font-mono">
          <div className="font-mono text-[11px] uppercase tracking-wide text-fg-subtle">V6 dispatch outbox operator runbook & recovery</div>
          <h3 className="mt-1 break-all text-sm font-semibold text-fg">{dispatchOutboxOperatorRecoveryPacket.task_label}</h3>
          <p className="mt-2 text-xs leading-relaxed text-fg-muted font-mono">status: {dispatchOutboxOperatorRecoveryPacket.operator_recovery_status}</p>
          <div className="mt-2 text-xs leading-relaxed text-fg-muted bg-status-blocked/5 p-2 rounded-lg border border-status-blocked/30 space-y-1.5 font-mono">
            <div><span className="font-semibold text-fg font-mono">operator_recovery_status:</span> {dispatchOutboxOperatorRecoveryPacket.operator_recovery_status}</div>
            <div><span className="font-semibold text-fg font-mono">recovery_runbook_created:</span> {String(dispatchOutboxOperatorRecoveryPacket.recovery_runbook_created)}</div>
            <div><span className="font-semibold text-fg font-mono">manual_fallback_plan_created:</span> {String(dispatchOutboxOperatorRecoveryPacket.manual_fallback_plan_created)}</div>
            <div><span className="font-semibold text-fg font-mono">rollback_plan_created:</span> {String(dispatchOutboxOperatorRecoveryPacket.rollback_plan_created)}</div>
            <div><span className="font-semibold text-fg font-mono">dry_run_replay_plan_created:</span> {String(dispatchOutboxOperatorRecoveryPacket.dry_run_replay_plan_created)}</div>
            <div><span className="font-semibold text-fg font-mono">failure_mode_matrix_created:</span> {String(dispatchOutboxOperatorRecoveryPacket.failure_mode_matrix_created)}</div>
            <div><span className="font-semibold text-fg font-mono">evidence_collection_checklist_created:</span> {String(dispatchOutboxOperatorRecoveryPacket.evidence_collection_checklist_created)}</div>
            <div><span className="font-semibold text-fg font-mono">dispatch_preflight_checklist_created:</span> {String(dispatchOutboxOperatorRecoveryPacket.dispatch_preflight_checklist_created)}</div>
            <div><span className="font-semibold text-fg font-mono">executable_outbox_entry_created:</span> {String(dispatchOutboxOperatorRecoveryPacket.executable_outbox_entry_created)}</div>
            <div><span className="font-semibold text-fg font-mono">real_outbox_entry_created:</span> {String(dispatchOutboxOperatorRecoveryPacket.real_outbox_entry_created)}</div>
            <div><span className="font-semibold text-fg font-mono">dispatch_outbox_ready:</span> {String(dispatchOutboxOperatorRecoveryPacket.dispatch_outbox_ready)}</div>
            <div><span className="font-semibold text-fg font-mono">dispatch_attempted:</span> {String(dispatchOutboxOperatorRecoveryPacket.dispatch_attempted)}</div>
            <div><span className="font-semibold text-fg font-mono">dispatch_request_count:</span> {dispatchOutboxOperatorRecoveryPacket.dispatch_request_count}</div>
            <div><span className="font-semibold text-fg font-mono">kill_switch_active:</span> {String(dispatchOutboxOperatorRecoveryPacket.kill_switch_active)}</div>
            <div><span className="font-semibold text-fg font-mono">ready_for_dispatch:</span> {String(dispatchOutboxOperatorRecoveryPacket.ready_for_dispatch)}</div>
            <div><span className="font-semibold text-fg font-mono">blocked_until_explicit_live_scope:</span> {String(dispatchOutboxOperatorRecoveryPacket.blocked_until_explicit_live_scope)}</div>
          </div>
          <div className="mt-2 text-xs leading-relaxed text-fg-muted bg-status-blocked/5 p-2 rounded-lg border border-status-blocked/30 font-mono font-mono font-mono">
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

        <div className="mt-4 rounded-lg border border-line bg-surface-2 p-3 font-mono">
          <div className="font-mono text-[11px] uppercase tracking-wide text-fg-subtle">V6 explicit live scope gate & source candidate</div>
          <h3 className="mt-1 break-all text-sm font-semibold text-fg">{explicitLiveScopeGatePacket.task_label}</h3>
          <p className="mt-2 text-xs leading-relaxed text-fg-muted font-mono">status: {explicitLiveScopeGatePacket.explicit_live_scope_gate_status}</p>
          <div className="mt-2 text-xs leading-relaxed text-fg-muted bg-status-blocked/5 p-2 rounded-lg border border-status-blocked/30 space-y-1.5 font-mono">
            <div><span className="font-semibold text-fg font-mono">explicit_live_scope_gate_status:</span> {explicitLiveScopeGatePacket.explicit_live_scope_gate_status}</div>
            <div><span className="font-semibold text-fg font-mono">source_intake_parser_created:</span> {String(explicitLiveScopeGatePacket.source_intake_parser_created)}</div>
            <div><span className="font-semibold text-fg font-mono">normalized_dispatch_candidate_created:</span> {String(explicitLiveScopeGatePacket.normalized_dispatch_candidate_created)}</div>
            <div><span className="font-semibold text-fg font-mono">normalized_candidate_status:</span> {explicitLiveScopeGatePacket.normalized_candidate_status}</div>
            <div><span className="font-semibold text-fg font-mono">discord_live_scope_candidate_created:</span> {String(explicitLiveScopeGatePacket.discord_live_scope_candidate_created)}</div>
            <div><span className="font-semibold text-fg font-mono">official_docs_evidence_created:</span> {String(explicitLiveScopeGatePacket.official_docs_evidence_created)}</div>
            <div><span className="font-semibold text-fg font-mono">endpoint_allowlist_created:</span> {String(explicitLiveScopeGatePacket.endpoint_allowlist_created)}</div>
            <div><span className="font-semibold text-fg font-mono">credential_presence_check_performed:</span> {String(explicitLiveScopeGatePacket.credential_presence_check_performed)}</div>
            <div><span className="font-semibold text-fg font-mono">credential_value_read_made:</span> {String(explicitLiveScopeGatePacket.credential_value_read_made)}</div>
            <div><span className="font-semibold text-fg font-mono">env_value_read_made:</span> {String(explicitLiveScopeGatePacket.env_value_read_made)}</div>
            <div><span className="font-semibold text-fg font-mono">credential_presence_key_names_only:</span> {String(explicitLiveScopeGatePacket.credential_presence_key_names_only)}</div>
            <div><span className="font-semibold text-fg font-mono">destination_binding_status:</span> {explicitLiveScopeGatePacket.destination_binding_status}</div>
            <div><span className="font-semibold text-fg font-mono">payload_hash_preview_created:</span> {String(explicitLiveScopeGatePacket.payload_hash_preview_created)}</div>
            <div><span className="font-semibold text-fg font-mono">exact_payload_preview_created:</span> {String(explicitLiveScopeGatePacket.exact_payload_preview_created)}</div>
            <div><span className="font-semibold text-fg font-mono">executable_outbox_entry_created:</span> {String(explicitLiveScopeGatePacket.executable_outbox_entry_created)}</div>
            <div><span className="font-semibold text-fg font-mono">real_outbox_entry_created:</span> {String(explicitLiveScopeGatePacket.real_outbox_entry_created)}</div>
            <div><span className="font-semibold text-fg font-mono">approval_ledger_entry_created:</span> {String(explicitLiveScopeGatePacket.approval_ledger_entry_created)}</div>
            <div><span className="font-semibold text-fg font-mono">dispatch_outbox_ready:</span> {String(explicitLiveScopeGatePacket.dispatch_outbox_ready)}</div>
            <div><span className="font-semibold text-fg font-mono">dispatch_attempted:</span> {String(explicitLiveScopeGatePacket.dispatch_attempted)}</div>
            <div><span className="font-semibold text-fg font-mono">dispatch_request_count:</span> {explicitLiveScopeGatePacket.dispatch_request_count}</div>
            <div><span className="font-semibold text-fg font-mono">kill_switch_active:</span> {String(explicitLiveScopeGatePacket.kill_switch_active)}</div>
            <div><span className="font-semibold text-fg font-mono">ready_for_dispatch:</span> {String(explicitLiveScopeGatePacket.ready_for_dispatch)}</div>
          </div>
          <div className="mt-2 text-xs leading-relaxed text-fg-muted bg-status-blocked/5 p-2 rounded-lg border border-status-blocked/30 font-mono font-mono font-mono">
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

        <div className="mt-4 rounded-lg border border-line bg-surface-2 p-3 font-mono">
          <div className="font-mono text-[11px] uppercase tracking-wide text-fg-subtle">V6 Discord supervised live preflight</div>
          <h3 className="mt-1 break-all text-sm font-semibold text-fg">{discordSupervisedLivePreflightPacket.task_label}</h3>
          <p className="mt-2 text-xs leading-relaxed text-fg-muted font-mono">status: {discordSupervisedLivePreflightPacket.supervised_live_preflight_status}</p>
          <div className="mt-2 text-xs leading-relaxed text-fg-muted bg-status-blocked/5 p-2 rounded-lg border border-status-blocked/30 space-y-1.5 font-mono">
            <div><span className="font-semibold text-fg font-mono">supervised_live_preflight_status:</span> {discordSupervisedLivePreflightPacket.supervised_live_preflight_status}</div>
            <div><span className="font-semibold text-fg font-mono">source_candidate_status:</span> {discordSupervisedLivePreflightPacket.source_candidate_status}</div>
            <div><span className="font-semibold text-fg font-mono">normalized_discord_payload_candidate_created:</span> {String(discordSupervisedLivePreflightPacket.normalized_discord_payload_candidate_created)}</div>
            <div><span className="font-semibold text-fg font-mono">request_envelope_preview_created:</span> {String(discordSupervisedLivePreflightPacket.request_envelope_preview_created)}</div>
            <div><span className="font-semibold text-fg font-mono">request_envelope_executable:</span> {String(discordSupervisedLivePreflightPacket.request_envelope_executable)}</div>
            <div><span className="font-semibold text-fg font-mono">endpoint_allowlist_host:</span> {discordSupervisedLivePreflightPacket.endpoint_allowlist_host}</div>
            <div><span className="font-semibold text-fg font-mono">endpoint_allowlist_path_shape:</span> {discordSupervisedLivePreflightPacket.endpoint_allowlist_path_shape}</div>
            <div><span className="font-semibold text-fg font-mono">credential_presence_check_performed:</span> {String(discordSupervisedLivePreflightPacket.credential_presence_check_performed)}</div>
            <div><span className="font-semibold text-fg font-mono">credential_value_read_made:</span> {String(discordSupervisedLivePreflightPacket.credential_value_read_made)}</div>
            <div><span className="font-semibold text-fg font-mono">env_value_read_made:</span> {String(discordSupervisedLivePreflightPacket.env_value_read_made)}</div>
            <div><span className="font-semibold text-fg font-mono">operator_go_phrase_required:</span> {String(discordSupervisedLivePreflightPacket.operator_go_phrase_required)}</div>
            <div><span className="font-semibold text-fg font-mono">operator_go_phrase_recorded:</span> {String(discordSupervisedLivePreflightPacket.operator_go_phrase_recorded)}</div>
            <div><span className="font-semibold text-fg font-mono">executable_outbox_entry_created:</span> {String(discordSupervisedLivePreflightPacket.executable_outbox_entry_created)}</div>
            <div><span className="font-semibold text-fg font-mono">real_outbox_entry_created:</span> {String(discordSupervisedLivePreflightPacket.real_outbox_entry_created)}</div>
            <div><span className="font-semibold text-fg font-mono">dispatch_outbox_ready:</span> {String(discordSupervisedLivePreflightPacket.dispatch_outbox_ready)}</div>
            <div><span className="font-semibold text-fg font-mono">dispatch_attempted:</span> {String(discordSupervisedLivePreflightPacket.dispatch_attempted)}</div>
            <div><span className="font-semibold text-fg font-mono">dispatch_request_count:</span> {discordSupervisedLivePreflightPacket.dispatch_request_count}</div>
            <div><span className="font-semibold text-fg font-mono">webhook_request_count:</span> {discordSupervisedLivePreflightPacket.webhook_request_count}</div>
            <div><span className="font-semibold text-fg font-mono">kill_switch_active:</span> {String(discordSupervisedLivePreflightPacket.kill_switch_active)}</div>
            <div><span className="font-semibold text-fg font-mono">ready_for_dispatch:</span> {String(discordSupervisedLivePreflightPacket.ready_for_dispatch)}</div>
          </div>

          <div className="mt-4 border-t border-line pt-3 font-mono">
            <div className="font-semibold text-xs text-accent uppercase tracking-wider mb-2">Request Envelope Preview</div>
            <div className="p-3 border border-line bg-surface-1 rounded-lg text-xs space-y-1">
              <div>Host: {requestEnvelopePreview.host}</div>
              <div>Method: {requestEnvelopePreview.method}</div>
              <div>Path Shape: {requestEnvelopePreview.path_shape}</div>
              <div className="break-all">Body Hash: {requestEnvelopePreview.body_hash_preview}</div>
              <div className="break-all">Payload Hash: {requestEnvelopePreview.payload_hash_preview}</div>
            </div>
          </div>

          <div className="mt-2 text-xs leading-relaxed text-fg-muted bg-status-blocked/5 p-2 rounded-lg border border-status-blocked/30 font-mono font-mono font-mono">
            <div>supervised_live_preflight_status=created_for_operator_review</div>
            <div>request_envelope_executable=false</div>
            <div>operator_go_phrase_required=true</div>
            <div>operator_go_phrase_recorded=false</div>
            <div>credential_value_read_made=false</div>
            <div>env_value_read_made=false</div>
            <div>dispatch_request_count=0</div>
            <div>webhook_request_count=0</div>
            <div>ready_for_dispatch=false</div>
            <div>live_action_allowed=false</div>
            <div>blocked_until_operator_explicit_live_scope=true</div>
            <div>Locks: no LLM/provider/API/env/credential/public URL/live action</div>
          </div>
        </div>
      </Panel>
      <SubstackArticleStudioCard mode="evidence" />
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 font-mono text-[11px] font-bold uppercase tracking-[0.14em] text-fg-subtle">
            <IconFingerprint className="h-4 w-4 text-accent" />
            Forensic mode
          </div>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight text-fg">
            Evidence Vault
          </h1>
          <div className="mt-1 break-all font-mono text-[12px] text-fg-muted">
            {activeTab === 'validation' ? packet.task_label : auditPacket.task_label}
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <StatusChip
              status={activeTab === 'validation' ? packet.result : 'verified'}
              icon
            >
              {activeTab === 'validation' ? packet.result_label : 'verified local audit'}
            </StatusChip>
            <EvidenceChip>
              {activeTab === 'validation' ? packet.commit_ref : auditPacket.source_baseline_commit.slice(0, 12)}
            </EvidenceChip>
            <span className="flex items-center gap-1 font-mono text-[11px] text-fg-subtle">
              <IconClock className="h-3.5 w-3.5" />
              {activeTab === 'validation' ? packet.timestamp : 'local-only-audit'}
            </span>
          </div>
        </div>
      </header>

      {/* Tab Switcher */}
      <div role="tablist" aria-label="Evidence Vault sections" className="flex gap-1.5 border-b border-line pb-px">
        <button
          type="button"
          id="vault-tab-validation"
          role="tab"
          aria-selected={activeTab === 'validation'}
          onClick={() => handleTabChange('validation')}
          className={`border-b-2 px-4 py-2.5 text-sm font-medium transition-colors -mb-px ${
            activeTab === 'validation'
              ? 'border-accent text-fg font-semibold'
              : 'border-transparent text-fg-muted hover:text-fg'
          }`}
        >
          System Validation Ledger
        </button>
        <button
          type="button"
          id="vault-tab-audit"
          role="tab"
          aria-selected={activeTab === 'manual_pilot_audit'}
          onClick={() => handleTabChange('manual_pilot_audit')}
          className={`border-b-2 px-4 py-2.5 text-sm font-medium transition-colors -mb-px ${
            activeTab === 'manual_pilot_audit'
              ? 'border-accent text-fg font-semibold'
              : 'border-transparent text-fg-muted hover:text-fg'
          }`}
        >
          Manual Pilot Audit
        </button>
      </div>


      <Panel
        title="V6 operator evidence vault · fixture-only"
        subtitle={`${v6Packet.evidence_vault_items.length} evidence cards · ${v6Packet.sample_scope}`}
        actions={<StatusChip status="review">sample_fixture_only</StatusChip>}
      >
        <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
          {v6Packet.evidence_vault_items.map((item) => (
            <article key={item.evidence_id} className="rounded-lg border border-line bg-surface-2 p-3">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="font-mono text-[11px] uppercase tracking-wide text-fg-subtle">
                    {item.evidence_type}
                  </div>
                  <h3 className="mt-1 truncate text-sm font-semibold text-fg">{item.evidence_id}</h3>
                </div>
                <StatusChip status="verified">{item.display_status}</StatusChip>
              </div>
              <div className="mt-2 break-all font-mono text-[11px] text-fg-muted">
                {item.source_hash_or_preview_hash}
              </div>
              <p className="mt-2 text-xs text-fg-muted">{item.source_file_path}</p>
            </article>
          ))}
        </div>
        <div className="mt-4 rounded-lg border border-status-blocked/30 bg-status-blocked/5 p-3">
          <div className="font-mono text-[11px] font-bold uppercase tracking-wide text-status-blocked">
            Live pilot blocked · no runtime proof
          </div>
          <p className="mt-1 text-xs leading-relaxed text-fg-muted">
            Runtime proof is false; provider, network, browser session, env line,
            raw secret, live send, and dispatch behavior remain disabled.
          </p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {v6Packet.live_pilot_status_card.blockers.map((blocker) => (
              <EvidenceChip key={blocker}>{blocker}</EvidenceChip>
            ))}
          </div>
        </div>
      </Panel>



      <Panel
        title="LinkedIn manual publication evidence vault"
        subtitle={`${linkedinManualExportPacket.export_packet_id} · ${linkedinPublicationAuditReviewMetricsSummaryPacket.publication_audit_review_packet_id}`}
        actions={<StatusChip status="review">sample_fixture_only</StatusChip>}
      >
        <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
          {[...linkedinManualApprovalExportEvidencePacket.evidence_cards, ...linkedinManualOperatorHandoffPacket.evidence_cards, ...linkedinManualPublicationUrlAuditImportPacket.evidence_cards, ...linkedinPublicationAuditReviewMetricsSummaryPacket.evidence_cards].map((card, index) => (
            <article key={`${card.card_id}-${index}`} className="rounded-lg border border-line bg-surface-2 p-3">
              <div className="font-mono text-[11px] uppercase tracking-wide text-fg-subtle">{card.card_type}</div>
              <h3 className="mt-1 break-all text-sm font-semibold text-fg">{card.source_id}</h3>
              <div className="mt-2 break-all font-mono text-[11px] text-fg-muted">{card.hash}</div>
              <StatusChip status={card.display_status === 'blocked' ? 'blocked' : card.display_status === 'bound' ? 'verified' : 'review'}>{card.display_status}</StatusChip>
            </article>
          ))}
        </div>
        <div className="mt-4 rounded-lg border border-status-blocked/30 bg-status-blocked/5 p-3 text-xs leading-relaxed text-fg-muted">
          LinkedIn fixture-only forensic surface: linkedin_api_used={String(linkedinPublicationAuditReviewMetricsSummaryPacket.linkedin_api_used)} · network_call_made={String(linkedinPublicationAuditReviewMetricsSummaryPacket.network_call_made)} · url_network_verified={String(linkedinPublicationAuditReviewMetricsSummaryPacket.url_network_verified)} · metrics_network_verified={String(linkedinPublicationAuditReviewMetricsSummaryPacket.metrics_network_verified)} · controls_enabled={String(linkedinPublicationAuditReviewMetricsSummaryPacket.enabled_publish_send_dispatch_approve_controls)}
        </div>
      </Panel>

      <Panel
        title="Substack approval/export evidence packet"
        subtitle={substackManualApprovalExportEvidencePacket.approval_export_evidence_packet_id}
        actions={<StatusChip status="review">{substackManualApprovalExportEvidencePacket.operator_review_status}</StatusChip>}
      >
        <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
          {substackManualApprovalExportEvidencePacket.evidence_cards.map((card) => (
            <article key={card.card_id} className="rounded-lg border border-line bg-surface-2 p-3">
              <div className="font-mono text-[11px] uppercase tracking-wide text-fg-subtle">{card.card_type}</div>
              <h3 className="mt-1 break-all text-sm font-semibold text-fg">{card.source_id}</h3>
              <div className="mt-2 break-all font-mono text-[11px] text-fg-muted">{card.hash}</div>
              <StatusChip status={card.display_status === 'blocked' ? 'blocked' : 'review'}>{card.display_status}</StatusChip>
            </article>
          ))}
        </div>
        <div className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-2">
          {(['live_publish_allowed', 'substack_api_used', 'provider_call_made', 'network_call_made', 'credential_read_made', 'env_value_read_made', 'browser_session_used'] as const).map((key) => (
            <div key={key} className="flex items-center justify-between gap-2 rounded-lg border border-status-blocked/30 bg-status-blocked/5 px-3 py-2">
              <span className="font-mono text-[11px] text-fg-muted">{key}</span>
              <StatusChip status="blocked">{String(substackManualApprovalExportEvidencePacket[key])}</StatusChip>
            </div>
          ))}
        </div>
      </Panel>



      <Panel
        title="Substack operator handoff evidence packet"
        subtitle={substackManualExportOperatorHandoffPacket.operator_handoff_packet_id}
        actions={<StatusChip status="review">{substackManualExportOperatorHandoffPacket.operator_handoff_status}</StatusChip>}
      >
        <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
          {substackManualExportOperatorHandoffPacket.evidence_cards.map((card) => (
            <article key={card.card_id} className="rounded-lg border border-line bg-surface-2 p-3">
              <div className="font-mono text-[11px] uppercase tracking-wide text-fg-subtle">{card.card_type}</div>
              <h3 className="mt-1 break-all text-sm font-semibold text-fg">{card.source_id}</h3>
              <div className="mt-2 break-all font-mono text-[11px] text-fg-muted">{card.hash}</div>
              <StatusChip status={card.display_status === 'blocked' ? 'blocked' : 'review'}>{card.display_status}</StatusChip>
            </article>
          ))}
        </div>
        <div className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-2">
          {(['manual_copy_only', 'live_publish_allowed', 'substack_api_used', 'provider_call_made', 'network_call_made', 'credential_read_made', 'env_value_read_made', 'browser_session_used'] as const).map((key) => (
            <div key={key} className="flex items-center justify-between gap-2 rounded-lg border border-status-blocked/30 bg-status-blocked/5 px-3 py-2">
              <span className="font-mono text-[11px] text-fg-muted">{key}</span>
              <StatusChip status={key === 'manual_copy_only' ? 'verified' : 'blocked'}>{String(substackManualExportOperatorHandoffPacket[key])}</StatusChip>
            </div>
          ))}
        </div>
      </Panel>


      <Panel
        title="Substack publication URL audit evidence"
        subtitle={substackManualPublicationUrlAuditImportPacket.publication_url_audit_packet_id}
        actions={<StatusChip status="review">{substackManualPublicationUrlAuditImportPacket.publication_audit_status}</StatusChip>}
      >
        <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
          {substackManualPublicationUrlAuditImportPacket.evidence_cards.map((card) => (
            <article key={card.card_id} className="rounded-lg border border-line bg-surface-2 p-3">
              <div className="font-mono text-[11px] uppercase tracking-wide text-fg-subtle">{card.card_type}</div>
              <h3 className="mt-1 break-all text-sm font-semibold text-fg">{card.source_id}</h3>
              <div className="mt-2 break-all font-mono text-[11px] text-fg-muted">{card.hash}</div>
              <StatusChip status={card.display_status === 'bound' ? 'verified' : 'review'}>{card.display_status}</StatusChip>
            </article>
          ))}
        </div>
        <div className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-2">
          {(['url_network_verified', 'network_call_made', 'substack_api_used', 'provider_call_made', 'credential_read_made', 'env_value_read_made', 'browser_session_used', 'live_publish_performed_by_contentops'] as const).map((key) => (
            <div key={key} className="flex items-center justify-between gap-2 rounded-lg border border-status-blocked/30 bg-status-blocked/5 px-3 py-2">
              <span className="font-mono text-[11px] text-fg-muted">{key}</span>
              <StatusChip status="blocked">{String(substackManualPublicationUrlAuditImportPacket[key])}</StatusChip>
            </div>
          ))}
        </div>
      </Panel>


      <Panel
        title="Substack publication audit review &amp; metrics evidence"
        subtitle={substackPublicationAuditReviewMetricsSummaryPacket.publication_audit_review_packet_id}
        actions={<StatusChip status="review">{substackPublicationAuditReviewMetricsSummaryPacket.publication_audit_status}</StatusChip>}
      >
        <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
          {substackPublicationAuditReviewMetricsSummaryPacket.evidence_cards.map((card) => (
            <article key={card.card_id} className="rounded-lg border border-line bg-surface-2 p-3">
              <div className="font-mono text-[11px] uppercase tracking-wide text-fg-subtle">{card.card_type}</div>
              <h3 className="mt-1 break-all text-sm font-semibold text-fg">{card.source_id}</h3>
              <div className="mt-2 break-all font-mono text-[11px] text-fg-muted">{card.hash}</div>
              <StatusChip status={card.display_status === 'bound' || card.display_status === 'verified' ? 'verified' : 'review'}>{card.display_status}</StatusChip>
            </article>
          ))}
        </div>
        <div className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-2">
          {(['metrics_network_verified', 'metrics_provider_api_used', 'url_network_verified', 'network_call_made', 'substack_api_used', 'provider_call_made', 'credential_read_made', 'env_value_read_made', 'browser_session_used', 'live_publish_performed_by_contentops', 'manual_publication_claim_operator_supplied', 'manual_metrics_claim_operator_supplied'] as const).map((key) => (
            <div key={key} className="flex items-center justify-between gap-2 rounded-lg border border-status-blocked/30 bg-status-blocked/5 px-3 py-2">
              <span className="font-mono text-[11px] text-fg-muted">{key}</span>
              <StatusChip status={key.endsWith('operator_supplied') ? 'verified' : 'blocked'}>{String(substackPublicationAuditReviewMetricsSummaryPacket[key])}</StatusChip>
            </div>
          ))}
        </div>
      </Panel>


      {activeTab === 'validation' ? (
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
          <div className="space-y-6 xl:col-span-2">
            <Panel title="Validation matrix" subtitle="Each check is part of the evidence record">
              <ul className="divide-y divide-line">
                {packet.validation_matrix.map((v) => {
                  const active =
                    selected?.kind === 'validation' && selected.id === v.id;
                  return (
                    <li key={v.id}>
                      <button
                        type="button"
                        id={`vm-${v.id}`}
                        onClick={() => select(selectValidation(v, packet.id))}
                        className={`flex w-full items-center justify-between gap-3 px-1 py-2.5 text-left transition-colors ${
                          active ? 'bg-accent/5' : 'hover:bg-surface-2'
                        }`}
                      >
                        <span className="flex items-center gap-2.5">
                          <StatusDot status={v.status} />
                          <span className="text-sm text-fg">{v.label}</span>
                        </span>
                        <span className="flex items-center gap-3">
                          <span className="hidden font-mono text-[11px] text-fg-subtle sm:inline">
                            {v.detail}
                          </span>
                          <StatusChip status={v.status}>{v.status}</StatusChip>
                        </span>
                      </button>
                    </li>
                  );
                })}
              </ul>
            </Panel>

            <Panel title="Forbidden scope â€” proven absent" subtitle="Static guarantees enforced for V5">
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                {packet.forbidden_scope.map((f) => (
                  <div
                    key={f.id}
                    className="flex items-center justify-between gap-2 rounded-lg border border-line bg-surface-2 px-3 py-2"
                  >
                    <span className="text-[12px] text-fg-muted">{f.label}</span>
                    <StatusChip status={f.status} icon>
                      clean
                    </StatusChip>
                  </div>
                ))}
              </div>
            </Panel>
          </div>

          <div className="space-y-6">
            <Panel
              title={
                <span className="flex items-center gap-2">
                  <IconFingerprint className="h-4 w-4 text-accent" />
                  Secret scan
                </span>
              }
            >
              <div className="flex items-center justify-between gap-2">
                <span className="flex items-center gap-2 text-sm text-fg-muted">
                  <StatusDot status={packet.secret_scan.status} />
                  {packet.secret_scan.label}
                </span>
                <StatusChip status={packet.secret_scan.status} icon>
                  {packet.secret_scan.status}
                </StatusChip>
              </div>
              <p className="mt-2 font-mono text-[11px] leading-relaxed text-fg-subtle">
                {packet.secret_scan.detail}
              </p>
            </Panel>

            <Panel title="Provenance">
              <div className="flex flex-wrap gap-1.5">
                {packet.provenance_chips.map((c) => (
                  <EvidenceChip key={c}>{c}</EvidenceChip>
                ))}
              </div>
              <div className="mt-4 border-t border-line pt-3">
                <SectionLabel>Source lineage</SectionLabel>
                <ul className="space-y-2">
                  {packet.source_lineage.map((l) => (
                    <li
                      key={l.id}
                      className="flex items-center gap-2.5 rounded-lg border border-line bg-surface-2 px-3 py-2"
                    >
                      <span className="font-mono text-[10.5px] text-fg-subtle">
                        {l.id}
                      </span>
                      <span className="text-[12px] text-fg-muted">{l.label}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </Panel>

            <Panel title="Audit trail">
              <ul className="space-y-3">
                {viewModel.audit_events.map((e) => (
                  <li key={e.id} className="relative pl-4">
                    <span className="absolute left-0 top-1.5 h-2 w-2 rounded-full bg-accent" />
                    <div className="text-[12px] text-fg">{e.action}</div>
                    <div className="mt-0.5 font-mono text-[10.5px] text-fg-subtle">
                      {e.actor} Â· {e.ref} Â· {e.timestamp}
                    </div>
                  </li>
                ))}
              </ul>
            </Panel>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.2fr_0.8fr]">
          <div className="space-y-6 min-w-0">
            {/* Manual Pilot Audit Overview */}
            <Panel
              title="Manual Pilot Audit Overview"
              subtitle="Verification status, hashes, baseline commit, and reference links"
              bodyClassName="p-4 space-y-4"
              actions={
                <button
                  type="button"
                  id="select-audit-packet-btn"
                  onClick={() => select(selectManualPilotTrailReconciliationAuditPacket(auditPacket))}
                  className={`rounded-lg border px-3 py-1 text-left transition-colors ${
                    selected?.kind === 'manual_pilot_audit_packet'
                      ? 'border-accent/40 bg-accent/5'
                      : 'border-line bg-surface-2 hover:border-line-strong'
                  }`}
                >
                  <span className="block font-mono text-[10.5px] font-semibold text-fg">
                    Audit SHA-256
                  </span>
                  <span className="font-mono text-[11px] text-fg-subtle">
                    {auditPacket.packet_hash.slice(0, 16)}...
                  </span>
                </button>
              }
            >
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                <MetricCard label="Audit Status" value="verified local (blocked/manual-only)" mono status="verified" />
                <MetricCard label="Contract Version" value={auditPacket.contract_version} mono status="neutral" />
                <MetricCard label="Contradictions" value={`${auditPacket.contradiction_results.contradictions_found.length}`} mono status="verified" />
              </div>

              <div className="rounded-xl border border-line bg-surface-2 p-4 space-y-2.5">
                <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle">
                  Compliance Metadata
                </div>
                <div className="grid gap-2">
                  <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-line bg-surface-1 px-3 py-2 text-sm">
                    <span className="font-semibold text-fg">Audit ID</span>
                    <span className="font-mono text-[11.5px] text-fg-muted break-all">{auditPacket.audit_id}</span>
                  </div>
                  <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-line bg-surface-1 px-3 py-2 text-sm">
                    <span className="font-semibold text-fg">Packet Hash</span>
                    <span className="font-mono text-[11.5px] text-fg-muted break-all">{auditPacket.packet_hash}</span>
                  </div>
                  <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-line bg-surface-1 px-3 py-2 text-sm">
                    <span className="font-semibold text-fg">Baseline Commit</span>
                    <span className="font-mono text-[11.5px] text-fg-muted break-all">{auditPacket.source_baseline_commit}</span>
                  </div>
                  <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-line bg-surface-1 px-3 py-2 text-sm">
                    <span className="font-semibold text-fg">Next Recommended Task</span>
                    <span className="font-mono text-[11.5px] text-fg-muted break-all">{auditPacket.next_recommended_task}</span>
                  </div>
                </div>
              </div>
            </Panel>

            {/* Invariants Validation Matrix */}
            <Panel
              title="Audit Invariant Results"
              subtitle="The 14 strict invariants verified against the manual pilot chain"
              bodyClassName="p-0 overflow-x-auto"
            >
              <table className="w-full min-w-[500px] border-collapse text-left text-sm">
                <thead>
                  <tr className="border-b border-line bg-surface-2 font-mono text-[10.5px] uppercase tracking-wider text-fg-muted">
                    <th className="px-4 py-3">Invariant Check</th>
                    <th className="px-4 py-3 text-center">Status</th>
                    <th className="px-4 py-3">Audit Scope</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {Object.entries(auditPacket.invariant_results).map(([name, passed]) => {
                    const isSelected = selected?.kind === 'audit_invariant' && selected.id === name;
                    return (
                      <tr
                        key={name}
                        id={`audit-invariant-row-${name}`}
                        onClick={() => select(selectAuditInvariant(name, passed))}
                        className={`cursor-pointer transition-colors hover:bg-surface-2/60 ${
                          isSelected ? 'bg-accent/5' : ''
                        }`}
                      >
                        <td className="px-4 py-3 font-mono text-[12px] font-semibold text-fg break-all">
                          {name}
                        </td>
                        <td className="px-4 py-3 text-center">
                          <StatusChip status={passed ? 'verified' : 'blocked'} nowrap>
                            {passed ? 'pass' : 'fail'}
                          </StatusChip>
                        </td>
                        <td className="px-4 py-3 text-[12.5px] text-fg-muted">
                          Local compliance audit constraint verification
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </Panel>

            {/* Audited Source Packets */}
            <Panel
              title="Audited Source Packets"
              subtitle="Underlying contract packets reconciled in the chain"
              bodyClassName="p-0 overflow-x-auto"
            >
              <table className="w-full min-w-[500px] border-collapse text-left text-sm">
                <thead>
                  <tr className="border-b border-line bg-surface-2 font-mono text-[10.5px] uppercase tracking-wider text-fg-muted">
                    <th className="px-4 py-3">Pipeline Stage</th>
                    <th className="px-4 py-3">Contract Version</th>
                    <th className="px-4 py-3">Packet Hash SHA-256</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {Object.entries(auditPacket.source_packets).map(([name, meta]) => (
                    <tr key={name} className="transition-colors hover:bg-surface-2/60">
                      <td className="px-4 py-3 font-mono text-[12px] font-semibold text-fg break-all">
                        {name}
                      </td>
                      <td className="px-4 py-3 font-mono text-[11.5px] text-fg-muted break-all">
                        {meta.contract_version}
                      </td>
                      <td className="px-4 py-3 font-mono text-[11.5px] text-fg-subtle break-all">
                        {meta.packet_hash}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Panel>
          </div>

          <div className="space-y-6 min-w-0">
            {/* Contradiction Checker */}
            <Panel
              title="Contradictions Detected"
              subtitle="Exceptions or conflicts found in the compliance chain"
              bodyClassName="p-4 space-y-3"
            >
              {auditPacket.contradiction_results.contradictions_found.length === 0 ? (
                <div className="rounded-xl border border-status-verified/20 bg-status-verified/5 p-4 text-center">
                  <div className="font-mono text-[11px] font-bold uppercase tracking-wider text-status-verified flex items-center justify-center gap-1.5">
                    No Contradictions
                  </div>
                  <p className="mt-1 text-xs text-fg-muted leading-relaxed">
                    Audit chain is internally consistent. All safety flags align.
                  </p>
                </div>
              ) : (
                <div className="space-y-2">
                  {auditPacket.contradiction_results.contradictions_found.map((c, i) => {
                    const active = selected?.kind === 'audit_contradiction' && selected.id === `contradiction-${i}`;
                    return (
                      <button
                        key={i}
                        type="button"
                        onClick={() => select(selectAuditContradiction(c, i))}
                        className={`w-full text-left rounded-lg border p-3 transition-colors ${
                          active ? 'border-accent/40 bg-accent/5' : 'border-status-blocked/20 bg-status-blocked/5'
                        }`}
                      >
                        <div className="font-semibold text-status-blocked text-xs">Contradiction #{i + 1}</div>
                        <p className="mt-1 font-mono text-[11px] text-fg leading-relaxed break-all">{c}</p>
                      </button>
                    );
                  })}
                </div>
              )}
            </Panel>

            {/* Missing Evidence Required */}
            <Panel
              title="Missing Evidence (Pending)"
              subtitle="Prerequisites remaining empty until manual pilot completion"
              bodyClassName="p-4 space-y-3"
            >
              <div className="rounded-xl border border-status-review/20 bg-status-review/5 p-3.5">
                <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-status-review flex items-center gap-1.5">
                  Reconciliation Blocked
                </div>
                <p className="mt-1.5 text-xs text-fg-muted leading-relaxed">
                  Compliance index requires off-system manual entry of verification evidence.
                </p>
              </div>

              <div className="space-y-2">
                {auditPacket.missing_evidence_results.required_missing.map((item) => (
                  <div
                    key={item}
                    className="flex items-center gap-2.5 rounded-lg border border-line bg-surface-2 px-3 py-2"
                  >
                    <StatusDot status="review" />
                    <span className="font-mono text-[12px] text-fg-muted">{item}</span>
                  </div>
                ))}
              </div>
            </Panel>

            {/* Disabled Live Actions */}
            <Panel
              title="Disabled Live Action Proof"
              subtitle="Rigid bounds enforced for manual-only assurance"
              bodyClassName="p-4"
            >
              <div className="mb-4 flex items-start gap-2.5 rounded-xl border border-status-blocked/20 bg-status-blocked/5 p-3">
                <IconBlock className="mt-0.5 h-3.5 w-3.5 shrink-0 text-status-blocked" />
                <p className="text-[12px] leading-relaxed text-fg-muted">
                  Audit confirms all platform publishing, account connection, credential sync, and scheduling endpoints are fully disabled.
                </p>
              </div>
              <div className="grid gap-2 sm:grid-cols-2">
                {['Publish', 'Send', 'Schedule', 'Connect account', 'Verify credentials', 'Sync platform', 'Live dispatch'].map((label) => (
                  <div key={label}>
                    <LockedAction
                      label={label}
                      reason="Audit boundary lock: live dispatch forbidden"
                    />
                  </div>
                ))}
              </div>
            </Panel>

            {/* Forensic References */}
            <Panel
              title="Evidence References"
              subtitle="Files and JSON targets on local disk"
              bodyClassName="p-4 space-y-3"
            >
              <div>
                <SectionLabel>Forensic MD Report</SectionLabel>
                <div className="font-mono text-[11px] text-fg-muted break-all rounded border border-line bg-surface-2 p-2.5">
                  docs/automation/0175AA/v5_manual_pilot_trail_reconciliation_audit_contract.md
                </div>
              </div>
              <div>
                <SectionLabel>Compliance JSON Packet</SectionLabel>
                <div className="font-mono text-[11px] text-fg-muted break-all rounded border border-line bg-surface-2 p-2.5">
                  docs/automation/0175AA/v5_manual_pilot_trail_reconciliation_audit_contract_packet.json
                </div>
              </div>
            </Panel>
          </div>
        </div>
      )}

      <Panel
        title="X manual publication evidence vault"
        subtitle={`${xManualExportPacket.export_packet_id} | ${xPublicationAuditReviewMetricsSummaryPacket.publication_audit_review_packet_id}`}
        actions={<StatusChip status="blocked">manual fixture only</StatusChip>}
      >
        <div className="grid gap-2 md:grid-cols-2">
          {[...xManualApprovalExportEvidencePacket.evidence_cards, ...xManualOperatorHandoffPacket.evidence_cards, ...xManualPublicationUrlAuditImportPacket.evidence_cards, ...xPublicationAuditReviewMetricsSummaryPacket.evidence_cards].map((card, index) => (
            <div key={`${card.card_id}-${index}`} className="rounded-lg border border-line bg-surface-2 p-3">
              <div className="text-xs font-semibold text-fg">{card.card_id}</div>
              <div className="mt-1 font-mono text-[10px] text-fg-muted">{card.source_id}</div>
              <div className="mt-1 break-all font-mono text-[10px] text-accent">{card.hash}</div>
            </div>
          ))}
        </div>
        <div className="mt-4 rounded-lg border border-status-blocked/30 bg-status-blocked/5 p-3 text-xs leading-relaxed text-fg-muted">
          X evidence is operator-supplied fixture evidence only: x_api_used={String(xManualExportPacket.x_api_used)} | url_network_verified={String(xManualPublicationUrlAuditImportPacket.url_network_verified)} | metrics_network_verified={String(xPublicationAuditReviewMetricsSummaryPacket.metrics_network_verified)} | controls_enabled={String(xManualOperatorHandoffPacket.enabled_publish_send_dispatch_approve_controls)}.
        </div>
      </Panel>
    </div>
  );
}

function MetricCard({
  label,
  value,
  mono,
  status,
}: {
  label: string;
  value: string;
  mono?: boolean;
  status?: 'verified' | 'review' | 'blocked' | 'neutral';
}) {
  return (
    <div className="rounded-xl border border-line bg-surface-2 p-3">
      <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle">
        {label}
      </div>
      <div className={`mt-1 break-all text-sm font-semibold text-fg ${mono ? 'font-mono text-[12px] font-normal' : ''}`}>
        {status ? <StatusChip status={status}>{value}</StatusChip> : value}
      </div>
    </div>
  );
}
