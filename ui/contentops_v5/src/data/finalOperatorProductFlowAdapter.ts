// V6 final operator flow adapter.
// Deterministic local builder only: no network, browser, provider, env, credential, scrape, fetch, or media download.

import type {
  StatusKind,
  V6FinalOperatorProductFlowModel,
  V6InternalChartCandidate,
  V6ManualAuditRow,
  V6NewsImageCandidate,
  V6OperatorApprovalDecisionPacket,
  V6OperatorFlowStage,
  V6PlatformUniverseRow,
} from '../types';

const TASK_LABEL = 'TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_DECISION_PACKET_INTAKE_V0';

function stableHash(input: string): string {
  let hash = 0x811c9dc5;
  for (let i = 0; i < input.length; i += 1) {
    hash ^= input.charCodeAt(i);
    hash = Math.imul(hash, 0x01000193) >>> 0;
  }
  return hash.toString(16).padStart(8, '0');
}

const payloadHash = (platformId: string, variantKey: string, copyMode: string) =>
  `local-${stableHash(`${platformId}|${variantKey}|${copyMode}`)}-${stableHash(TASK_LABEL)}`;

const platform = (
  platform_id: string,
  platformName: string,
  role: string,
  posture: string,
  status: StatusKind,
  manual_action: string,
  variant_key: string,
  copy_mode: string,
  media_fit: string,
  audit_evidence_mode: string,
  dispatch_gate: V6PlatformUniverseRow['dispatch_gate'],
): V6PlatformUniverseRow => ({
  platform_id,
  platform: platformName,
  role,
  posture,
  status,
  manual_action,
  variant_key,
  payload_hash: payloadHash(platform_id, variant_key, copy_mode),
  copy_mode,
  media_fit,
  audit_evidence_mode,
  dispatch_gate,
});

const flowStages: V6OperatorFlowStage[] = [
  { stage_id: 'source', label: 'Source intake', status: 'review', summary: 'Jim selects news/current-event or Capital Chronicle internal report source class.', evidence_ref: 'source_class=operator_selected' },
  { stage_id: 'draft', label: 'Canonical draft', status: 'review', summary: 'Local canonical Substack-style draft preview remains review-only.', evidence_ref: 'draft_preview_hash=local_adapter' },
  { stage_id: 'approval', label: 'Hash approval', status: 'review', summary: 'Operator-supplied approve/hold/reject packets bind to exact adapter payload hashes.', evidence_ref: 'operator_decision_intake=local_fixture_only' },
  { stage_id: 'variants', label: 'Platform variants', status: 'review', summary: 'Full platform universe gets deterministic platform-fit rows before manual export.', evidence_ref: 'variants=local_builder_output' },
  { stage_id: 'media', label: 'Media selection', status: 'review', summary: 'News uses grounded metadata candidates; internal reports use built-in chart/card candidates.', evidence_ref: 'media_search_or_download_performed=false' },
  { stage_id: 'audit', label: 'Manual dispatch / audit', status: 'blocked', summary: 'Manual handoff and redacted audit rows are shown; live dispatch remains locked.', evidence_ref: 'live_write_allowed=false' },
];

const platformUniverse = [
  platform('substack', 'Substack', 'Canonical long-form authority', 'Manual export / operator evidence', 'review', 'Copy reviewed canonical article after Jim approval.', 'substack_canonical_preview', 'long_form_article', 'Use internal chart for report posts; metadata-only official image candidate for news posts.', 'operator_supplied_url_metrics_only', 'manual_review_only'),
  platform('linkedin', 'LinkedIn', 'Professional distribution lane', 'Manual publication evidence accepted', 'review', 'Paste approved variant manually; record operator-supplied URL/metrics.', 'linkedin_professional_preview', 'professional_summary', 'Prefer 1200x627 report card or official-source news visual metadata.', 'operator_supplied_url_metrics_only', 'manual_review_only'),
  platform('x', 'X', 'Real-time market commentary lane', 'Manual/deferred plus local registry evidence', 'review', 'Use exact reviewed payload only; registry accepts operator-supplied outcome rows.', 'x_manual_preview', 'short_market_commentary', 'Square report card or metadata-only news thumbnail; no auto-upload.', 'local_registry_operator_supplied_only', 'manual_review_only'),
  platform('discord', 'Discord', 'Community feedback flywheel', 'Pre-live dry-run/outbox governance', 'blocked', 'Keep as preview/outbox evidence until live scope is separately approved.', 'discord_drop_preview', 'community_prompt', 'Media optional; cite source packet instead of upload automation.', 'dry_run_outbox_only', 'blocked_live_scope_required'),
  platform('telegram', 'Telegram', 'Remote operator lane', 'Checkpoint/manual remote lane', 'blocked', 'Use checkpoint packet only; no bot/API send.', 'telegram_operator_preview', 'operator_checkpoint', 'Text-first; include media manifest reference only.', 'checkpoint_packet_only', 'blocked_live_scope_required'),
  platform('facebook', 'Facebook Page', 'Meta-family page distribution lane', 'Advisory/manual Meta Business Suite first', 'blocked', 'Prepare copy/media fit notes; live/API posting blocked.', 'facebook_page_preview', 'page_post', '1200x627 report card or reviewed news metadata candidate.', 'manual_future_evidence_only', 'blocked_deferred'),
  platform('threads', 'Threads', 'Meta-family short-form conversation lane', 'Advisory/manual recovery notes', 'blocked', 'Prepare concise variant; API/live posting blocked.', 'threads_preview', 'short_conversation', 'Square report card fits; no upload readiness claim.', 'manual_future_evidence_only', 'blocked_deferred'),
  platform('instagram', 'Instagram', 'Visual/social media lane', 'Deferred until rights and account constraints clear', 'blocked', 'Review media fit only; no upload readiness claim.', 'instagram_caption_preview', 'visual_caption', 'Built-in square card required for internal reports; news external image remains metadata-only.', 'manual_future_evidence_only', 'blocked_deferred'),
  platform('tiktok', 'TikTok', 'High-friction short-video lane', 'Last-priority future lane', 'blocked', 'Capture video-script direction only; no current execution.', 'tiktok_metadata_deferred_preview', 'video_script_outline', 'Requires future video asset spec; current row is text/script only.', 'manual_future_evidence_only', 'blocked_deferred'),
  platform('generic_manual', 'Generic Manual', 'Operator-controlled fallback lane', 'Manual copy/export evidence only', 'review', 'Use when a platform-specific lane is not productized.', 'generic_manual_preview', 'manual_copy_block', 'Operator chooses already-reviewed candidate; no external fetch.', 'operator_supplied_url_metrics_only', 'manual_review_only'),
] as const satisfies V6PlatformUniverseRow[];

const newsCandidate = (
  candidate_id: string,
  title: string,
  search_query: string,
  source_url_metadata: string,
  image_url_metadata: string,
  selected_for_platforms: string[],
  license_notes: string,
  relevance_notes: string,
  rights_status: StatusKind,
): V6NewsImageCandidate => ({
  candidate_id,
  source_class: 'news_current_event',
  title,
  search_query,
  source_url_metadata,
  image_url_metadata,
  metadata_hash: payloadHash('news_media', candidate_id, search_query),
  selected_for_platforms,
  license_notes,
  relevance_notes,
  public_fetch_performed: false,
  download_performed: false,
  rights_status,
});

const chartCandidate = (
  chart_id: string,
  title: string,
  source_report: string,
  format: string,
  selected_for_platforms: string[],
  fit_notes: string,
  alt_text: string,
): V6InternalChartCandidate => ({
  chart_id,
  source_class: 'capital_chronicle_internal_report',
  title,
  source_report,
  format,
  media_hash: payloadHash('internal_chart', chart_id, format),
  selected_for_platforms,
  fit_notes,
  alt_text,
  external_image_needed: false,
  rights_status: 'verified',
});

const decisionStatus = (decision: V6OperatorApprovalDecisionPacket['decision']): StatusKind => {
  if (decision === 'approve') return 'verified';
  if (decision === 'hold') return 'review';
  return 'blocked';
};

const nextAction = (decision: V6OperatorApprovalDecisionPacket['decision']) => {
  if (decision === 'approve') return 'Manual export/audit evidence may proceed after final operator handoff; dispatch stays locked.';
  if (decision === 'hold') return 'Resolve operator notes and resubmit the same payload hash or a new reviewed hash.';
  return 'Do not use this payload; regenerate or archive the variant after operator review.';
};

const decisionPacket = (
  row: V6PlatformUniverseRow,
  decision: V6OperatorApprovalDecisionPacket['decision'],
  operator_reference: string,
  rationale: string,
): V6OperatorApprovalDecisionPacket => {
  const decision_packet_id = `decision_${row.platform_id}_${stableHash(`${row.payload_hash}|${decision}|${operator_reference}`)}`;
  return {
    decision_packet_id,
    platform_id: row.platform_id,
    platform: row.platform,
    source_variant_key: row.variant_key,
    payload_hash: row.payload_hash,
    decision,
    decision_status: decisionStatus(decision),
    operator_evidence_mode: 'operator_supplied_fixture',
    operator_reference,
    rationale,
    next_required_action: nextAction(decision),
    decision_packet_hash: payloadHash('operator_decision', decision_packet_id, row.payload_hash),
    approval_recorded: decision === 'approve',
    dispatch_permission_granted: false,
    live_write_allowed: false,
    public_url_fetch_made: false,
    provider_or_api_call_made: false,
    browser_or_cdp_used: false,
  };
};

const decisionPackets = [
  decisionPacket(platformUniverse[0], 'approve', 'jim-local-fixture-approval-001', 'Canonical Substack payload approved for manual export evidence only.'),
  decisionPacket(platformUniverse[2], 'hold', 'jim-local-fixture-hold-001', 'X wording needs another operator pass before any manual copy.'),
  decisionPacket(platformUniverse[7], 'reject', 'jim-local-fixture-reject-001', 'Instagram lane is rejected until rights/account constraints are solved.'),
] as const satisfies V6OperatorApprovalDecisionPacket[];

const auditRow = (row: V6PlatformUniverseRow): V6ManualAuditRow => {
  const decision = decisionPackets.find((packet) => packet.payload_hash === row.payload_hash);
  return {
    row_id: `audit_${row.platform_id}`,
    platform: row.platform,
    source_variant_key: row.variant_key,
    payload_hash: row.payload_hash,
    approval_recorded: decision?.approval_recorded ?? false,
    decision_packet_id: decision?.decision_packet_id,
    decision: decision?.decision,
    public_url_status: row.dispatch_gate === 'manual_review_only' ? 'operator_supplied_only' : 'not_applicable_until_manual_post',
    metrics_status: row.dispatch_gate === 'manual_review_only' ? 'operator_supplied_only' : 'not_applicable_until_manual_post',
    evidence_mode: row.audit_evidence_mode,
    live_dispatch_performed: false,
    status: decision?.decision_status ?? row.status,
  };
};

const newsCandidates = [
  newsCandidate('IMG-CAND-001', 'Official CPI release visual context', 'CPI release official chart visual context site:bls.gov', 'https://www.bls.gov/news.release/cpi.htm (operator/search metadata only)', 'metadata-only://official-release-thumbnail', ['Substack', 'LinkedIn', 'X', 'Facebook Page'], 'Operator must confirm official-source reuse terms before manual use.', 'Best fit for CPI news hook; supports data-sufficiency framing.', 'review'),
  newsCandidate('IMG-CAND-002', 'Central-bank inflation explainer image', 'central bank inflation explainer image official source', 'https://example-public-institution.invalid/inflation-explainer (fixture metadata)', 'metadata-only://institutional-inflation-card', ['LinkedIn', 'Threads'], 'Fixture candidate; rights not verified.', 'Educational visual fallback if official visual is not approved.', 'blocked'),
] as const satisfies V6NewsImageCandidate[];

const internalChartCandidates = [
  chartCandidate('CHART-ALPHA-001', 'Internal alpha dispersion card', 'Capital Chronicle Internal alpha macro brief', 'built-in 1200x627 card', ['Substack', 'LinkedIn', 'Facebook Page'], 'Primary fit for LinkedIn/Substack; crop notes required for Instagram.', 'Internal chart card showing redacted macro dispersion bands.'),
  chartCandidate('CHART-ALPHA-002', 'Forecast-readiness checklist card', 'Capital Chronicle Internal alpha macro brief', 'built-in square card', ['X', 'Threads', 'Instagram'], 'Primary fit for Threads/Instagram/X image preview.', 'Checklist card explaining why the report is context, not a signal.'),
] as const satisfies V6InternalChartCandidate[];

export const finalOperatorProductFlow: V6FinalOperatorProductFlowModel = {
  packet_id: `final_operator_flow_${stableHash(TASK_LABEL + platformUniverse.length)}`,
  packet_hash: payloadHash('final_operator_flow', TASK_LABEL, `${platformUniverse.length}|${newsCandidates.length}|${internalChartCandidates.length}|${decisionPackets.length}`),
  builder_version: 'operator_approval_decision_packet_intake_v0',
  task_label: TASK_LABEL,
  source_classes: ['news_current_event', 'capital_chronicle_internal_report'],
  flow_stages: flowStages,
  platform_universe: [...platformUniverse],
  media_lane: {
    news_topic_id: 'GN-0042',
    news_policy: 'Grounded image candidates are metadata-only. No Google scraping, public URL fetch, image download, or rights verification is performed.',
    news_candidates: [...newsCandidates],
    internal_report_id: 'CC-ALPHA-REPORT-0009',
    internal_policy: 'Capital Chronicle internal alpha/report posts prefer built-in chart/card media from the report system.',
    internal_chart_candidates: [...internalChartCandidates],
    forbidden_actions: ['google_scrape', 'image_download', 'public_url_fetch', 'rights_verification_claim', 'platform_upload'],
  },
  operator_decision_intake_lane: {
    intake_status: 'review',
    intake_summary: 'Local approve/hold/reject packets are operator-supplied fixture evidence bound to exact adapter payload hashes.',
    evidence_policy: 'Approve means manual-review evidence only. It does not grant dispatch, public URL verification, scheduler, API, browser/CDP, provider, or live-write permission.',
    decision_packets: [...decisionPackets],
    forbidden_actions: ['dispatch', 'publish', 'schedule', 'execute outbox', 'verify public URL', 'call provider/API', 'use browser/CDP', 'read credentials'],
  },
  manual_audit_lane: {
    approval_status: 'review',
    approval_summary: 'Operator decision packets may be displayed only when supplied and hash-bound; they never synthesize dispatch permission.',
    dispatch_status: 'blocked',
    dispatch_summary: 'Manual copy/export only; no platform/API/browser execution path exists.',
    audit_summary: 'Audit accepts operator-supplied public URL/metrics only and labels them manual evidence.',
    audit_rows: platformUniverse.map(auditRow),
    locked_actions: ['publish', 'dispatch', 'schedule', 'verify public URL', 'scrape', 'download media', 'read credentials'],
  },
};
