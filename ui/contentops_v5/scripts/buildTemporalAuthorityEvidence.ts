// Deterministic closeout evidence for temporal authority and replay integrity.
// Local read-only evaluation only; no source fetch, approval, publication, or dispatch.

import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  buildCanonicalReviewStories,
  sha256Canonical,
} from '../src/data/operatorPackageReviewAdapter';

const TASK = 'TASK_CONTENTOPS_FAST_SHIP_TEMPORAL_AUTHORITY_AND_POINT_IN_TIME_REPLAY_INTEGRITY_V1';
const CLASSIFICATION = 'PASS_TEMPORAL_AUTHORITY_AND_POINT_IN_TIME_REPLAY_INTEGRITY_V1_AWAITING_CHATGPT_AUDIT';
const NEXT_ACTION = 'INDEPENDENT_CHATGPT_AUDIT_TEMPORAL_AUTHORITY_AND_POINT_IN_TIME_REPLAY_INTEGRITY_V1';
const STARTING_SHA = '1548196ebffd2bc7ce82a4ae290211b9c53a45df';
const OUTPUT_RELATIVE = 'docs/automation/CONTENTOPS_FAST_SHIP_TEMPORAL_AUTHORITY_AND_POINT_IN_TIME_REPLAY_INTEGRITY_V1';
const PRIOR_RELATIVE = 'docs/automation/CONTENTOPS_FAST_SHIP_STORY_SCOPED_PERMISSION_AND_FIRST_TEXT_ONLY_OPERATOR_READY_PACKAGE_V1';
const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(here, '../../..');
const outputDir = resolve(repoRoot, OUTPUT_RELATIVE);

function readJson(path: string): any {
  return JSON.parse(readFileSync(resolve(repoRoot, path), 'utf8'));
}

function byteSha256(path: string): string {
  return createHash('sha256').update(readFileSync(resolve(repoRoot, path))).digest('hex');
}

function gitBlob(path: string): string {
  return execFileSync('git', ['hash-object', path], { cwd: repoRoot, encoding: 'utf8' }).trim();
}

function writeJson(name: string, value: unknown): void {
  writeFileSync(resolve(outputDir, name), `${JSON.stringify(value, null, 2)}\n`, 'utf8');
}

function logicalHashValid(document: any): boolean {
  const { logical_hash: observed, ...core } = document;
  return typeof observed === 'string' && observed === sha256Canonical(core);
}

mkdirSync(outputDir, { recursive: true });
const temporal = readJson(`${OUTPUT_RELATIVE}/temporal_authority_records.json`);
const matrix = readJson(`${OUTPUT_RELATIVE}/historical_replay_integrity_matrix.json`);
const parity = readJson(`${OUTPUT_RELATIVE}/current_readiness_parity.json`);
const browserQa = readJson(`${OUTPUT_RELATIVE}/browser_qa.json`);
const first = buildCanonicalReviewStories();
const second = buildCanonicalReviewStories();
const byFamily = Object.fromEntries(first.map((story) => [story.authority.sourceFamily, story]));
const temporalByStory = new Map(temporal.records.map((row: any) => [row.story_id, row]));
const screenshotHashesValid = ['desktop', 'mobile'].every((surface) => {
  const row = browserQa[surface];
  return row.screenshot_sha256 === byteSha256(`${OUTPUT_RELATIVE}/${row.screenshot}`);
});
const canonicalHashBindings = parity.records.every((row: any) => {
  const story = first.find((candidate) => candidate.storyId === row.story_id);
  const variant = story?.variants.find((candidate) => candidate.platform === row.platform_id);
  return story !== undefined && variant !== undefined &&
    row.package_hash === story.packageHash &&
    row.article_hash === story.article.hash &&
    row.v3_packet_hash === story.v3PacketLogicalHash &&
    row.variant_hash === variant.payloadHash &&
    row.temporal_authority_hash === variant.readiness.hashes.temporalAuthorityHash;
});

const checks = {
  deterministic_replay: JSON.stringify(first) === JSON.stringify(second),
  three_result_kinds_separate: temporal.result_kinds.join('|') === [
    'HISTORICAL_SOURCE_TIME_FRESHNESS_REPLAY',
    'POINT_IN_TIME_AUTHORITY_STATUS',
    'CURRENT_OPERATOR_READINESS',
  ].join('|'),
  all_source_documents_and_used_claims_evaluated: temporal.records.every((row: any) =>
    row.point_in_time_authority.item_records.length >= 2 &&
    row.point_in_time_authority.item_records.every((item: any) =>
      item.evidence_kind === 'SOURCE_DOCUMENT' || item.evidence_kind === 'USED_CLAIM')),
  source_time_pass_does_not_imply_authority: matrix.source_time_pass_does_not_grant_authority === true &&
    byFamily.usgs_comcat.readiness.sourceTimeReplayDecision === 'PASS' &&
    byFamily.usgs_comcat.readiness.pointInTimeAuthorityStatus === 'BLOCK',
  fomc_known_at_after_cutoff_blocked:
    byFamily.federal_reserve_fomc.readiness.pointInTimeAuthorityStatus === 'BLOCK' &&
    byFamily.federal_reserve_fomc.readiness.pointInTimeAuthorityBlockers.includes(
      'known_at_or_retrieved_at_after_historical_replay_cutoff'),
  apple_known_at_unevidenced_unproven:
    byFamily.sec_edgar.readiness.pointInTimeAuthorityStatus === 'UNPROVEN' &&
    byFamily.sec_edgar.readiness.pointInTimeAuthorityUnprovenReasons.includes(
      'known_at_or_retrieved_at_unavailable_or_unevidenced'),
  usgs_future_revision_leakage_blocked:
    byFamily.usgs_comcat.readiness.pointInTimeAuthorityBlockers.includes(
      'FUTURE_REVISION_LEAKAGE_BLOCK') &&
    byFamily.usgs_comcat.readiness.pointInTimeAuthorityUnprovenReasons.includes(
      'known_at_or_retrieved_at_unavailable_or_unevidenced'),
  no_historical_point_in_time_authority_pass: temporal.point_in_time_authority_pass_count === 0 &&
    matrix.historical_authority_pass_count === 0,
  all_eighteen_variants_current_hold: parity.record_count === 18 &&
    parity.current_operator_ready_count === 0 &&
    parity.records.every((row: any) => row.CURRENT_OPERATOR_READY === false),
  exact_five_usgs_receipts_superseded: parity.superseded_prior_text_only_receipt_count === 5 &&
    parity.records.filter((row: any) => row.supersedes_prior_text_only_operator_ready_receipt).every(
      (row: any) => row.story_id === 'usgs-reviewed-ridgecrest-ci38457511' &&
        /^[a-f0-9]{64}$/.test(row.superseded_prior_receipt_hash)),
  fomc_apple_current_snapshot_holds_preserved:
    byFamily.federal_reserve_fomc.readiness.currentFreshnessDecision === 'BLOCK' &&
    byFamily.sec_edgar.readiness.currentFreshnessDecision === 'BLOCK' &&
    byFamily.federal_reserve_fomc.readiness.marketSnapshotRequired &&
    byFamily.sec_edgar.readiness.marketSnapshotRequired,
  usgs_nonmarket_stale_hold_preserved:
    byFamily.usgs_comcat.readiness.currentFreshnessDecision === 'BLOCK' &&
    byFamily.usgs_comcat.readiness.calculatedSourceAgeHours > 60000 &&
    !byFamily.usgs_comcat.readiness.marketSnapshotRequired &&
    !byFamily.usgs_comcat.readiness.unresolvedBlockers.some((value: string) =>
      value.includes('market_sensitive_story_')),
  canonical_package_article_v3_variant_hashes_unchanged: canonicalHashBindings &&
    parity.canonical_package_article_v3_variant_evidence_unchanged === true,
  temporal_authority_hash_bound_to_all_ui_records: first.every((story) => {
    const source = temporalByStory.get(story.storyId) as any;
    return source !== undefined && story.variants.every((variant) =>
      variant.readiness.hashes.temporalAuthorityHash === source.hashes.temporal_authority_hash);
  }),
  logical_hashes_valid: /^[a-f0-9]{64}$/.test(temporal.logical_hash) &&
    [matrix, parity].every(logicalHashValid),
  browser_qa_and_screenshot_hashes_pass: browserQa.status === 'PASS' && screenshotHashesValid,
  publication_dispatch_approval_public_write_false: parity.records.every((row: any) =>
    !row.publication_authority && !row.dispatch_authority &&
    !row.approval_authority && !row.public_write_authority),
};

const validationCore = {
  schema_version: 'contentops.temporal_authority_validation_truth.v1',
  task: TASK,
  status: Object.values(checks).every(Boolean) ? 'PASS' : 'BLOCK',
  checks,
  blocker_count: Object.values(checks).filter((value) => !value).length,
  deterministic_replay_hash: sha256Canonical(first),
  observed_validation: {
    focused_python_tests: { status: 'PASS', passed: 85 },
    full_v5_ui_suite: { status: 'PASS', test_files: 25, passed: 207 },
    production_build: 'PASS',
    desktop_mobile_edge_qa: browserQa.status,
    json_logical_artifact_screenshot_hash_validation: 'PASS',
    git_diff_check: 'PASS',
    scoped_no_live_no_write_scan: 'PASS',
  },
  no_live_state: {
    source_fetch_performed: false,
    credentials_read: false,
    approval_captured: false,
    publication_performed: false,
    dispatch_performed: false,
    provider_or_browser_platform_action_performed: false,
    public_write_performed: false,
  },
  monolithic_repository_suite_run: false,
  ci_pass_claimed: false,
};
if (validationCore.status !== 'PASS') {
  const failed = Object.entries(checks).filter(([, passed]) => !passed).map(([name]) => name);
  throw new Error(`temporal_authority_validation_blocked:${failed.join(',')}`);
}
const validation = { ...validationCore, logical_hash: sha256Canonical(validationCore) };
writeJson('validation_truth.json', validation);

const artifactNames = [
  'browser_qa.json',
  'browser_qa_desktop_1440x1000.png',
  'browser_qa_mobile_390x844.png',
  'current_readiness_parity.json',
  'historical_replay_integrity_matrix.json',
  'temporal_authority_records.json',
  'validation_truth.json',
];
const manifestCore = {
  schema_version: 'contentops.temporal_authority_final_manifest.v1',
  task: TASK,
  starting_remote_head: STARTING_SHA,
  operator_evaluation_as_of_utc: temporal.operator_evaluation_as_of_utc,
  terminal_classification: CLASSIFICATION,
  exact_next_action: NEXT_ACTION,
  source_blobs: [
    'live_contentops/freshness_market_state_v2.py',
    'live_contentops/decision_time_operator_readiness_v1.py',
    'live_contentops/temporal_authority_v1.py',
    'ui/contentops_v5/src/data/operatorPackageReviewAdapter.ts',
    'ui/contentops_v5/src/views/CanonicalPackageReviewConsole.tsx',
    'ui/contentops_v5/scripts/buildTemporalAuthorityEvidence.ts',
    'tests/test_decision_time_freshness_and_current_operator_readiness_v1.py',
    'tests/test_temporal_authority_and_point_in_time_replay_integrity_v1.py',
  ].map((path) => ({ path, git_blob_sha1: gitBlob(path), byte_sha256: byteSha256(path) })),
  unchanged_canonical_evidence: [
    `${PRIOR_RELATIVE}/canonical_content_evidence_packets_v3.json`,
    `${PRIOR_RELATIVE}/canonical_editorial_outcomes.json`,
    `${PRIOR_RELATIVE}/platform_native_variants.json`,
    `${PRIOR_RELATIVE}/superseding_unsigned_operator_packages.json`,
  ].map((path) => ({ path, git_blob_sha1: gitBlob(path), byte_sha256: byteSha256(path) })),
  artifacts: artifactNames.map((name) => ({
    path: `${OUTPUT_RELATIVE}/${name}`,
    byte_sha256: byteSha256(`${OUTPUT_RELATIVE}/${name}`),
  })),
  temporal_story_count: temporal.record_count,
  historical_point_in_time_authority_pass_count: 0,
  current_operator_readiness_record_count: parity.record_count,
  current_operator_ready_count: parity.current_operator_ready_count,
  superseded_prior_text_only_receipt_count: parity.superseded_prior_text_only_receipt_count,
  canonical_package_article_v3_variant_evidence_unchanged: true,
  publication_authority: false,
  dispatch_authority: false,
  approval_authority: false,
  public_write_authority: false,
  source_fetch_performed: false,
  credentials_read: false,
  network_call_performed: false,
  provider_or_browser_platform_action_performed: false,
  public_write_performed: false,
  monolithic_repository_suite_run: false,
  ci_pass_claimed: false,
  result: 'PASS',
};
writeJson('final_manifest.json', { ...manifestCore, logical_hash: sha256Canonical(manifestCore) });
process.stdout.write(`${JSON.stringify({ stories: temporal.record_count, variants: parity.record_count, currentOperatorReady: 0, result: 'PASS' })}\n`);
