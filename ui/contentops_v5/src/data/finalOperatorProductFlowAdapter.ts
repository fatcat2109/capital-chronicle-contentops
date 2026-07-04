// V6 final operator flow adapter.
// Deterministic local builder only: no network, browser, provider, env, credential, scrape, fetch, or media download.

import type {
  StatusKind,
  V6FinalOperatorActionStripRow,
  V6FinalOperatorProductFlowModel,
  V6InternalChartCandidate,
  V6LocalOutboxReadinessLaneModel,
  V6LocalOutboxReadinessRow,
  V6LocalOutboxReadinessState,
  V6ManualAuditRow,
  V6ManualDeferredDistributionRow,
  V6NewsImageCandidate,
  V6OperatorApprovalDecisionPacket,
  V6OperatorBridgeStatusRow,
  V6OperatorFlowStage,
  V6PlatformUniverseRow,
} from '../types';

const TASK_LABEL = 'TASK_CONTENTOPS_V6_FINAL_OPERATOR_HANDOFF_AND_NEXT_ACTION_STRIP_HARDENING_V0';

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
  { stage_id: 'readiness', label: 'Outbox readiness', status: 'review', summary: 'Decision packets reconcile into local manual-readiness rows without executable outboxes.', evidence_ref: 'outbox_dispatchable=false' },
  { stage_id: 'variants', label: 'Platform variants', status: 'review', summary: 'Full platform universe gets deterministic platform-fit rows before manual export.', evidence_ref: 'variants=local_builder_output' },
  { stage_id: 'media', label: 'Media selection', status: 'review', summary: 'News uses grounded metadata candidates; internal reports use built-in chart/card candidates.', evidence_ref: 'media_search_or_download_performed=false' },
  { stage_id: 'bridge', label: 'Discord/Telegram bridge', status: 'blocked', summary: 'Discord and Telegram evidence is consolidated as local-only operator bridge status with no send path.', evidence_ref: 'operator_bridge_send_attempted=false' },
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

const readinessState = (
  row: V6PlatformUniverseRow,
  decision?: V6OperatorApprovalDecisionPacket,
): V6LocalOutboxReadinessState => {
  if (decision?.decision === 'approve' && row.dispatch_gate === 'manual_review_only') return 'approved_manual_ready';
  if (decision?.decision === 'hold') return 'held_for_revision';
  if (decision?.decision === 'reject') return 'rejected_blocked';
  if (row.dispatch_gate !== 'manual_review_only') return 'blocked_live_scope_required';
  return 'blocked_no_decision';
};

const readinessStatus = (state: V6LocalOutboxReadinessState): StatusKind => {
  if (state === 'approved_manual_ready') return 'verified';
  if (state === 'held_for_revision' || state === 'blocked_no_decision') return 'review';
  return 'blocked';
};

const readinessNextAction = (state: V6LocalOutboxReadinessState): string => {
  if (state === 'approved_manual_ready') return 'Manual export evidence may be prepared by operator; no executable outbox exists.';
  if (state === 'held_for_revision') return 'Revise or re-review the exact payload hash before manual export evidence.';
  if (state === 'rejected_blocked') return 'Keep this payload blocked; regenerate or archive after operator review.';
  if (state === 'blocked_live_scope_required') return 'Future explicit live/platform scope is required before this lane can progress.';
  return 'Collect an operator approve/hold/reject packet bound to this payload hash.';
};

const readinessRow = (row: V6PlatformUniverseRow): V6LocalOutboxReadinessRow => {
  const decision = decisionPackets.find((packet) => packet.payload_hash === row.payload_hash);
  const state = readinessState(row, decision);
  return {
    row_id: `readiness_${row.platform_id}`,
    platform_id: row.platform_id,
    platform: row.platform,
    source_variant_key: row.variant_key,
    payload_hash: row.payload_hash,
    decision: decision?.decision,
    decision_packet_id: decision?.decision_packet_id,
    decision_packet_hash: decision?.decision_packet_hash,
    readiness_state: state,
    readiness_status: readinessStatus(state),
    manual_next_action: readinessNextAction(state),
    outbox_entry_created: false,
    outbox_dispatchable: false,
    dispatch_allowed_now: false,
    live_write_allowed_now: false,
    scheduler_or_retry_wired: false,
    public_url_fetch_made: false,
    provider_or_api_call_made: false,
    browser_or_cdp_used: false,
    approval_ledger_live_write_made: false,
  };
};

const readinessRows = platformUniverse.map(readinessRow);

const readinessCounts = readinessRows.reduce<V6LocalOutboxReadinessLaneModel['counts']>((counts, row) => {
  counts.total += 1;
  counts[row.readiness_state] += 1;
  if (row.outbox_dispatchable) counts.dispatchable += 1;
  return counts;
}, {
  approved_manual_ready: 0,
  held_for_revision: 0,
  rejected_blocked: 0,
  blocked_no_decision: 0,
  blocked_live_scope_required: 0,
  total: 0,
  dispatchable: 0,
});

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

const bridgeRows = [
  {
    bridge_id: 'bridge_discord_dry_run_operator_status',
    platform_id: 'discord',
    platform: 'Discord',
    source_evidence: 'discord dry-run/outbox/governance packets already exist locally; no live send is claimed',
    operator_surface: 'community feedback flywheel preview',
    bridge_state: 'dry_run_proven_no_send',
    status: 'blocked',
    payload_hash: platformUniverse[3].payload_hash,
    manual_handoff: 'Operator may copy the reviewed Discord drop manually outside repo after Jim approval; repo must not send or validate webhook.',
    redacted_status: 'webhook/token/url redacted and unread; send_attempted=false',
    message_send_attempted: false,
    platform_api_called: false,
    webhook_or_bot_token_read: false,
    browser_or_cdp_used: false,
    public_url_fetch_made: false,
    scheduler_or_retry_wired: false,
    live_approval_ledger_written: false,
  },
  {
    bridge_id: 'bridge_telegram_checkpoint_operator_status',
    platform_id: 'telegram',
    platform: 'Telegram',
    source_evidence: 'telegram checkpoint/manual remote lane exists as operator handoff evidence only',
    operator_surface: 'remote operator checkpoint preview',
    bridge_state: 'checkpoint_manual_only',
    status: 'blocked',
    payload_hash: platformUniverse[4].payload_hash,
    manual_handoff: 'Operator may copy the checkpoint text manually outside repo; repo must not use bot API, channel ID, token, browser, or scheduler.',
    redacted_status: 'bot token/channel secret unread; api_called=false',
    message_send_attempted: false,
    platform_api_called: false,
    webhook_or_bot_token_read: false,
    browser_or_cdp_used: false,
    public_url_fetch_made: false,
    scheduler_or_retry_wired: false,
    live_approval_ledger_written: false,
  },
] as const satisfies V6OperatorBridgeStatusRow[];

const manualDeferredRow = (
  row: V6PlatformUniverseRow,
  platform_id: V6ManualDeferredDistributionRow['platform_id'],
  readiness_state: V6ManualDeferredDistributionRow['readiness_state'],
  blocker_summary: string,
  manual_handoff: string,
  media_requirement: string,
): V6ManualDeferredDistributionRow => ({
  lane_id: `manual_deferred_${platform_id}`,
  platform_id,
  platform: row.platform,
  readiness_state,
  status: row.status,
  payload_hash: row.payload_hash,
  source_variant_key: row.variant_key,
  blocker_summary,
  manual_handoff,
  media_requirement,
  audit_evidence_mode: row.audit_evidence_mode,
  live_write_allowed: false,
  platform_api_called: false,
  browser_or_cdp_used: false,
  public_url_fetch_made: false,
  media_download_or_upload_performed: false,
  scheduler_or_retry_wired: false,
  credential_or_env_read: false,
  approval_ledger_live_write_made: false,
});

const manualDeferredRows = [
  manualDeferredRow(platformUniverse[5], 'facebook', 'manual_handoff_only', 'Meta-family Facebook Page lane is advisory/manual only; Page/API posting and live edits are blocked.', 'Prepare reviewed copy and media-fit notes for Meta Business Suite manual paste outside repo.', 'Use a reviewed 1200x627 internal report card or operator-approved metadata-only news candidate; no upload performed.'),
  manualDeferredRow(platformUniverse[6], 'threads', 'manual_handoff_only', 'Threads lane is short-form manual copy only; platform API, browser posting, replies, and reactions are blocked.', 'Prepare concise reviewed copy for operator paste outside repo after Jim approval.', 'Square card may be referenced when already reviewed; no media upload readiness is claimed.'),
  manualDeferredRow(platformUniverse[7], 'instagram', 'blocked_deferred', 'Instagram is deferred because media rights, account constraints, and upload path are not cleared.', 'Do not post. Keep caption/media-fit notes for future operator-owned review.', 'Requires an internal square card or approved visual asset; external news image remains metadata-only.'),
  manualDeferredRow(platformUniverse[8], 'tiktok', 'blocked_deferred', 'TikTok is last-priority video-script metadata only; no video asset, upload, account, or live execution path exists.', 'Keep the script outline as planning metadata; operator must create/post outside repo in a future approved scope.', 'Requires a future video asset spec; current lane contains text/script direction only.'),
  manualDeferredRow(platformUniverse[9], 'generic_manual', 'fallback_manual_only', 'Generic Manual is an operator fallback; it does not imply provider capability for any specific platform.', 'Use only for copy/export evidence when a platform-specific lane is not productized.', 'Operator chooses an already-reviewed candidate; no external fetch, download, upload, or verification.'),
] as const satisfies V6ManualDeferredDistributionRow[];

const actionStripRow = (
  action_id: string,
  label: string,
  source_lanes: string[],
  status: StatusKind,
  next_action: string,
  evidence_summary: string,
  payload_refs: string[],
): V6FinalOperatorActionStripRow => ({
  action_id,
  label,
  source_lanes,
  status,
  next_action,
  evidence_summary,
  payload_refs,
  operator_owned: true,
  live_write_allowed: false,
  dispatch_allowed: false,
  platform_api_allowed: false,
  browser_or_cdp_allowed: false,
  public_url_fetch_allowed: false,
  media_download_or_upload_allowed: false,
  scheduler_or_retry_allowed: false,
  credential_or_env_read_allowed: false,
  approval_ledger_live_write_allowed: false,
});

const finalOperatorActionStripRows = [
  actionStripRow(
    'action_strip_approved_manual_export',
    'Approved manual export evidence',
    ['operator_decision_intake_lane', 'local_outbox_readiness_lane', 'manual_audit_lane'],
    'verified',
    'Jim may use the approved Substack payload hash for operator-owned manual export evidence; repo dispatch stays locked.',
    'One approve packet reconciles to approved_manual_ready and manual audit evidence without creating an executable outbox.',
    [platformUniverse[0].payload_hash, decisionPackets[0].decision_packet_hash],
  ),
  actionStripRow(
    'action_strip_revision_or_reject_queue',
    'Hold/reject queue',
    ['operator_decision_intake_lane', 'local_outbox_readiness_lane'],
    'review',
    'Revise the held X payload and keep the rejected Instagram payload blocked until Jim supplies a new decision packet.',
    'Held and rejected hashes are visible beside their decision packet hashes so operators cannot confuse them with approved payloads.',
    [platformUniverse[2].payload_hash, platformUniverse[7].payload_hash],
  ),
  actionStripRow(
    'action_strip_bridge_status_handoff',
    'Discord/Telegram bridge status handoff',
    ['operator_bridge_lane'],
    'blocked',
    'Use Discord/Telegram bridge rows as redacted status only; any message send remains outside repo and future scoped.',
    'Bridge rows prove dry-run/checkpoint status while message_send_attempted, token reads, API calls, browser/CDP, schedulers, and ledger writes remain false.',
    bridgeRows.map((row) => row.payload_hash),
  ),
  actionStripRow(
    'action_strip_deferred_social_lanes',
    'Deferred social/manual lane handoff',
    ['manual_deferred_distribution_lane'],
    'blocked',
    'Keep Facebook Page, Threads, Instagram, TikTok, and Generic Manual rows as local handoff/status evidence only.',
    'Manual/deferred rows expose blockers, media requirements, audit modes, and explicit false execution flags for every deferred lane.',
    manualDeferredRows.map((row) => row.payload_hash),
  ),
  actionStripRow(
    'action_strip_locked_execution_flags',
    'Global locked execution flags',
    ['media_lane', 'operator_decision_intake_lane', 'local_outbox_readiness_lane', 'manual_audit_lane'],
    'blocked',
    'Do not post, edit, comment, DM, react, fetch public URLs, use browser/CDP, call APIs, download/upload media, schedule/retry, read credentials/env/session, or write live ledgers.',
    'All consolidated rows repeat blocked flags so the final strip cannot be mistaken for a live automation surface.',
    [payloadHash('final_action_strip', 'locked_execution_flags', TASK_LABEL)],
  ),
] as const satisfies V6FinalOperatorActionStripRow[];

export const finalOperatorProductFlow: V6FinalOperatorProductFlowModel = {
  packet_id: `final_operator_flow_${stableHash(TASK_LABEL + platformUniverse.length)}`,
  packet_hash: payloadHash('final_operator_flow', TASK_LABEL, `${platformUniverse.length}|${newsCandidates.length}|${internalChartCandidates.length}|${decisionPackets.length}|${readinessRows.length}|${bridgeRows.length}|${manualDeferredRows.length}|${finalOperatorActionStripRows.length}`),
  builder_version: 'final_operator_action_strip_hardening_v0',
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
  local_outbox_readiness_lane: {
    lane_status: 'review',
    reconciliation_summary: 'Operator decision packets are reconciled into local manual-readiness rows. No executable outbox is created.',
    safety_policy: 'Readiness is review evidence only: dispatchable=false, live_write_allowed=false, scheduler_or_retry_wired=false, public_url_fetch=false, provider_or_api_call=false, browser_or_cdp=false, approval_ledger_live_write=false.',
    counts: readinessCounts,
    readiness_rows: [...readinessRows],
    blocked_actions: ['execute outbox', 'dispatch', 'publish', 'schedule', 'retry', 'verify public URL', 'call provider/API', 'use browser/CDP', 'download media', 'write live approval ledger'],
  },
  operator_bridge_lane: {
    lane_status: 'blocked',
    lane_summary: 'Discord and Telegram are consolidated into one local-only operator bridge: proven/checkpoint status may be displayed, but sending stays outside repo and operator-owned.',
    evidence_policy: 'Bridge rows may show redacted status and manual handoff text only. They never read secrets, call APIs, use browser/CDP, fetch URLs, wire schedulers, write live approval ledgers, or send messages.',
    bridge_rows: [...bridgeRows],
    blocked_actions: ['send Discord message', 'send Telegram message', 'read webhook URL', 'read bot token', 'call platform API', 'use browser/CDP', 'fetch public URL', 'schedule/retry', 'write live approval ledger'],
  },
  manual_deferred_distribution_lane: {
    lane_status: 'blocked',
    lane_summary: 'Facebook Page, Threads, Instagram, TikTok, and Generic Manual are hardened as local-only manual/deferred lanes with explicit blockers and operator handoff text.',
    evidence_policy: 'Rows reuse deterministic platform payload hashes and never post, edit, comment, DM, react, fetch public URLs, call platform APIs, use browser/CDP, read credentials/env, download/upload media, schedule/retry, or write a live approval ledger.',
    rows: [...manualDeferredRows],
    blocked_actions: ['publish/post/edit/comment', 'DM/reply/react', 'call Meta/TikTok/platform API', 'use browser/CDP', 'fetch public URL', 'download or upload media', 'schedule/retry', 'read credential/env/session', 'write live approval ledger'],
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
  final_operator_action_strip_lane: {
    strip_status: 'blocked',
    strip_summary: 'Final operator action strip consolidates approved manual export evidence, hold/reject decisions, Discord/Telegram bridge status, manual/deferred handoffs, audit evidence, and global locked execution flags.',
    evidence_policy: 'The strip is display-only and operator-owned. It never grants dispatch, live write, platform API, browser/CDP, public URL fetch, media download/upload, scheduler/retry, credential/env/session read, or live approval-ledger permission.',
    rows: [...finalOperatorActionStripRows],
    blocked_actions: ['publish/post/edit/comment', 'DM/reply/react', 'execute outbox', 'call platform/API/provider', 'use browser/CDP', 'fetch public URL', 'download/upload media', 'schedule/retry', 'read credential/env/session', 'write live approval ledger'],
    terminal_next_task: 'Archive stale one-off task scripts only after confirming no current tests/docs/imports reference them; then refresh final release evidence index if needed.',
  },
};
