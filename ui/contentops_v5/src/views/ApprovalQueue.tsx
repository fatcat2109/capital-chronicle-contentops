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
