import { cockpitReadModelPacket } from './cockpitReadModelPacket';
import type {
  CockpitQueueItem,
  CockpitViewModel,
  ManualPublishRecord,
  PlatformPayloadPreview,
  StatusKind,
  SystemState,
} from '../types';

const statusFromQueue = (item: CockpitQueueItem): StatusKind =>
  item.review_status.includes('manual') ? 'verified' : 'review';


export const cockpitViewModel: CockpitViewModel = {
  packet: cockpitReadModelPacket,
  manual_export_queue: cockpitReadModelPacket.current_review_queue.filter(
    (item) => item.platform === 'substack',
  ),
  x_preview_queue: cockpitReadModelPacket.current_review_queue.filter(
    (item) => item.platform === 'x',
  ),
  telegram_preview_queue: cockpitReadModelPacket.current_review_queue.filter(
    (item) => item.platform === 'telegram',
  ),
  blocked_live_dispatch_queue: cockpitReadModelPacket.blocked_live_dispatch_queue,
  evidence_index: cockpitReadModelPacket.evidence_index,
  safety_modes: [
    'NO_LIVE_DISPATCH',
    'NO_PLATFORM_API',
    'NO_PROVIDER_API',
    'NO_CREDENTIAL_READ',
    'NO_SCHEDULER',
    'NO_SCRAPING',
    'NO_AUTONOMOUS_REPLIES_OR_DMS',
  ],
  current_gate: cockpitReadModelPacket.readiness_class,
  accepted_baseline: cockpitReadModelPacket.source_baseline_commit,
};

export function buildCockpitSystemState(base: SystemState): SystemState {
  const packet = cockpitReadModelPacket;
  return {
    ...base,
    verdict: 'NOT READY FOR LIVE DISPATCH',
    verdict_status: 'blocked',
    baseline_ref: packet.source_baseline_commit,
    build_provenance: `${packet.model_version} · checksum ${packet.cockpit_read_model_checksum.slice(0, 12)}`,
    next_allowed_action: packet.next_operator_action,
    blockers: packet.blocked_live_dispatch_queue.map((blocker, index) => ({
      id: `BLK-LIVE-${String(index + 1).padStart(2, '0')}`,
      label: blocker.required_future_gate.replace(/_/g, ' '),
      detail: blocker.reason,
      severity: 'blocked',
    })),
    validation_passes: [
      { id: 'CR-1', label: 'No live dispatch', status: 'verified', detail: packet.no_live_behavior_proof.proof },
      { id: 'CR-2', label: 'No platform API', status: 'verified', detail: 'x/substack/telegram API flags false' },
      { id: 'CR-3', label: 'No credential hydration', status: 'verified', detail: 'credential_read=false and env_read=false' },
      { id: 'CR-4', label: 'Payload hashes evidence-bound', status: 'verified', detail: `${packet.current_review_queue.length} review payloads carry hashes` },
    ],
    pipeline_health: [
      { label: 'Reviewable now', value: String(packet.operator_summary.reviewable_now_count), status: 'review' },
      { label: 'Manual export', value: String(packet.platform_counts.substack), status: 'verified' },
      { label: 'Preview queues', value: String(packet.platform_counts.x + packet.platform_counts.telegram), status: 'review' },
      { label: 'Live dispatch', value: packet.live_dispatch_status, status: 'blocked' },
    ],
    queue_summary: [
      { label: 'Manual export queue', count: packet.platform_counts.substack, status: 'verified' },
      { label: 'X preview queue', count: packet.platform_counts.x, status: 'review' },
      { label: 'Telegram preview queue', count: packet.platform_counts.telegram, status: 'review' },
      { label: 'Blocked live dispatch', count: packet.operator_summary.blocked_live_dispatch_count, status: 'blocked' },
    ],
  };
}

export function buildCockpitPreviews(): PlatformPayloadPreview[] {
  const byPlatform = (platform: string) =>
    cockpitReadModelPacket.current_review_queue.find((item) => item.platform === platform) ??
    cockpitReadModelPacket.current_review_queue[0];
  const fromItem = (item: CockpitQueueItem, key: string, label: string): PlatformPayloadPreview => ({
    id: `PP-${label}`,
    platform: label,
    platform_key: key,
    source_draft_id: item.item_id,
    format_label: item.payload_class.replace(/_/g, ' '),
    fit_status: statusFromQueue(item),
    fit_summary: item.review_status,
    fields: [
      { id: `${key}-body`, label: 'Payload class', value: item.payload_class, mono: true },
      { id: `${key}-action`, label: 'Allowed action', value: item.allowed_operator_action, mono: true },
      { id: `${key}-hash`, label: 'Payload hash', value: item.payload_hash, mono: true },
      { id: `${key}-evidence`, label: 'Evidence refs', value: item.evidence_refs.join('\n'), mono: true },
      { id: `${key}-limits`, label: 'Limitations', value: item.limitations.join(' · ') },
    ],
    constraints: [
      { id: `${key}-c1`, label: 'Dispatch gate', limit: 'false', actual: String(item.can_dispatch), status: 'blocked', detail: 'Live dispatch is blocked.' },
      { id: `${key}-c2`, label: 'Public postable', limit: 'false', actual: String(item.public_postable), status: 'blocked', detail: 'Payload is review-only and not public-ready.' },
      { id: `${key}-c3`, label: 'Human review', limit: 'required', actual: item.human_review_required ? 'required' : 'missing', status: 'review', detail: 'Operator review remains required.' },
    ],
    media_note: 'No media upload · no file picker · no external asset fetch',
    live_status: 'LIVE_DISABLED',
    credential_status: 'NO_CREDENTIAL_READ',
    provider_status: 'NO_PROVIDER_CALL',
    not_dispatchable_reason: 'blocked by cockpit read model future gates',
    dispatchable: false,
  });
  const generic = (key: string, label: string, status: StatusKind = 'review'): PlatformPayloadPreview => ({
    ...fromItem(byPlatform('substack'), key, label),
    id: `PP-${label}`,
    platform: label,
    platform_key: key,
    fit_status: status,
    fit_summary: 'covered by V5 fallback preview · live dispatch still blocked',
  });
  return [
    fromItem(byPlatform('x'), 'x', 'X'),
    generic('linkedin', 'LinkedIn', 'verified'),
    generic('threads', 'Threads', 'verified'),
    fromItem(byPlatform('substack'), 'substack', 'Substack'),
    fromItem(byPlatform('telegram'), 'telegram', 'Telegram'),
    generic('facebook', 'Facebook'),
    generic('instagram', 'Instagram'),
    generic('tiktok', 'TikTok', 'blocked'),
  ];
}

export function buildCockpitManualRecords(): ManualPublishRecord[] {
  const manual = cockpitViewModel.manual_export_queue;
  const first = manual[0];
  const second = manual[1] ?? first;
  const base = (id: string, platform: string, key: string, item: CockpitQueueItem, stage: ManualPublishRecord['stage'], stageLabel: string, stageStatus: StatusKind): ManualPublishRecord => ({
    id,
    platform,
    platform_key: key,
    source_draft_id: item.item_id,
    payload_ref: item.payload_class,
    payload_hash: item.payload_hash,
    approval_packet_ref: cockpitReadModelPacket.cockpit_read_model_id,
    approval_packet_hash: cockpitReadModelPacket.cockpit_read_model_checksum,
    stage,
    stage_label: stageLabel,
    stage_status: stageStatus,
    manual_url: '',
    published_at: '',
    checklist: [
      { id: `${id}-ck1`, label: 'Approval packet signed', status: 'review', detail: 'Cockpit read model requires human review.' },
      { id: `${id}-ck2`, label: 'Payload hash matches preview', status: 'verified', detail: item.payload_hash },
      { id: `${id}-ck3`, label: 'No-signal language check', status: item.no_signal_language ? 'verified' : 'blocked', detail: item.limitations.join(' · ') },
    ],
    metrics: [],
    audit_state: 'dry-run evidence only',
    audit_status: stageStatus,
    caveat: item.limitations.join(' · '),
    blocked_reason: stage === 'blocked' ? 'blocked by cockpit read model future gates' : '',
    allowed_operator_action: item.allowed_operator_action,
    evidence_refs: item.evidence_refs,
    public_postable: false,
    live_status: 'MANUAL_ONLY',
    platform_api_status: 'NO_PLATFORM_API',
    credential_status: 'NO_CREDENTIAL_READ',
    scheduler_status: 'NO_SCHEDULER',
    autonomous_status: 'NO_AUTONOMOUS_POSTING',
    metrics_status: 'METRICS_MANUAL_ENTRY_ONLY',
    review_status: 'HUMAN_REVIEW_REQUIRED',
    can_post_live: false,
  });
  const records = [
    base('MP-X-0042', 'X', 'x', first, 'approved_for_manual', 'Approved for manual', 'verified'),
    base('MP-LI-0042', 'LinkedIn', 'linkedin', second, 'manually_posted', 'Manually posted', 'verified'),
    base('MP-TG-0042', 'Telegram', 'telegram', first, 'metrics_entered', 'Metrics entered', 'verified'),
    base('MP-TT-0042', 'TikTok', 'tiktok', second, 'blocked', 'Blocked', 'blocked'),
  ];
  records[1].manual_url = 'https://example.invalid/linkedin/local-mock-post-0042';
  records[1].published_at = '2026-06-15T08:40:00+07:00';
  records[2].manual_url = 'https://example.invalid/t/local-mock-channel/512';
  records[2].published_at = '2026-06-14T19:05:00+07:00';
  records[2].metrics = [
    { id: 'MP-TG-m1', captured_at: '2026-06-15T08:00:00+07:00', impressions: 1840, likes: 73, comments: 11, shares: 9, saves: 4, click_count: 38, notes: 'Manual snapshot typed by operator. No metrics API.', source: 'MANUAL_ENTRY' },
  ];
  return records;
}
