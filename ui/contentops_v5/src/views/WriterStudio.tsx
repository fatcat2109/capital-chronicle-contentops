// Capital Chronicle ContentOps V5 — Writer Studio view.
// Editorial drafting workspace: outline, guardrails, SEO, AI variants, media.
// AI Writer is UI-only and review-only. No provider/network call. Nothing
// here is public-postable. No storage, no credentials.

import { SubstackArticleStudioCard } from './SubstackArticleStudioCard';
import { useApp } from '../state';
import { viewModel } from '../fixtures';
import { selectAiVariant, selectMediaAsset, selectCandidateReviewItem, selectEditorialBriefReviewPacket, selectCandidateGateItem, selectContentIntentGatePrecheckPacket, selectReviewOnlyIntentItem, selectReviewOnlyContentIntentPacket, selectInputCapturePrecheckItem, selectOperatorInputCapturePrecheckPacket, selectSupervisedInputStubContractPacket, selectSupervisedInputStubItem, selectDraftEligibilityGatePrecheckPacket, selectDraftEligibilityItem } from '../selectors';
import { editorialBriefReviewAdapter } from '../data/editorialBriefReviewAdapter';
import { contentIntentGatePrecheckAdapter } from '../data/contentIntentGatePrecheckAdapter';
import { reviewOnlyContentIntentAdapter } from '../data/reviewOnlyContentIntentAdapter';
import { operatorInputCapturePrecheckAdapter } from '../data/operatorInputCapturePrecheckAdapter';
import { supervisedInputStubContractAdapter } from '../data/supervisedInputStubContractAdapter';
import { draftEligibilityGatePrecheckAdapter } from '../data/draftEligibilityGatePrecheckAdapter';
import { IconImage, IconSparkle } from '../ui/icons';
import {
  EvidenceChip,
  Panel,
  ScoreBar,
  SectionLabel,
  StatusChip,
  StatusDot,
} from '../ui/primitives';
import type { StatusKind } from '../types';

export function WriterStudio() {
  const { select, selected } = useApp();
  const d = viewModel.editorial_draft;

  return (
    <div className="space-y-6">
      <SubstackArticleStudioCard mode="writer" />
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 font-mono text-[11px] font-bold uppercase tracking-[0.14em] text-fg-subtle">
            Editorial drafting
            <span className="text-fg-subtle/60">·</span>
            <span className="text-fg-muted">{d.id}</span>
          </div>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight text-fg">
            Writer Studio
          </h1>
          <p className="mt-1 text-sm font-medium text-fg-muted">{d.title}</p>
          <div className="mt-2 flex flex-wrap items-center gap-1.5">
            {d.platform_tabs.map((p, i) => (
              <span
                key={p}
                className={`rounded-md px-2 py-0.5 font-mono text-[11px] ${
                  i === 0
                    ? 'bg-fg text-bg'
                    : 'border border-line bg-surface-2 text-fg-muted'
                }`}
              >
                {p}
              </span>
            ))}
          </div>
        </div>
        <StatusChip status="review" icon>
          Review only · not postable
        </StatusChip>
      </header>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        {/* Draft + outline */}
        <div className="space-y-6 xl:col-span-2">
          {/* Editorial Brief Review Queue Panel */}
          <Panel
            title="Editorial Brief Review Queue"
            subtitle="Local candidate metadata bridge · no article draft"
            actions={
              <button
                type="button"
                id="btn-inspect-review-packet"
                onClick={() => select(selectEditorialBriefReviewPacket(editorialBriefReviewAdapter.packet))}
                className="rounded-md border border-line bg-surface-2 px-2.5 py-1 font-mono text-[10.5px] text-fg-muted hover:border-line-strong hover:text-fg transition-colors"
              >
                Inspect Packet
              </button>
            }
            bodyClassName="p-4 space-y-4"
          >
            {/* Packet Metadata Grid */}
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
              <div className="rounded-xl border border-line bg-surface-2 p-3">
                <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle">
                  Packet Hash
                </div>
                <div className="mt-1 break-all font-mono text-[11px] font-semibold text-fg">
                  {editorialBriefReviewAdapter.packet.packet_hash}
                </div>
              </div>
              <div className="rounded-xl border border-line bg-surface-2 p-3">
                <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle">
                  Source Bridge Task
                </div>
                <div className="mt-1 break-all font-mono text-[11px] font-semibold text-fg">
                  {editorialBriefReviewAdapter.packet.source_bridge_task_label}
                </div>
              </div>
              <div className="rounded-xl border border-line bg-surface-2 p-3">
                <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle">
                  Ingestion Status
                </div>
                <div className="mt-1 break-all text-xs font-semibold text-fg">
                  <span className="font-mono uppercase text-status-review">{editorialBriefReviewAdapter.packet.ingestion_repo_status}</span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {/* Blocked Reasons */}
              <div className="rounded-xl border border-line bg-surface-2 p-3">
                <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-status-blocked">
                  Blocked reasons
                </div>
                <ul className="mt-2 list-inside list-disc text-xs text-fg-muted space-y-1">
                  {editorialBriefReviewAdapter.blockedReasons.map(r => (
                    <li key={r} className="font-mono text-[11px]">{r}</li>
                  ))}
                </ul>
              </div>

              {/* Checklist */}
              <div className="rounded-xl border border-line bg-surface-2 p-3">
                <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle">
                  Operator Checklist
                </div>
                <ul className="mt-2 list-inside list-disc text-xs text-fg-muted space-y-1">
                  {editorialBriefReviewAdapter.checklist.map(c => (
                    <li key={c}>{c}</li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Candidates Table */}
            <div className="border-t border-line pt-3">
              <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle mb-2">
                Candidate review items ({editorialBriefReviewAdapter.packet.candidate_count})
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs min-w-[500px]">
                  <thead>
                    <tr className="border-b border-line bg-surface-2 font-mono text-[10px] text-fg-subtle">
                      <th className="px-2 py-1.5">Candidate ID</th>
                      <th className="px-2 py-1.5">Evidence Role</th>
                      <th className="px-2 py-1.5">Family</th>
                      <th className="px-2 py-1.5">Records</th>
                      <th className="px-2 py-1.5">Next Step</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-line">
                    {editorialBriefReviewAdapter.candidateReviewItems.map((item) => {
                      const active = selected?.kind === 'candidate_review_item' && selected.id === item.candidate_id;
                      return (
                        <tr
                          key={item.candidate_id}
                          id={`candidate-row-${item.candidate_id}`}
                          onClick={() => select(selectCandidateReviewItem(item))}
                          className={`cursor-pointer transition-colors hover:bg-surface-3 ${
                            active ? 'bg-accent/5' : ''
                          }`}
                        >
                          <td className="px-2 py-2 font-mono font-semibold text-fg">
                            {item.candidate_id}
                          </td>
                          <td className="px-2 py-2 text-fg-muted font-mono">{item.evidence_role}</td>
                          <td className="px-2 py-2 text-fg-muted font-mono">{item.source_family}</td>
                          <td className="px-2 py-2 font-mono text-fg">{item.records_count}</td>
                          <td className="px-2 py-2 text-fg-muted font-mono">{item.allowed_next_step}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Safety & Truth Flags Strip */}
            <div className="border-t border-line pt-3 space-y-2">
              <div className="flex flex-wrap items-center gap-1.5 text-[10.5px] font-mono text-fg-subtle">
                <span className="font-bold uppercase mr-1">Safety Flags:</span>
                {Object.entries(editorialBriefReviewAdapter.safetyFlags).map(([key, val]) => (
                  <span key={key} className={`px-1.5 py-0.5 rounded border border-line bg-surface-2 ${val ? 'text-status-blocked' : 'text-status-verified'}`}>
                    {key}: {String(val)}
                  </span>
                ))}
              </div>
              <div className="flex flex-wrap items-center gap-1.5 text-[10.5px] font-mono text-fg-subtle">
                <span className="font-bold uppercase mr-1">Truth Flags:</span>
                {Object.entries(editorialBriefReviewAdapter.protectedTruthFlags).map(([key, val]) => (
                  <span key={key} className={`px-1.5 py-0.5 rounded border border-line bg-surface-2 ${val ? 'text-status-blocked' : 'text-status-verified'}`}>
                    {key}: {String(val)}
                  </span>
                ))}
              </div>
            </div>
          </Panel>

          {/* Content Intent Gate Precheck Panel */}
          <Panel
            title="Content Intent Gate Precheck"
            subtitle="Local intent precheck · blocked until operator review"
            actions={
              <button
                type="button"
                id="btn-inspect-precheck-packet"
                onClick={() => select(selectContentIntentGatePrecheckPacket(contentIntentGatePrecheckAdapter.packet))}
                className="rounded-md border border-line bg-surface-2 px-2.5 py-1 font-mono text-[10.5px] text-fg-muted hover:border-line-strong hover:text-fg transition-colors"
              >
                Inspect Precheck
              </button>
            }
            bodyClassName="p-4 space-y-4"
          >
            {/* Packet Metadata Grid */}
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
              <div className="rounded-xl border border-line bg-surface-2 p-3">
                <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle">
                  Precheck Hash
                </div>
                <div className="mt-1 break-all font-mono text-[11px] font-semibold text-fg">
                  {contentIntentGatePrecheckAdapter.packet.packet_hash}
                </div>
              </div>
              <div className="rounded-xl border border-line bg-surface-2 p-3">
                <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle">
                  Source Brief Hash
                </div>
                <div className="mt-1 break-all font-mono text-[11px] font-semibold text-fg">
                  {contentIntentGatePrecheckAdapter.packet.source_editorial_brief_review_packet_hash}
                </div>
              </div>
              <div className="rounded-xl border border-line bg-surface-2 p-3">
                <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle">
                  Gate Status
                </div>
                <div className="mt-1 break-all text-xs font-semibold text-fg">
                  <span className="font-mono uppercase text-status-blocked">{contentIntentGatePrecheckAdapter.packet.content_intent_gate_status}</span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {/* Blocked Reasons */}
              <div className="rounded-xl border border-line bg-surface-2 p-3">
                <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-status-blocked">
                  Precheck Blocked Reasons
                </div>
                <ul className="mt-2 list-inside list-disc text-xs text-fg-muted space-y-1">
                  {contentIntentGatePrecheckAdapter.blockedReasons.map(r => (
                    <li key={r} className="font-mono text-[11px]">{r}</li>
                  ))}
                </ul>
              </div>

              {/* Next step & Recommended Task */}
              <div className="rounded-xl border border-line bg-surface-2 p-3 space-y-2">
                <div>
                  <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle">
                    Allowed Next Step
                  </div>
                  <div className="mt-1 text-xs text-fg font-medium">
                    {contentIntentGatePrecheckAdapter.packet.allowed_next_step}
                  </div>
                </div>
                <div>
                  <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle">
                    Next Recommended Task
                  </div>
                  <div className="mt-1 font-mono text-[11px] text-fg break-all font-semibold">
                    {contentIntentGatePrecheckAdapter.packet.next_recommended_task}
                  </div>
                </div>
              </div>
            </div>

            {/* Candidate Gate Items Table */}
            <div className="border-t border-line pt-3">
              <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle mb-2">
                Candidate Gate Items ({contentIntentGatePrecheckAdapter.packet.source_candidate_count})
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs min-w-[500px]">
                  <thead>
                    <tr className="border-b border-line bg-surface-2 font-mono text-[10px] text-fg-subtle">
                      <th className="px-2 py-1.5">Candidate ID</th>
                      <th className="px-2 py-1.5">Evidence Role</th>
                      <th className="px-2 py-1.5">Family</th>
                      <th className="px-2 py-1.5">Records</th>
                      <th className="px-2 py-1.5">Precheck Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-line">
                    {contentIntentGatePrecheckAdapter.candidateGateItems.map((item) => {
                      const active = selected?.kind === 'candidate_gate_item' && selected.id === item.candidate_id;
                      const isReady = item.content_intent_gate_status === 'READY_FOR_OPERATOR_INTENT_REVIEW';
                      return (
                        <tr
                          key={item.candidate_id}
                          id={`precheck-candidate-row-${item.candidate_id}`}
                          onClick={() => select(selectCandidateGateItem(item))}
                          className={`cursor-pointer transition-colors hover:bg-surface-3 ${
                            active ? 'bg-accent/5' : ''
                          }`}
                        >
                          <td className="px-2 py-2 font-mono font-semibold text-fg">
                            {item.candidate_id}
                          </td>
                          <td className="px-2 py-2 text-fg-muted font-mono">{item.evidence_role}</td>
                          <td className="px-2 py-2 text-fg-muted font-mono">{item.source_family}</td>
                          <td className="px-2 py-2 font-mono text-fg">{item.records_count}</td>
                          <td className="px-2 py-2 font-mono">
                            <span className={isReady ? 'text-status-review font-semibold' : 'text-status-blocked font-semibold'}>
                              {item.content_intent_gate_status}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Disallowed Outputs strip */}
            <div className="border-t border-line pt-3">
              <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-status-blocked mb-1">
                Disallowed output enforcement (Strict compliance locks)
              </div>
              <div className="flex flex-wrap gap-1.5">
                {contentIntentGatePrecheckAdapter.disallowedOutputs.map((out) => (
                  <span key={out} className="px-1.5 py-0.5 rounded border border-line bg-surface-2 font-mono text-[9.5px] text-fg-muted">
                    {out}
                  </span>
                ))}
              </div>
            </div>

            {/* Safety & Truth Flags Strip */}
            <div className="border-t border-line pt-3 space-y-2">
              <div className="flex flex-wrap items-center gap-1.5 text-[10.5px] font-mono text-fg-subtle">
                <span className="font-bold uppercase mr-1">Safety Flags (verified locked):</span>
                {Object.entries(contentIntentGatePrecheckAdapter.safetyFlags).map(([key, val]) => (
                  <span key={key} className={`px-1.5 py-0.5 rounded border border-line bg-surface-2 ${val ? 'text-status-blocked' : 'text-status-verified font-semibold'}`}>
                    {key}: {String(val)}
                  </span>
                ))}
              </div>
              <div className="flex flex-wrap items-center gap-1.5 text-[10.5px] font-mono text-fg-subtle">
                <span className="font-bold uppercase mr-1">Truth Flags (verified false):</span>
                {Object.entries(contentIntentGatePrecheckAdapter.truthProtectionFlags).map(([key, val]) => (
                  <span key={key} className={`px-1.5 py-0.5 rounded border border-line bg-surface-2 ${val ? 'text-status-blocked' : 'text-status-verified font-semibold'}`}>
                    {key}: {String(val)}
                  </span>
                ))}
              </div>
            </div>
          </Panel>

          {/* Review-Only Content Intent Panel */}
          <Panel
            title="Review-Only Content Intent"
            subtitle="Local intent packet · blocked pending operator input"
            actions={
              <button
                type="button"
                id="btn-inspect-intent-packet"
                onClick={() => select(selectReviewOnlyContentIntentPacket(reviewOnlyContentIntentAdapter.packet))}
                className="rounded-md border border-line bg-surface-2 px-2.5 py-1 font-mono text-[10.5px] text-fg-muted hover:border-line-strong hover:text-fg transition-colors"
              >
                Inspect Intent
              </button>
            }
            bodyClassName="p-4 space-y-4"
          >
            {/* Packet Metadata Grid */}
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
              <div className="rounded-xl border border-line bg-surface-2 p-3">
                <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle">
                  Packet Hash
                </div>
                <div className="mt-1 break-all font-mono text-[11px] font-semibold text-fg">
                  {reviewOnlyContentIntentAdapter.packet.packet_hash}
                </div>
              </div>
              <div className="rounded-xl border border-line bg-surface-2 p-3">
                <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle">
                  Source Precheck Hash
                </div>
                <div className="mt-1 break-all font-mono text-[11px] font-semibold text-fg">
                  {reviewOnlyContentIntentAdapter.packet.source_content_intent_gate_precheck_packet_hash}
                </div>
              </div>
              <div className="rounded-xl border border-line bg-surface-2 p-3">
                <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle">
                  Global Intent Status
                </div>
                <div className="mt-1 break-all text-xs font-semibold text-fg">
                  <span className="font-mono uppercase text-status-blocked">
                    {reviewOnlyContentIntentAdapter.packet.global_intent_packet_status}
                  </span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {/* Blocked Reasons */}
              <div className="rounded-xl border border-line bg-surface-2 p-3">
                <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-status-blocked">
                  Intent Blocked Reasons
                </div>
                <ul className="mt-2 list-inside list-disc text-xs text-fg-muted space-y-1">
                  {reviewOnlyContentIntentAdapter.blockedReasons.map(r => (
                    <li key={r} className="font-mono text-[11px]">{r}</li>
                  ))}
                </ul>
              </div>

              {/* Next step & Recommended Task */}
              <div className="rounded-xl border border-line bg-surface-2 p-3 space-y-2">
                <div>
                  <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle">
                    Allowed Next Step
                  </div>
                  <div className="mt-1 text-xs text-fg font-medium">
                    {reviewOnlyContentIntentAdapter.packet.allowed_next_step}
                  </div>
                </div>
                <div>
                  <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle">
                    Next Recommended Task
                  </div>
                  <div className="mt-1 font-mono text-[11px] text-fg break-all font-semibold">
                    {reviewOnlyContentIntentAdapter.packet.next_recommended_task}
                  </div>
                </div>
              </div>
            </div>

            {/* Required Operator Inputs */}
            <div className="rounded-xl border border-line bg-surface-2 p-3">
              <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-status-review mb-2">
                Required Operator Inputs (Pending Capture)
              </div>
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3 text-xs">
                {Object.entries(reviewOnlyContentIntentAdapter.packet.required_operator_inputs).map(([key, val]) => (
                  <div key={key} className="rounded border border-line bg-surface-1 p-2">
                    <span className="font-mono font-bold text-fg-subtle block">{key}</span>
                    <span className="font-mono font-semibold text-status-review block mt-0.5">{val}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Review-Only Intent Items Table */}
            <div className="border-t border-line pt-3">
              <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle mb-2">
                Review-Only Intent Items ({reviewOnlyContentIntentAdapter.packet.source_candidate_count})
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs min-w-[500px]">
                  <thead>
                    <tr className="border-b border-line bg-surface-2 font-mono text-[10px] text-fg-subtle">
                      <th className="px-2 py-1.5">Candidate ID</th>
                      <th className="px-2 py-1.5">Scope Label</th>
                      <th className="px-2 py-1.5">Evidence Role</th>
                      <th className="px-2 py-1.5">Family</th>
                      <th className="px-2 py-1.5">Records</th>
                      <th className="px-2 py-1.5">Intent Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-line">
                    {reviewOnlyContentIntentAdapter.reviewOnlyIntentItems.map((item) => {
                      const active = selected?.kind === 'review_only_intent_item' && selected.id === item.intent_item_id;
                      const isPending = item.review_only_intent_status === 'REVIEW_ONLY_INTENT_PENDING_OPERATOR_INPUT';
                      return (
                        <tr
                          key={item.intent_item_id}
                          id={`intent-item-row-${item.intent_item_id}`}
                          onClick={() => select(selectReviewOnlyIntentItem(item))}
                          className={`cursor-pointer transition-colors hover:bg-surface-3 ${
                            active ? 'bg-accent/5' : ''
                          }`}
                        >
                          <td className="px-2 py-2 font-mono font-semibold text-fg">
                            {item.source_candidate_id}
                          </td>
                          <td className="px-2 py-2 text-fg-muted font-mono">{item.intent_scope_label}</td>
                          <td className="px-2 py-2 text-fg-muted font-mono">{item.evidence_role}</td>
                          <td className="px-2 py-2 text-fg-muted font-mono">{item.source_family}</td>
                          <td className="px-2 py-2 font-mono text-fg">{item.records_count}</td>
                          <td className="px-2 py-2 font-mono">
                            <span className={isPending ? 'text-status-review font-semibold' : 'text-status-blocked font-semibold'}>
                              {item.review_only_intent_status}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Disallowed Outputs strip */}
            <div className="border-t border-line pt-3">
              <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-status-blocked mb-1">
                Disallowed output enforcement (Strict compliance locks)
              </div>
              <div className="flex flex-wrap gap-1.5">
                {reviewOnlyContentIntentAdapter.disallowedOutputs.map((out) => (
                  <span key={out} className="px-1.5 py-0.5 rounded border border-line bg-surface-2 font-mono text-[9.5px] text-fg-muted">
                    {out}
                  </span>
                ))}
              </div>
            </div>

            {/* Safety & Truth Flags Strip */}
            <div className="border-t border-line pt-3 space-y-2">
              <div className="flex flex-wrap items-center gap-1.5 text-[10.5px] font-mono text-fg-subtle">
                <span className="font-bold uppercase mr-1">Safety Flags (verified locked):</span>
                {Object.entries(reviewOnlyContentIntentAdapter.safetyFlags).map(([key, val]) => (
                  <span key={key} className={`px-1.5 py-0.5 rounded border border-line bg-surface-2 ${val ? 'text-status-blocked' : 'text-status-verified font-semibold'}`}>
                    {key}: {String(val)}
                  </span>
                ))}
              </div>
              <div className="flex flex-wrap items-center gap-1.5 text-[10.5px] font-mono text-fg-subtle">
                <span className="font-bold uppercase mr-1">Truth Flags (verified false):</span>
                {Object.entries(reviewOnlyContentIntentAdapter.truthProtectionFlags).map(([key, val]) => (
                  <span key={key} className={`px-1.5 py-0.5 rounded border border-line bg-surface-2 ${val ? 'text-status-blocked' : 'text-status-verified font-semibold'}`}>
                    {key}: {String(val)}
                  </span>
                ))}
              </div>
            </div>
          </Panel>

          {/* Operator Input Capture Precheck Panel */}
          <Panel
            title="Operator Input Capture Precheck"
            subtitle="Readonly schema-only input surface · capture disabled"
            actions={
              <button
                type="button"
                id="btn-inspect-input-precheck-packet"
                onClick={() => select(selectOperatorInputCapturePrecheckPacket(operatorInputCapturePrecheckAdapter.packet))}
                className="rounded-md border border-line bg-surface-2 px-2.5 py-1 font-mono text-[10.5px] text-fg-muted hover:border-line-strong hover:text-fg transition-colors"
              >
                Inspect Input Precheck
              </button>
            }
            bodyClassName="p-4 space-y-4"
          >
            <div className="rounded-xl border border-status-blocked/30 bg-status-blocked/10 p-3">
              <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-status-blocked">
                Capture Locked
              </div>
              <p className="mt-1 text-xs leading-relaxed text-fg-muted">
                This panel displays required operator input metadata only. No input capture is enabled in this task.
              </p>
            </div>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
              <div className="rounded-xl border border-line bg-surface-2 p-3">
                <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle">
                  Precheck Hash
                </div>
                <div className="mt-1 break-all font-mono text-[11px] font-semibold text-fg">
                  {operatorInputCapturePrecheckAdapter.packet.packet_hash}
                </div>
              </div>
              <div className="rounded-xl border border-line bg-surface-2 p-3">
                <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle">
                  Source Intent Hash
                </div>
                <div className="mt-1 break-all font-mono text-[11px] font-semibold text-fg">
                  {operatorInputCapturePrecheckAdapter.packet.source_review_only_intent_packet_hash}
                </div>
              </div>
              <div className="rounded-xl border border-line bg-surface-2 p-3">
                <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle">
                  Capture Status
                </div>
                <div className="mt-1 break-all text-xs font-semibold text-status-blocked">
                  {operatorInputCapturePrecheckAdapter.packet.global_operator_input_capture_status}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div className="rounded-xl border border-line bg-surface-2 p-3">
                <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-status-blocked">
                  Blocked Reasons
                </div>
                <ul className="mt-2 list-inside list-disc space-y-1 text-xs text-fg-muted">
                  {operatorInputCapturePrecheckAdapter.blockedReasons.map((r) => (
                    <li key={r} className="font-mono text-[11px]">{r}</li>
                  ))}
                </ul>
              </div>

              <div className="rounded-xl border border-line bg-surface-2 p-3 space-y-2">
                <div>
                  <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle">
                    Allowed Next Step
                  </div>
                  <div className="mt-1 text-xs font-medium text-fg">
                    {operatorInputCapturePrecheckAdapter.packet.allowed_next_step}
                  </div>
                </div>
                <div>
                  <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle">
                    Next Recommended Task
                  </div>
                  <div className="mt-1 break-all font-mono text-[11px] font-semibold text-fg">
                    {operatorInputCapturePrecheckAdapter.packet.next_recommended_task}
                  </div>
                </div>
              </div>
            </div>

            <div className="rounded-xl border border-line bg-surface-2 p-3">
              <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-status-review mb-2">
                Required Input Field Policy (Readonly)
              </div>
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3 text-xs">
                {Object.entries(operatorInputCapturePrecheckAdapter.fieldPolicy).map(([key, policy]) => (
                  <div key={key} className="rounded border border-line bg-surface-1 p-2">
                    <span className="block font-mono font-bold text-fg-subtle">{key}</span>
                    <span className="mt-0.5 block font-mono font-semibold text-status-review">{policy.stored_value}</span>
                    <span className="mt-1 block font-mono text-[10px] text-status-blocked">capture_enabled: {String(policy.capture_enabled)}</span>
                    <span className="block font-mono text-[10px] text-status-blocked">editable_in_this_task: {String(policy.editable_in_this_task)}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="border-t border-line pt-3">
              <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle mb-2">
                Input Precheck Items ({operatorInputCapturePrecheckAdapter.packet.source_intent_item_count})
              </div>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[560px] text-left text-xs">
                  <thead>
                    <tr className="border-b border-line bg-surface-2 font-mono text-[10px] text-fg-subtle">
                      <th className="px-2 py-1.5">Candidate ID</th>
                      <th className="px-2 py-1.5">Scope Label</th>
                      <th className="px-2 py-1.5">Family</th>
                      <th className="px-2 py-1.5">Fields</th>
                      <th className="px-2 py-1.5">Precheck Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-line">
                    {operatorInputCapturePrecheckAdapter.inputCapturePrecheckItems.map((item) => {
                      const active = selected?.kind === 'input_capture_precheck_item' && selected.id === item.intent_item_id;
                      return (
                        <tr
                          key={item.intent_item_id}
                          id={`input-precheck-item-row-${item.intent_item_id}`}
                          onClick={() => select(selectInputCapturePrecheckItem(item))}
                          className={`cursor-pointer transition-colors hover:bg-surface-3 ${
                            active ? 'bg-accent/5' : ''
                          }`}
                        >
                          <td className="px-2 py-2 font-mono font-semibold text-fg">
                            {item.source_candidate_id}
                          </td>
                          <td className="px-2 py-2 font-mono text-fg-muted">{item.intent_scope_label}</td>
                          <td className="px-2 py-2 font-mono text-fg-muted">{item.source_family}</td>
                          <td className="px-2 py-2 font-mono text-fg">{item.required_input_fields.length}</td>
                          <td className="px-2 py-2 font-mono font-semibold text-status-review">
                            {item.operator_input_capture_precheck_status}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="border-t border-line pt-3">
              <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-status-blocked mb-1">
                Disallowed output enforcement (Strict compliance locks)
              </div>
              <div className="flex flex-wrap gap-1.5">
                {operatorInputCapturePrecheckAdapter.disallowedOutputs.map((out) => (
                  <span key={out} className="rounded border border-line bg-surface-2 px-1.5 py-0.5 font-mono text-[9.5px] text-fg-muted">
                    {out}
                  </span>
                ))}
              </div>
            </div>

            <div className="border-t border-line pt-3 space-y-2">
              <div className="flex flex-wrap items-center gap-1.5 text-[10.5px] font-mono text-fg-subtle">
                <span className="font-bold uppercase mr-1">Safety Flags (verified locked):</span>
                {Object.entries(operatorInputCapturePrecheckAdapter.safetyFlags).map(([key, val]) => (
                  <span key={key} className={`rounded border border-line bg-surface-2 px-1.5 py-0.5 ${val ? 'text-status-blocked' : 'text-status-verified font-semibold'}`}>
                    {key}: {String(val)}
                  </span>
                ))}
              </div>
              <div className="flex flex-wrap items-center gap-1.5 text-[10.5px] font-mono text-fg-subtle">
                <span className="font-bold uppercase mr-1">Truth Flags (verified false):</span>
                {Object.entries(operatorInputCapturePrecheckAdapter.truthProtectionFlags).map(([key, val]) => (
                  <span key={key} className={`rounded border border-line bg-surface-2 px-1.5 py-0.5 ${val ? 'text-status-blocked' : 'text-status-verified font-semibold'}`}>
                    {key}: {String(val)}
                  </span>
                ))}
              </div>
            </div>
          </Panel>

          {/* Supervised Operator Input Stub Contract Panel */}
          <Panel
            title="Supervised Input Stub Contract"
            subtitle="Readonly supervised input stub · future capture only"
            actions={
              <button
                type="button"
                id="btn-inspect-supervised-input-stub-contract"
                onClick={() => select(selectSupervisedInputStubContractPacket(supervisedInputStubContractAdapter.packet))}
                className="rounded-md border border-line bg-surface-2 px-2.5 py-1 font-mono text-[10.5px] text-fg-muted hover:border-line-strong hover:text-fg transition-colors"
              >
                Inspect Stub Contract
              </button>
            }
            bodyClassName="p-4 space-y-4"
          >
            <div className="rounded-xl border border-status-blocked/30 bg-status-blocked/10 p-3">
              <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-status-blocked">
                Supervised Capture Locked
              </div>
              <p className="mt-1 text-xs leading-relaxed text-fg-muted">
                This panel displays pending supervised input stub slots only. Future capture modes are declared but not enabled here.
              </p>
            </div>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
              <div className="rounded-xl border border-line bg-surface-2 p-3">
                <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle">
                  Stub Packet Hash
                </div>
                <div className="mt-1 break-all font-mono text-[11px] font-semibold text-fg">
                  {supervisedInputStubContractAdapter.packet.packet_hash}
                </div>
              </div>
              <div className="rounded-xl border border-line bg-surface-2 p-3">
                <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle">
                  Source Precheck Hash
                </div>
                <div className="mt-1 break-all font-mono text-[11px] font-semibold text-fg">
                  {supervisedInputStubContractAdapter.packet.source_operator_input_capture_precheck_packet_hash}
                </div>
              </div>
              <div className="rounded-xl border border-line bg-surface-2 p-3">
                <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle">
                  Stub Status
                </div>
                <div className="mt-1 break-all text-xs font-semibold text-status-blocked">
                  {supervisedInputStubContractAdapter.packet.global_supervised_input_stub_status}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div className="rounded-xl border border-line bg-surface-2 p-3">
                <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-status-blocked">
                  Blocked Reasons
                </div>
                <ul className="mt-2 list-inside list-disc space-y-1 text-xs text-fg-muted">
                  {supervisedInputStubContractAdapter.blockedReasons.map((r) => (
                    <li key={r} className="font-mono text-[11px]">{r}</li>
                  ))}
                </ul>
              </div>

              <div className="rounded-xl border border-line bg-surface-2 p-3 space-y-2">
                <div>
                  <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle">
                    Allowed Next Step
                  </div>
                  <div className="mt-1 text-xs font-medium text-fg">
                    {supervisedInputStubContractAdapter.packet.allowed_next_step}
                  </div>
                </div>
                <div>
                  <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle">
                    Next Recommended Task
                  </div>
                  <div className="mt-1 break-all font-mono text-[11px] font-semibold text-fg">
                    {supervisedInputStubContractAdapter.packet.next_recommended_task}
                  </div>
                </div>
              </div>
            </div>

            <div className="rounded-xl border border-line bg-surface-2 p-3">
              <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-status-review mb-2">
                Required Stub Field Policy (Readonly)
              </div>
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3 text-xs">
                {Object.entries(supervisedInputStubContractAdapter.fieldPolicy).map(([key, policy]) => (
                  <div key={key} className="rounded border border-line bg-surface-1 p-2">
                    <span className="block font-mono font-bold text-fg-subtle">{key}</span>
                    <span className="mt-0.5 block font-mono font-semibold text-status-review">{policy.placeholder_value}</span>
                    <span className="mt-1 block font-mono text-[10px] text-status-blocked">current_value: {String(policy.current_value)}</span>
                    <span className="block font-mono text-[10px] text-status-blocked">capture_enabled_in_this_task: {String(policy.capture_enabled_in_this_task)}</span>
                    <span className="block font-mono text-[10px] text-status-blocked">editable_in_this_task: {String(policy.editable_in_this_task)}</span>
                    <span className="block font-mono text-[10px] text-status-blocked">persistence_enabled: {String(policy.persistence_enabled)}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-xl border border-line bg-surface-2 p-3">
              <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle mb-2">
                Allowed Future Capture Modes (Not Enabled Here)
              </div>
              <div className="flex flex-wrap gap-1.5">
                {supervisedInputStubContractAdapter.allowedFutureCaptureModes.map((mode) => (
                  <span key={mode} className="rounded border border-status-review/30 bg-status-review/10 px-1.5 py-0.5 font-mono text-[9.5px] text-status-review">
                    {mode}
                  </span>
                ))}
              </div>
              <div className="mt-2 font-mono text-[10.5px] font-semibold text-status-blocked">
                future_capture_modes_enabled_in_this_task: {String(supervisedInputStubContractAdapter.packet.future_capture_modes_enabled_in_this_task)}
              </div>
            </div>

            <div className="border-t border-line pt-3">
              <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-fg-subtle mb-2">
                Supervised Stub Items ({supervisedInputStubContractAdapter.packet.source_input_capture_precheck_item_count})
              </div>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[620px] text-left text-xs">
                  <thead>
                    <tr className="border-b border-line bg-surface-2 font-mono text-[10px] text-fg-subtle">
                      <th className="px-2 py-1.5">Candidate ID</th>
                      <th className="px-2 py-1.5">Scope Label</th>
                      <th className="px-2 py-1.5">Family</th>
                      <th className="px-2 py-1.5">Fields</th>
                      <th className="px-2 py-1.5">Stub Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-line">
                    {supervisedInputStubContractAdapter.supervisedInputStubItems.map((item) => {
                      const active = selected?.kind === 'supervised_input_stub_item' && selected.id === item.stub_item_id;
                      return (
                        <tr
                          key={item.stub_item_id}
                          id={`supervised-input-stub-row-${item.stub_item_id}`}
                          onClick={() => select(selectSupervisedInputStubItem(item))}
                          className={`cursor-pointer transition-colors hover:bg-surface-3 ${
                            active ? 'bg-accent/5' : ''
                          }`}
                        >
                          <td className="px-2 py-2 font-mono font-semibold text-fg">
                            {item.source_candidate_id}
                          </td>
                          <td className="px-2 py-2 font-mono text-fg-muted">{item.intent_scope_label}</td>
                          <td className="px-2 py-2 font-mono text-fg-muted">{item.source_family}</td>
                          <td className="px-2 py-2 font-mono text-fg">{item.required_input_fields.length}</td>
                          <td className="px-2 py-2 font-mono font-semibold text-status-review">
                            {item.supervised_input_stub_status}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="border-t border-line pt-3">
              <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-status-blocked mb-1">
                Forbidden current actions (Strict no-capture locks)
              </div>
              <div className="flex flex-wrap gap-1.5">
                {supervisedInputStubContractAdapter.forbiddenCurrentActions.map((action) => (
                  <span key={action} className="rounded border border-line bg-surface-2 px-1.5 py-0.5 font-mono text-[9.5px] text-fg-muted">
                    {action}
                  </span>
                ))}
              </div>
            </div>

            <div className="border-t border-line pt-3">
              <div className="font-mono text-[10.5px] font-bold uppercase tracking-wide text-status-blocked mb-1">
                Disallowed output enforcement (Strict compliance locks)
              </div>
              <div className="flex flex-wrap gap-1.5">
                {supervisedInputStubContractAdapter.disallowedOutputs.map((out) => (
                  <span key={out} className="rounded border border-line bg-surface-2 px-1.5 py-0.5 font-mono text-[9.5px] text-fg-muted">
                    {out}
                  </span>
                ))}
              </div>
            </div>

            <div className="border-t border-line pt-3 space-y-2">
              <div className="flex flex-wrap items-center gap-1.5 text-[10.5px] font-mono text-fg-subtle">
                <span className="font-bold uppercase mr-1">Safety Flags (verified locked):</span>
                {Object.entries(supervisedInputStubContractAdapter.safetyFlags).map(([key, val]) => (
                  <span key={key} className={`rounded border border-line bg-surface-2 px-1.5 py-0.5 ${val ? 'text-status-blocked' : 'text-status-verified font-semibold'}`}>
                    {key}: {String(val)}
                  </span>
                ))}
              </div>
              <div className="flex flex-wrap items-center gap-1.5 text-[10.5px] font-mono text-fg-subtle">
                <span className="font-bold uppercase mr-1">Truth Flags (verified false):</span>
                {Object.entries(supervisedInputStubContractAdapter.truthProtectionFlags).map(([key, val]) => (
                  <span key={key} className={`rounded border border-line bg-surface-2 px-1.5 py-0.5 ${val ? 'text-status-blocked' : 'text-status-verified font-semibold'}`}>
                    {key}: {String(val)}
                  </span>
                ))}
              </div>
            </div>
          </Panel>

          <Panel
            title="Draft"
            subtitle="Local working copy · no auto publish"
            actions={<EvidenceChip>{viewModel.content_items[1].evidence_id}</EvidenceChip>}
          >
            {/* Draft Eligibility Gate Strip */}
            <div className="mb-4 rounded-xl border border-line bg-surface-2 p-3 space-y-2">
              <div className="flex items-center justify-between gap-2">
                <span className="font-semibold text-sm text-fg">Draft Eligibility Gate</span>
                <button
                  type="button"
                  id="btn-inspect-draft-eligibility"
                  onClick={() => select(selectDraftEligibilityGatePrecheckPacket(draftEligibilityGatePrecheckAdapter.packet))}
                  className="rounded-md border border-line bg-surface-1 px-2 py-0.5 font-mono text-[10px] text-fg-muted hover:border-line-strong hover:text-fg transition-colors"
                >
                  Inspect Draft Eligibility
                </button>
              </div>
              <div className="flex items-center gap-1.5 text-xs font-semibold">
                <StatusDot status="blocked" />
                <span className="text-status-blocked">Blocked · supervised input required</span>
              </div>
              <div className="flex flex-wrap gap-x-3 gap-y-1 font-mono text-[11px] text-fg-subtle border-t border-line/60 pt-1.5">
                <span>draft_generation_enabled: false</span>
                <span>public_postable: false</span>
                <span className="text-status-review font-semibold">missing_required_input_fields: 6</span>
              </div>

              <details className="group border-t border-line/60 pt-1.5">
                <summary className="cursor-pointer font-mono text-[10.5px] font-semibold text-fg-muted hover:text-fg list-none flex items-center gap-1 select-none">
                  <span className="inline-block transition-transform duration-100 group-open:rotate-90">▶</span>
                  Show Gate Details
                </summary>
                <div className="mt-2 space-y-2 text-xs">
                  <div className="grid grid-cols-[1fr_2.5fr] gap-x-2 gap-y-1 font-mono text-[10.5px]">
                    <div className="text-fg-subtle font-bold uppercase">Packet Status:</div>
                    <div className="text-status-blocked font-semibold uppercase">{draftEligibilityGatePrecheckAdapter.packet.global_draft_eligibility_status}</div>
                    <div className="text-fg-subtle font-bold uppercase">Packet Hash:</div>
                    <div className="text-fg truncate font-semibold">{draftEligibilityGatePrecheckAdapter.packet.packet_hash}</div>
                    <div className="text-fg-subtle font-bold uppercase">Source Stub Hash:</div>
                    <div className="text-fg truncate font-semibold">{draftEligibilityGatePrecheckAdapter.packet.source_supervised_input_stub_packet_hash}</div>
                    <div className="text-fg-subtle font-bold uppercase">Next Task:</div>
                    <div className="text-fg font-semibold break-all">{draftEligibilityGatePrecheckAdapter.packet.next_recommended_task}</div>
                  </div>
                  <div className="border-t border-line/60 pt-2">
                    <div className="font-mono text-[10.5px] font-bold uppercase text-fg-subtle mb-1">
                      Draft Eligibility Items ({draftEligibilityGatePrecheckAdapter.draftEligibilityItems.length})
                    </div>
                    <div className="space-y-1 font-mono text-[10.5px]">
                      {draftEligibilityGatePrecheckAdapter.draftEligibilityItems.map((item) => {
                        const active = selected?.kind === 'draft_eligibility_item' && selected.id === item.draft_eligibility_item_id;
                        return (
                          <div
                            key={item.draft_eligibility_item_id}
                            id={`draft-eligibility-item-row-${item.draft_eligibility_item_id}`}
                            onClick={() => select(selectDraftEligibilityItem(item))}
                            className={`cursor-pointer rounded px-1.5 py-1 border transition-colors ${
                              active
                                ? 'border-accent/40 bg-accent/5 text-fg'
                                : 'border-line bg-surface-1 text-fg-muted hover:bg-surface-3 hover:text-fg'
                            }`}
                          >
                            <div className="flex items-center justify-between font-semibold">
                              <span className="truncate max-w-[14rem]">{item.source_candidate_id}</span>
                              <span className="text-status-blocked">{item.draft_eligibility_status.replace('BLOCKED_DRAFT_ELIGIBILITY_', '')}</span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                  <div className="border-t border-line/60 pt-2 space-y-1.5">
                    <div className="flex flex-wrap items-center gap-1 font-mono text-[9px]">
                      <span className="font-bold uppercase mr-1 text-fg-subtle">Safety:</span>
                      {Object.entries(draftEligibilityGatePrecheckAdapter.safetyFlags).map(([key, val]) => (
                        <span key={key} className={`px-1 rounded border border-line bg-surface-1 ${val ? 'text-status-blocked' : 'text-status-verified font-semibold'}`}>
                          {key}: {String(val)}
                        </span>
                      ))}
                    </div>
                    <div className="flex flex-wrap items-center gap-1 font-mono text-[9px]">
                      <span className="font-bold uppercase mr-1 text-fg-subtle">Truth:</span>
                      {Object.entries(draftEligibilityGatePrecheckAdapter.truthProtectionFlags).map(([key, val]) => (
                        <span key={key} className={`px-1 rounded border border-line bg-surface-1 ${val ? 'text-status-blocked' : 'text-status-verified font-semibold'}`}>
                          {key}: {String(val)}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </details>
            </div>

            <ol className="mb-4 space-y-1.5">
              {d.outline.map((o, i) => (
                <li key={i} className="flex gap-2.5 text-sm text-fg-muted">
                  <span className="font-mono text-[11px] text-fg-subtle">
                    {String(i + 1).padStart(2, '0')}
                  </span>
                  <span>{o}</span>
                </li>
              ))}
            </ol>
            <p className="rounded-lg border border-line bg-surface-2 p-3 text-sm leading-relaxed text-fg-muted">
              {d.body_excerpt}
            </p>
            <div className="mt-3 flex items-start gap-2 rounded-lg border border-status-review/30 bg-status-review/10 p-3">
              <StatusDot status="review" />
              <p className="text-[12px] leading-relaxed text-fg">
                <span className="font-semibold">Limitation note:</span>{' '}
                {d.limitation_note}
              </p>
            </div>
          </Panel>

          {/* AI variants */}
          <Panel
            title={
              <span className="flex items-center gap-2">
                <IconSparkle className="h-4 w-4 text-accent" />
                AI Writer
              </span>
            }
            subtitle="UI-only · draft variants · provider gate closed · human review required"
          >
            <div className="space-y-2">
              {d.ai_outputs.map((v) => {
                const active =
                  selected?.kind === 'ai_variant' && selected.id === v.variant_id;
                return (
                  <button
                    type="button"
                    key={v.variant_id}
                    id={`ai-${v.variant_id}`}
                    onClick={() => select(selectAiVariant(v))}
                    className={`w-full rounded-lg border px-3 py-2.5 text-left transition-colors ${
                      active
                        ? 'border-accent/40 bg-accent/5'
                        : 'border-line bg-surface-2 hover:border-line-strong'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="flex items-center gap-2 text-sm font-medium text-fg">
                        <span className="font-mono text-[11px] text-fg-subtle">
                          {v.variant_id}
                        </span>
                        {v.platform} · {v.style_mode}
                      </span>
                      <StatusChip status={v.guardrail_status}>
                        {v.guardrail_status}
                      </StatusChip>
                    </div>
                    <p className="mt-1 text-[11px] leading-relaxed text-fg-subtle">
                      {v.not_public_postable_reason}
                    </p>
                    <p className="mt-1 font-mono text-[10.5px] text-status-blocked">
                      publish_ready: false
                    </p>
                  </button>
                );
              })}
            </div>
          </Panel>
        </div>

        {/* Right: guardrails, SEO, media */}
        <div className="space-y-6">
          {/* Compact media quick-access — keeps the Media Tray reachable in the
              first fold at 1440x900. Mock/local assets only: no upload, no file
              picker, no media API. Selecting a chip routes to the inspector. */}
          <Panel
            title={
              <span className="flex items-center gap-2">
                <IconImage className="h-4 w-4 text-fg-subtle" />
                Media Tray
              </span>
            }
            subtitle="Mock only · local assets · no upload, no file picker, no media API"
            actions={
              <span className="rounded-md border border-line bg-surface-2 px-1.5 py-0.5 font-mono text-[10.5px] text-fg-muted">
                {d.media.length} mock
              </span>
            }
            bodyClassName="p-3"
          >
            <div className="flex flex-wrap gap-1.5">
              {d.media.map((m) => {
                const active =
                  selected?.kind === 'media_asset' && selected.id === m.id;
                return (
                  <button
                    type="button"
                    key={m.id}
                    id={`media-chip-${m.id}`}
                    onClick={() => select(selectMediaAsset(m))}
                    className={`flex items-center gap-2 rounded-full border px-2.5 py-1 text-[11px] font-medium transition-colors ${
                      active
                        ? 'border-accent/40 bg-accent/5 text-fg'
                        : 'border-line bg-surface-2 text-fg-muted hover:border-line-strong hover:text-fg'
                    }`}
                  >
                    <IconImage className="h-3.5 w-3.5 shrink-0 text-fg-subtle" />
                    <span className="max-w-[10rem] truncate font-mono">
                      {m.name}
                    </span>
                    <StatusDot status={m.rights_status} />
                  </button>
                );
              })}
            </div>
          </Panel>

          <Panel title="Guardrails &amp; claim risk" bodyClassName="p-4 space-y-4">
            <div>
              <SectionLabel>Guardrails</SectionLabel>
              <ul className="space-y-1.5">
                {d.guardrails.map((g) => (
                  <li
                    key={g.id}
                    className="flex items-center justify-between gap-2 text-sm"
                  >
                    <span className="flex items-center gap-2 text-fg-muted">
                      <StatusDot status={g.status} />
                      {g.label}
                    </span>
                    <StatusChip status={g.status}>{g.status}</StatusChip>
                  </li>
                ))}
              </ul>
            </div>
            <div className="border-t border-line pt-3">
              <SectionLabel>Claim risks</SectionLabel>
              <ul className="space-y-1.5">
                {d.claim_risks.map((c) => (
                  <li
                    key={c.id}
                    className="flex items-center gap-2 text-[12px] text-fg-muted"
                  >
                    <StatusDot status={c.severity} />
                    {c.label}
                  </li>
                ))}
              </ul>
            </div>
            <div className="border-t border-line pt-3">
              <SectionLabel>Citations</SectionLabel>
              <ul className="space-y-1.5">
                {d.citations.map((c) => (
                  <li
                    key={c.id}
                    className="flex items-center justify-between gap-2 text-[12px]"
                  >
                    <span className="text-fg-muted">{c.label}</span>
                    <StatusChip status={c.status}>{c.status}</StatusChip>
                  </li>
                ))}
              </ul>
            </div>
          </Panel>

          <Panel
            title="SEO &amp; Editorial Score"
            subtitle="Advisory only · not a publish gate"
          >
            <div className="space-y-3">
              <Score label="Editorial" value={d.seo.editorial_score} />
              <Score label="SEO" value={d.seo.seo_score} />
              <Score label="Platform fit" value={d.seo.platform_fit_score} />
            </div>
            <div className="mt-4 border-t border-line pt-3">
              <SectionLabel>Keywords</SectionLabel>
              <div className="flex flex-wrap gap-1.5">
                {d.seo.keywords.map((k) => (
                  <span
                    key={k}
                    className="rounded-md border border-line bg-surface-2 px-1.5 py-0.5 text-[11px] text-fg-muted"
                  >
                    {k}
                  </span>
                ))}
              </div>
            </div>
            <p className="mt-3 font-mono text-[11px] text-fg-subtle">
              Readability: {d.seo.readability}
            </p>
          </Panel>
        </div>
      </div>
    </div>
  );
}

function Score({ label, value }: { label: string; value: number }) {
  const status: StatusKind =
    value >= 80 ? 'verified' : value >= 60 ? 'review' : 'blocked';
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-[12px]">
        <span className="text-fg-muted">{label}</span>
        <span className="font-mono font-semibold text-fg">{value}</span>
      </div>
      <ScoreBar value={value} status={status} />
    </div>
  );
}
