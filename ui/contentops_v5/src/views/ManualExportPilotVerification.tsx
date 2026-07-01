// Capital Chronicle ContentOps V5 — Manual Export / Pilot Verification.
// Read-only local package preview. No API calls, credentials, scheduling, or posting.

import { SubstackArticleStudioCard } from './SubstackArticleStudioCard';
import {
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
import { manualExportPilotVerificationPacket as p } from '../data/manualExportPilotVerificationPacket';
import { useApp } from '../state';
import {
  selectManualCopyBlock,
  selectManualExportChecklistItem,
  selectManualExportPilotPacket,
  selectManualExportTarget,
} from '../selectors';
import { IconBlock, IconShield } from '../ui/icons';
import { LockedAction, Panel, StatusChip, StatusDot } from '../ui/primitives';

export function ManualExportPilotVerification() {
  const { select, selected } = useApp();
  const activeTargets = p.platform_targets.filter((t) => t.target_class === 'active_manual_export_preview');
  const futureTargets = p.platform_targets.filter((t) => t.target_class === 'future_manual_expansion');

  return (
    <div className="space-y-6">

      <ManualDistributionRegistryPanel />
      <SubstackArticleStudioCard mode="manual" />
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 font-mono text-[11px] font-bold uppercase tracking-[0.14em] text-fg-subtle">
            Manual Export Contract
            <span className="text-fg-subtle/60">·</span>
            <span className="text-fg-muted">0174UW</span>
          </div>
          <h1 className="mt-2 flex items-center gap-2 text-2xl font-semibold tracking-tight text-fg">
            <IconShield className="h-6 w-6 text-accent" />
            Manual Export &amp; Pilot Verification
          </h1>
          <p className="mt-1 max-w-3xl text-sm font-medium leading-relaxed text-fg-muted">
            Reviewable local export package for supervised pilot editorial runs.
            It prepares copy blocks and verification evidence only; operators must
            manually copy/publish outside ContentOps after human review.
          </p>
        </div>
        <button
          type="button"
          id="select-manual-export-packet-btn"
          onClick={() => select(selectManualExportPilotPacket(p))}
          className={`rounded-lg border px-3 py-1 text-left transition-colors ${
            selected?.kind === 'manual_export_pilot_packet'
              ? 'border-accent/40 bg-accent/5'
              : 'border-line bg-surface-2 hover:border-line-strong'
          }`}
        >
          <span className="block font-mono text-[10.5px] font-semibold text-fg">
            Export SHA-256
          </span>
          <span className="font-mono text-[11px] text-fg-subtle">
            {p.packet_hash.slice(0, 16)}...
          </span>
        </button>
      </header>

      <div className="grid grid-cols-1 gap-3 md:grid-cols-5">
        {[
          'Manual Export Only',
          'No platform API',
          'No credentials loaded',
          'No live dispatch',
          'Operator publishes outside ContentOps',
        ].map((label, index) => (
          <div
            key={label}
            id={`manual-export-safety-${index}`}
            className="rounded-xl border border-status-blocked/30 bg-status-blocked/5 p-3"
          >
            <div className="flex items-center gap-2">
              <StatusDot status="blocked" />
              <span className="text-[12px] font-semibold uppercase tracking-wide text-fg">
                {label}
              </span>
            </div>
          </div>
        ))}
      </div>

      <Panel
        title="Export Package Overview"
        subtitle="Packet identity, source 0174UU binding, and pilot verification posture"
        bodyClassName="p-4"
      >
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
          <Metric label="Package" value={p.export_package_id} mono status="review" />
          <Metric label="Pilot status" value={p.pilot_verification_status} mono status="blocked" />
          <Metric label="Source hash" value={p.source_read_model_packet_hash} mono status="verified" />
          <Metric label="Packet hash" value={p.packet_hash} mono status="verified" />
        </div>
        <div className="mt-4 rounded-xl border border-line bg-surface-2 p-4">
          <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle">
            Evidence refs
          </div>
          <div className="mt-2 grid gap-2">
            {p.evidence_refs.map((ref) => (
              <div key={ref} className="rounded-lg border border-line bg-surface-1 px-3 py-2 font-mono text-[12px] text-fg-muted">
                {ref}
              </div>
            ))}
          </div>
        </div>
      </Panel>

      <Panel
        title="Operator feedback backlog · manual export review"
        subtitle={`${operatorFeedbackBacklogSummaryPacket.candidate_count} candidates · ${operatorFeedbackBacklogSummaryPacket.summary_method}`}
        actions={<StatusChip status="review">operator-supplied feedback only</StatusChip>}
      >
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
          <Metric label="Feedback intake packet" value={operatorSuppliedFeedbackIntakePacket.feedback_intake_packet_id} mono status="review" />
          <Metric label="Feedback intake hash" value={operatorSuppliedFeedbackIntakePacket.exact_payload_hash} mono status="verified" />
          <Metric label="Backlog summary packet" value={operatorFeedbackBacklogSummaryPacket.backlog_summary_packet_id} mono status="review" />
          <Metric label="Backlog summary hash" value={operatorFeedbackBacklogSummaryPacket.exact_payload_hash} mono status="verified" />
          <Metric label="feedback_count" value={String(operatorFeedbackBacklogSummaryPacket.feedback_count)} status="verified" />
          <Metric label="candidate_count" value={String(operatorFeedbackBacklogSummaryPacket.candidate_count)} status="verified" />
          <Metric label="summary_method" value={operatorFeedbackBacklogSummaryPacket.summary_method} mono status="verified" />
          <Metric label="operator-supplied only" value={operatorSuppliedFeedbackIntakePacket.intake_status} mono status="review" />
        </div>
        <div className="mt-4 rounded-lg border border-status-blocked/30 bg-status-blocked/5 p-3 text-xs leading-relaxed text-fg-muted">
          Operator-supplied feedback only. No LLM/provider call, public URL fetch, platform API, browser session, env/credential read, publish, send, dispatch, approve, or schedule action. No approve/send/publish/dispatch/schedule controls are enabled on this read-only Manual Export surface.
        </div>
      </Panel>

      <Panel
        title="Feedback backlog → next article brief candidate"
        subtitle={`${feedbackBacklogNextArticleBriefPacket.selected_backlog_candidate_id} · ${feedbackBacklogNextArticleBriefPacket.selection_method}`}
        actions={<StatusChip status="review">{feedbackBacklogNextArticleBriefPacket.candidate_review_status}</StatusChip>}
      >
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
          <Metric label="Brief packet" value={feedbackBacklogNextArticleBriefPacket.next_article_brief_packet_id} mono status="review" />
          <Metric label="Brief hash" value={feedbackBacklogNextArticleBriefPacket.exact_payload_hash} mono status="verified" />
          <Metric label="Source backlog" value={feedbackBacklogNextArticleBriefPacket.source_backlog_summary_packet_id} mono status="verified" />
          <Metric label="Priority score" value={String(feedbackBacklogNextArticleBriefPacket.selected_priority_score)} status="review" />
        </div>
        <article className="mt-4 rounded-lg border border-line bg-surface-2 p-4">
          <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle">Review-only working headline</div>
          <h3 className="mt-1 text-base font-semibold text-fg">{feedbackBacklogNextArticleBriefPacket.brief_candidate.working_headline}</h3>
          <p className="mt-2 text-sm leading-relaxed text-fg-muted">{feedbackBacklogNextArticleBriefPacket.brief_candidate.editorial_angle}</p>
          <div className="mt-3 flex flex-wrap gap-1.5">
            {feedbackBacklogNextArticleBriefPacket.selected_topic_tags.map((tag) => <StatusChip key={tag} status="review">{tag}</StatusChip>)}
          </div>
        </article>
        <div className="mt-4 rounded-lg border border-status-blocked/30 bg-status-blocked/5 p-3 text-xs leading-relaxed text-fg-muted">
          Review-only bridge from operator-supplied feedback backlog. source_pack_required_before_drafting={String(feedbackBacklogNextArticleBriefPacket.source_pack_required_before_drafting)} · canonical_draft_created={String(feedbackBacklogNextArticleBriefPacket.canonical_draft_created)} · llm_provider_call_made={String(feedbackBacklogNextArticleBriefPacket.llm_provider_call_made)} · platform_api_used={String(feedbackBacklogNextArticleBriefPacket.platform_api_used)} · public_url_fetch_made={String(feedbackBacklogNextArticleBriefPacket.public_url_fetch_made)}.
        </div>
      </Panel>



      <Panel
        title="Substack operator handoff packet"
        subtitle={substackManualExportOperatorHandoffPacket.operator_handoff_packet_id}
        actions={<StatusChip status="review">{substackManualExportOperatorHandoffPacket.operator_handoff_status}</StatusChip>}
      >
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          <Metric label="Handoff hash" value={substackManualExportOperatorHandoffPacket.operator_handoff_hash} mono status="verified" />
          <Metric label="Export payload" value={substackManualExportOperatorHandoffPacket.source_export_payload_hash} mono status="verified" />
          <Metric label="Approval evidence" value={substackManualExportOperatorHandoffPacket.approval_export_evidence_hash} mono status="verified" />
        </div>
        <div className="mt-4 grid grid-cols-1 gap-2 md:grid-cols-2">
          {substackManualExportOperatorHandoffPacket.manual_copy_checklist.map((item) => (
            <div key={item.check_id} className="rounded-lg border border-line bg-surface-2 px-3 py-2">
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm font-semibold text-fg">{item.label}</span>
                <StatusChip status="review">{item.status}</StatusChip>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4 rounded-lg border border-status-blocked/30 bg-status-blocked/5 p-3 text-xs leading-relaxed text-fg-muted">
          manual_copy_only={String(substackManualExportOperatorHandoffPacket.manual_copy_only)} ? live_publish_allowed={String(substackManualExportOperatorHandoffPacket.live_publish_allowed)} ? substack_api_used={String(substackManualExportOperatorHandoffPacket.substack_api_used)} ? enabled controls={String(substackManualExportOperatorHandoffPacket.enabled_publish_send_dispatch_approve_controls)}
        </div>
      </Panel>



      <Panel
        title="Substack manual publication URL audit import"
        subtitle={substackManualPublicationUrlAuditImportPacket.publication_url_audit_packet_id}
        actions={<StatusChip status="review">{substackManualPublicationUrlAuditImportPacket.publication_audit_status}</StatusChip>}
      >
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          <Metric label="URL hash" value={substackManualPublicationUrlAuditImportPacket.operator_supplied_publication_url_hash} mono status="verified" />
          <Metric label="Network verified" value={String(substackManualPublicationUrlAuditImportPacket.url_network_verified)} mono status="blocked" />
          <Metric label="ContentOps publish" value={String(substackManualPublicationUrlAuditImportPacket.live_publish_performed_by_contentops)} mono status="blocked" />
        </div>
        <div className="mt-4 rounded-lg border border-status-blocked/30 bg-status-blocked/5 p-3 text-xs leading-relaxed text-fg-muted">
          Operator-supplied URL text only; not opened, fetched, scraped, or network verified.
          substack_api_used={String(substackManualPublicationUrlAuditImportPacket.substack_api_used)} ? network_call_made={String(substackManualPublicationUrlAuditImportPacket.network_call_made)} ? manual_publication_claim_operator_supplied={String(substackManualPublicationUrlAuditImportPacket.manual_publication_claim_operator_supplied)}
        </div>
      </Panel>



      <Panel
        title="Substack publication audit review &amp; manual metrics summary"
        subtitle={substackPublicationAuditReviewMetricsSummaryPacket.publication_audit_review_packet_id}
        actions={<StatusChip status="review">{substackPublicationAuditReviewMetricsSummaryPacket.publication_audit_status}</StatusChip>}
      >
        <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
          <Metric label="Audit status" value={substackPublicationAuditReviewMetricsSummaryPacket.publication_audit_status} mono status="review" />
          <Metric label="Metrics status" value={substackPublicationAuditReviewMetricsSummaryPacket.metrics_summary_status} mono status="review" />
          <Metric label="Metrics source" value={substackPublicationAuditReviewMetricsSummaryPacket.metrics_source} mono status="verified" />
          <Metric label="Metrics verified" value={String(substackPublicationAuditReviewMetricsSummaryPacket.metrics_network_verified)} mono status="blocked" />
        </div>
        <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-8">
          <Metric label="Views" value={String(substackPublicationAuditReviewMetricsSummaryPacket.manual_metrics.views)} status="verified" />
          <Metric label="Opens" value={String(substackPublicationAuditReviewMetricsSummaryPacket.manual_metrics.opens)} status="verified" />
          <Metric label="Likes" value={String(substackPublicationAuditReviewMetricsSummaryPacket.manual_metrics.likes)} status="verified" />
          <Metric label="Comments" value={String(substackPublicationAuditReviewMetricsSummaryPacket.manual_metrics.comments)} status="verified" />
          <Metric label="Shares" value={String(substackPublicationAuditReviewMetricsSummaryPacket.manual_metrics.shares)} status="verified" />
          <Metric label="Restacks" value={String(substackPublicationAuditReviewMetricsSummaryPacket.manual_metrics.restacks)} status="verified" />
          <Metric label="Sub subscribers" value={String(substackPublicationAuditReviewMetricsSummaryPacket.manual_metrics.subscribers_delta)} status="verified" />
          <Metric label="Notes" value={substackPublicationAuditReviewMetricsSummaryPacket.manual_metrics.notes || 'None'} status="verified" />
        </div>
        <div className="mt-4 rounded-lg border border-status-blocked/30 bg-status-blocked/5 p-3 text-xs leading-relaxed text-fg-muted">
          Operator-supplied publication metrics only; no live API calls, scraping, or network requests performed.
          substack_api_used={String(substackPublicationAuditReviewMetricsSummaryPacket.substack_api_used)} ? metrics_network_verified={String(substackPublicationAuditReviewMetricsSummaryPacket.metrics_network_verified)} ? manual_metrics_claim_operator_supplied={String(substackPublicationAuditReviewMetricsSummaryPacket.manual_metrics_claim_operator_supplied)}
        </div>
      </Panel>



      <Panel
        title="LinkedIn manual publication evidence loop"
        subtitle={linkedinManualOperatorHandoffPacket.operator_handoff_packet_id}
        actions={<StatusChip status="review">fixture-only</StatusChip>}
      >
        <div className="grid grid-cols-1 gap-3 md:grid-cols-5">
          <Metric label="Export" value={linkedinManualExportPacket.export_packet_id} mono status="verified" />
          <Metric label="Approval evidence" value={linkedinManualApprovalExportEvidencePacket.approval_export_evidence_packet_id} mono status="review" />
          <Metric label="URL audit" value={linkedinManualPublicationUrlAuditImportPacket.publication_url_audit_packet_id} mono status="review" />
          <Metric label="Metrics" value={linkedinPublicationAuditReviewMetricsSummaryPacket.publication_audit_review_packet_id} mono status="review" />
          <Metric label="LinkedIn API" value={String(linkedinManualExportPacket.linkedin_api_used)} mono status="blocked" />
        </div>
        <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7">
          <Metric label="Impressions" value={String(linkedinPublicationAuditReviewMetricsSummaryPacket.manual_metrics.impressions)} status="verified" />
          <Metric label="Reactions" value={String(linkedinPublicationAuditReviewMetricsSummaryPacket.manual_metrics.reactions)} status="verified" />
          <Metric label="Comments" value={String(linkedinPublicationAuditReviewMetricsSummaryPacket.manual_metrics.comments)} status="verified" />
          <Metric label="Reposts" value={String(linkedinPublicationAuditReviewMetricsSummaryPacket.manual_metrics.reposts)} status="verified" />
          <Metric label="Clicks" value={String(linkedinPublicationAuditReviewMetricsSummaryPacket.manual_metrics.clicks)} status="verified" />
          <Metric label="Profile views" value={String(linkedinPublicationAuditReviewMetricsSummaryPacket.manual_metrics.profile_views)} status="verified" />
          <Metric label="Followers" value={String(linkedinPublicationAuditReviewMetricsSummaryPacket.manual_metrics.followers_delta)} status="verified" />
        </div>
        <div className="mt-4 rounded-lg border border-status-blocked/30 bg-status-blocked/5 p-3 text-xs leading-relaxed text-fg-muted">
          LinkedIn manual fixture only; no LinkedIn API, browser automation, credential/session/env read, URL fetch/scrape/network verification, post, DM, comment, like, reaction, scheduler, dispatch, send, or approval control.
          enabled={String(linkedinManualOperatorHandoffPacket.enabled_publish_send_dispatch_approve_controls)} · url_network_verified={String(linkedinManualPublicationUrlAuditImportPacket.url_network_verified)} · metrics_network_verified={String(linkedinPublicationAuditReviewMetricsSummaryPacket.metrics_network_verified)}
        </div>
      </Panel>



      <Panel
        title="X manual publication evidence loop"
        subtitle={xManualOperatorHandoffPacket.operator_handoff_packet_id}
        actions={<StatusChip status="review">fixture-only</StatusChip>}
      >
        <div className="grid grid-cols-1 gap-3 md:grid-cols-5">
          <Metric label="X draft" value={xManualExportPacket.export_packet_id} mono status="verified" />
          <Metric label="Approval evidence" value={xManualApprovalExportEvidencePacket.approval_export_evidence_packet_id} mono status="review" />
          <Metric label="URL audit" value={xManualPublicationUrlAuditImportPacket.publication_url_audit_packet_id} mono status="review" />
          <Metric label="Metrics" value={xPublicationAuditReviewMetricsSummaryPacket.publication_audit_review_packet_id} mono status="review" />
          <Metric label="X API" value={String(xManualExportPacket.x_api_used)} mono status="blocked" />
        </div>
        <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-8">
          <Metric label="Impressions" value={String(xPublicationAuditReviewMetricsSummaryPacket.manual_metrics.impressions)} status="verified" />
          <Metric label="Likes" value={String(xPublicationAuditReviewMetricsSummaryPacket.manual_metrics.likes)} status="verified" />
          <Metric label="Replies" value={String(xPublicationAuditReviewMetricsSummaryPacket.manual_metrics.replies)} status="verified" />
          <Metric label="Reposts" value={String(xPublicationAuditReviewMetricsSummaryPacket.manual_metrics.reposts)} status="verified" />
          <Metric label="Quotes" value={String(xPublicationAuditReviewMetricsSummaryPacket.manual_metrics.quotes)} status="verified" />
          <Metric label="Bookmarks" value={String(xPublicationAuditReviewMetricsSummaryPacket.manual_metrics.bookmarks)} status="verified" />
          <Metric label="Profile visits" value={String(xPublicationAuditReviewMetricsSummaryPacket.manual_metrics.profile_visits)} status="verified" />
          <Metric label="Link clicks" value={String(xPublicationAuditReviewMetricsSummaryPacket.manual_metrics.link_clicks)} status="verified" />
        </div>
        <div className="mt-4 rounded-lg border border-status-blocked/30 bg-status-blocked/5 p-3 text-xs leading-relaxed text-fg-muted">
          X manual fixture only; no X API, browser automation, credential/session/env read, URL fetch/scrape/network verification, post, DM, reply, like, repost, quote-post, scheduler, dispatch, send, or approval control.
          enabled={String(xManualOperatorHandoffPacket.enabled_publish_send_dispatch_approve_controls)} ? url_network_verified={String(xManualPublicationUrlAuditImportPacket.url_network_verified)} ? metrics_network_verified={String(xPublicationAuditReviewMetricsSummaryPacket.metrics_network_verified)}
        </div>
      </Panel>

      <Panel
        title="Platform Manual Copy Targets"
        subtitle="Select any target to inspect manual/no-api/no-credential flags"
        bodyClassName="p-0 overflow-x-auto"
      >
        <table className="w-full min-w-[760px] border-collapse text-left text-sm">
          <thead>
            <tr className="border-b border-line bg-surface-2 font-mono text-[10.5px] uppercase tracking-wider text-fg-muted">
              <th className="px-4 py-3">Target</th>
              <th className="px-4 py-3">Class</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">No API</th>
              <th className="px-4 py-3">No Credentials</th>
              <th className="px-4 py-3">Dispatch</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {p.platform_targets.map((target) => (
              <tr
                key={target.target_id}
                id={`manual-export-target-${target.target_id}`}
                onClick={() => select(selectManualExportTarget(target))}
                className={`cursor-pointer transition-colors hover:bg-surface-2/60 ${
                  selected?.kind === 'manual_export_target' && selected.id === target.target_id
                    ? 'bg-accent/5'
                    : ''
                }`}
              >
                <td className="px-4 py-3 font-mono text-[12px] font-semibold text-fg">
                  {target.platform_label}
                </td>
                <td className="px-4 py-3 font-mono text-[11px] text-fg-subtle">
                  {target.target_class}
                </td>
                <td className="px-4 py-3">
                  <StatusChip status={target.status === 'future_gate_blocked' ? 'blocked' : 'review'}>
                    {target.status}
                  </StatusChip>
                </td>
                <td className="px-4 py-3"><StatusChip status="verified" nowrap>true</StatusChip></td>
                <td className="px-4 py-3"><StatusChip status="verified" nowrap>true</StatusChip></td>
                <td className="px-4 py-3"><StatusChip status="blocked">blocked</StatusChip></td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <Panel
          title="Manual Copy Blocks"
          subtitle="Local draft text only; no secrets, raw response bodies, or live market data"
          bodyClassName="p-4"
        >
          <div className="grid gap-3">
            {p.manual_copy_blocks.map((block) => (
              <button
                key={block.block_id}
                type="button"
                id={`manual-copy-block-${block.block_id}`}
                onClick={() => select(selectManualCopyBlock(block))}
                className={`rounded-xl border p-4 text-left transition-colors hover:border-line-strong ${
                  selected?.kind === 'manual_copy_block' && selected.id === block.block_id
                    ? 'border-accent/40 bg-accent/5'
                    : 'border-line bg-surface-2'
                }`}
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h3 className="font-semibold text-fg">{block.title}</h3>
                  <StatusChip status="review">manual review</StatusChip>
                </div>
                <p className="mt-2 text-sm leading-relaxed text-fg-muted">
                  {block.copy_text}
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  <StatusChip status="verified">no secrets</StatusChip>
                  <StatusChip status="verified">no raw bodies</StatusChip>
                  <StatusChip status="blocked">not public-postable</StatusChip>
                </div>
              </button>
            ))}
          </div>
        </Panel>

        <Panel
          title="Pilot Verification Packet"
          subtitle="Blocked-first proof packet for human review"
          bodyClassName="p-4"
        >
          <div className="space-y-3">
            <Metric label="Verification" value={p.pilot_verification_packet.verification_id} mono status="review" />
            <Metric label="Status" value={p.pilot_verification_packet.status} mono status="blocked" />
            <Metric label="Verification hash" value={p.pilot_verification_packet.packet_hash} mono status="verified" />
          </div>
          <div className="mt-4 space-y-2">
            {p.operator_review_checklist.map((item) => (
              <button
                key={item.item_id}
                type="button"
                id={`manual-export-check-${item.item_id}`}
                onClick={() => select(selectManualExportChecklistItem(item))}
                className="flex w-full items-start gap-2 rounded-lg border border-line bg-surface-2 px-3 py-2 text-left transition-colors hover:border-line-strong"
              >
                <StatusDot status={item.status} />
                <span className="min-w-0">
                  <span className="block text-sm font-semibold text-fg">{item.label}</span>
                  <span className="block text-[12px] leading-relaxed text-fg-muted">{item.detail}</span>
                </span>
              </button>
            ))}
          </div>
        </Panel>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Panel title="Empty Placeholders" subtitle="Not recorded until operator acts outside ContentOps" bodyClassName="p-4">
          <div className="grid gap-3">
            <Placeholder label="Manual publish URL" status={p.manual_publish_url_placeholder.status} detail={p.manual_publish_url_placeholder.detail} />
            <Placeholder label="Manual metrics" status={p.manual_metrics_placeholder.status} detail={p.manual_metrics_placeholder.detail} />
            <Placeholder label="Review signature" status={p.review_signature_placeholder.status} detail="Signature value is empty and not cryptographic." />
          </div>
        </Panel>

        <Panel title="Disabled Future Gates" subtitle="Visible controls prove live actions remain impossible" bodyClassName="p-4">
          <div className="mb-4 flex items-start gap-3 rounded-xl border border-status-blocked/30 bg-status-blocked/5 p-3">
            <IconBlock className="mt-0.5 h-4 w-4 shrink-0 text-status-blocked" />
            <p className="text-[12px] leading-relaxed text-fg-muted">
              Live controls are intentionally disabled: publish, send, schedule,
              connect account, verify credentials, sync platform, and live dispatch.
            </p>
          </div>
          <div className="grid gap-2 sm:grid-cols-2">
            {['Publish', 'Send', 'Schedule', 'Connect account', 'Verify credentials', 'Sync platform', 'Live dispatch'].map((label) => (
              <div key={label} id={`manual-export-disabled-${label.toLowerCase().replace(/\s+/g, '-')}`}>
                <LockedAction
                  label={label}
                  reason="manual_export_pilot_verification_only_no_live_affordance"
                />
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <Panel title="Expansion Targets" subtitle="Future manual copy targets stay blocked until separate contracts exist" bodyClassName="p-4">
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-5">
          {futureTargets.map((target) => (
            <div key={target.target_id} className="rounded-xl border border-line bg-surface-2 p-3">
              <div className="text-sm font-semibold text-fg">{target.platform_label}</div>
              <div className="mt-1 font-mono text-[11px] text-fg-subtle">{target.blocked_reason}</div>
              <div className="mt-3"><StatusChip status="blocked">future gate</StatusChip></div>
            </div>
          ))}
        </div>
        <div className="sr-only">{activeTargets.length} active manual export targets</div>
      </Panel>
    </div>
  );
}

function Metric({ label, value, mono, status }: { label: string; value: string; mono?: boolean; status?: 'verified' | 'review' | 'blocked' }) {
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

function Placeholder({ label, status, detail }: { label: string; status: string; detail: string }) {
  return (
    <div className="rounded-xl border border-line bg-surface-2 p-3">
      <div className="flex items-center justify-between gap-2">
        <span className="text-sm font-semibold text-fg">{label}</span>
        <StatusChip status="review">{status}</StatusChip>
      </div>
      <div className="mt-2 rounded-lg border border-dashed border-line-strong bg-surface-1 px-3 py-2 font-mono text-[12px] text-fg-subtle">
        value: ''
      </div>
      <p className="mt-2 text-[12px] leading-relaxed text-fg-muted">{detail}</p>
    </div>
  );
}
