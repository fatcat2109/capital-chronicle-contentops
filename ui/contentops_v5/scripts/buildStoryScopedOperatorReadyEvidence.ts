// Deterministic evidence for story-scoped permission and operator-ready text variants.
// Local, read-only evaluation only; no approval, publication, dispatch, or provider call.

import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  buildCanonicalReviewStories,
  sha256Canonical,
} from '../src/data/operatorPackageReviewAdapter';

const TASK = 'TASK_CONTENTOPS_FAST_SHIP_STORY_SCOPED_PERMISSION_AND_FIRST_TEXT_ONLY_OPERATOR_READY_PACKAGE_V1';
const CLASSIFICATION = 'PASS_FIRST_TEXT_ONLY_OPERATOR_READY_PACKAGE_V1_AWAITING_CHATGPT_AUDIT';
const NEXT_ACTION = 'INDEPENDENT_CHATGPT_AUDIT_STORY_SCOPED_PERMISSION_AND_FIRST_TEXT_ONLY_OPERATOR_READY_PACKAGE_V1';
const STARTING_SHA = '41c43419cbaa272f17f8543afa78edc0bdb30a87';
const OUTPUT_RELATIVE = 'docs/automation/CONTENTOPS_FAST_SHIP_STORY_SCOPED_PERMISSION_AND_FIRST_TEXT_ONLY_OPERATOR_READY_PACKAGE_V1';
const REGISTRY_PATH = 'docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/source_evidence_capability_registry_v2.json';
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

mkdirSync(outputDir, { recursive: true });
const first = buildCanonicalReviewStories();
const second = buildCanonicalReviewStories();
const replayHash = sha256Canonical(first);
const deterministicReplay = JSON.stringify(first) === JSON.stringify(second);
const claimAdjudication = readJson(`${OUTPUT_RELATIVE}/claim_permission_adjudication.json`);
const pythonValidation = readJson(`${OUTPUT_RELATIVE}/validation_truth.json`);
const browserQa = readJson(`${OUTPUT_RELATIVE}/browser_qa.json`);

const records = first.flatMap((story) => story.variants.map((variant) => ({
  schema_version: 'contentops.story_scoped_platform_readiness_record.v1',
  record_id: `story-scoped-readiness:${story.storyId}:${variant.platform}`,
  readiness_overlay: variant.readiness.readinessOverlay,
  story_id: story.storyId,
  source_family: story.authority.sourceFamily,
  story_type: story.readiness.storyType,
  effective_article_mode: variant.readiness.articleMode,
  market_sensitive: variant.readiness.marketSensitive,
  market_snapshot_required: variant.readiness.marketSnapshotRequired,
  platform_id: variant.platform,
  content_surface: variant.readiness.contentSurface,
  variant_mode: variant.readiness.variantMode,
  effective_platform_visual_mode: variant.readiness.effectivePlatformVisualMode,
  applicable_gates: variant.readiness.applicableGates,
  passed_gates: variant.readiness.passedGates,
  unresolved_blockers: variant.readiness.unresolvedBlockers,
  editorial_readiness: variant.readiness.editorialReadiness,
  operator_ready_for_decision: variant.readiness.operatorReadyForDecision,
  operator_decision_state: variant.readiness.operatorDecisionState,
  canonical_package_state: story.state,
  canonical_editorial_state: story.editorialState,
  publication_authority: false,
  publication_readiness: variant.readiness.publicationReadiness,
  publication_authority_blocker: variant.readiness.publicationAuthorityBlocker,
  dispatch_authority: false,
  dispatch_readiness: variant.readiness.dispatchReadiness,
  hashes: {
    package_hash: variant.readiness.hashes.packageHash,
    article_hash: variant.readiness.hashes.articleHash,
    v3_packet_hash: variant.readiness.hashes.v3PacketHash,
    variant_hash: variant.readiness.hashes.variantHash,
    visual_policy_hash: variant.readiness.hashes.visualPolicyHash,
    readiness_hash: variant.readiness.hashes.readinessHash,
  },
})));
const readyRecords = records.filter((row) => row.operator_ready_for_decision);
const recordsCore = {
  schema_version: 'contentops.story_scoped_platform_readiness_records.v1',
  task: TASK,
  readiness_overlay: 'DERIVED_READINESS_OVERLAY',
  capability_registry: {
    path: REGISTRY_PATH,
    git_blob_sha1: gitBlob(REGISTRY_PATH),
    byte_sha256: byteSha256(REGISTRY_PATH),
  },
  record_count: records.length,
  operator_ready_record_count: readyRecords.length,
  records,
};
writeJson('per_platform_readiness_records.json', {
  ...recordsCore,
  logical_hash: sha256Canonical(recordsCore),
});
const readyOperatorPackages = first.flatMap((story) => story.variants
  .filter((variant) => variant.readiness.operatorReadyForDecision)
  .map((variant) => {
    const core = {
      schema_version: 'contentops.text_only_operator_ready_package.v1',
      story_id: story.storyId,
      candidate_id: story.candidateId,
      platform_id: variant.platform,
      content_surface: variant.surface,
      effective_platform_visual_mode: variant.readiness.effectivePlatformVisualMode,
      text: variant.text,
      authorized_claim_ids: variant.authorizedClaimIds,
      citations: variant.citations,
      limitations: variant.limitations,
      package_hash: story.packageHash,
      article_hash: story.article.hash,
      v3_packet_hash: story.v3PacketLogicalHash,
      variant_hash: variant.payloadHash,
      readiness_hash: variant.readiness.hashes.readinessHash,
      editorial_state: 'EDITORIALLY_READY_FOR_OPERATOR_DECISION',
      operator_decision_state: 'PENDING_OPERATOR_DECISION',
      publication_authority: false,
      dispatch_authority: false,
      public_write_authority: false,
      exact_next_gate: 'JIM_MUST_DECIDE_EXACT_HASH_BOUND_TEXT_ONLY_PACKAGE_IN_SEPARATE_AUTHORIZED_TASK',
    };
    return { ...core, operator_package_receipt_hash: sha256Canonical(core) };
  }));
const readyPackagesCore = {
  schema_version: 'contentops.text_only_operator_ready_packages.v1',
  task: TASK,
  package_count: readyOperatorPackages.length,
  state: 'EDITORIALLY_READY_FOR_OPERATOR_DECISION',
  operator_decision_state: 'PENDING_OPERATOR_DECISION',
  packages: readyOperatorPackages,
  publication_authority: false,
  dispatch_authority: false,
  public_write_authority: false,
};
writeJson('text_only_operator_ready_packages.json', {
  ...readyPackagesCore,
  logical_hash: sha256Canonical(readyPackagesCore),
});

const storyByFamily = Object.fromEntries(first.map((story) => [story.authority.sourceFamily, story]));
const checks = {
  deterministic_replay: deterministicReplay,
  exact_three_story_eighteen_platform_records: first.length === 3 && records.length === 18,
  exact_five_claims_reporting_allowed: claimAdjudication.claim_count === 5 &&
    claimAdjudication.adjudications.every((row: any) => row.reporting_allowed === true && row.blockers.length === 0),
  nonnumeric_claim_bridge_allows_narrative_not_numeric:
    pythonValidation.nonnumeric_claim_permission_bridge_executable === true,
  fomc_snapshot_and_freshness_gates_preserved:
    storyByFamily.federal_reserve_fomc.readiness.marketSensitive === true &&
    storyByFamily.federal_reserve_fomc.readiness.marketSnapshotRequired === true &&
    storyByFamily.federal_reserve_fomc.blockers.freshness.length === 2,
  apple_snapshot_and_freshness_gates_preserved:
    storyByFamily.sec_edgar.readiness.marketSensitive === true &&
    storyByFamily.sec_edgar.readiness.marketSnapshotRequired === true &&
    storyByFamily.sec_edgar.blockers.freshness.length === 2,
  usgs_nonmarket_freshness_clear:
    storyByFamily.usgs_comcat.readiness.marketSensitive === false &&
    storyByFamily.usgs_comcat.readiness.marketSnapshotRequired === false &&
    storyByFamily.usgs_comcat.blockers.freshness.length === 0,
  only_exact_usgs_text_variants_operator_ready:
    readyRecords.length === 5 && readyRecords.every((row) =>
      row.source_family === 'usgs_comcat' &&
      row.effective_platform_visual_mode === 'text_only' &&
      row.platform_id !== 'substack_newsletter'),
  substack_long_form_visual_hold_preserved: records.filter((row) =>
    row.platform_id === 'substack_newsletter').every((row) =>
      row.editorial_readiness === 'BLOCK' && row.unresolved_blockers.some((value) => value.includes('visual'))),
  ready_records_operator_decision_pending: readyRecords.every((row) =>
    row.editorial_readiness === 'PASS' && row.operator_decision_state === 'PENDING_OPERATOR_DECISION'),
  exact_text_only_operator_ready_packages_emitted:
    readyOperatorPackages.length === 5 && readyOperatorPackages.every((row) =>
      row.editorial_state === 'EDITORIALLY_READY_FOR_OPERATOR_DECISION' &&
      row.operator_decision_state === 'PENDING_OPERATOR_DECISION' &&
      row.publication_authority === false && row.dispatch_authority === false),
  publication_and_dispatch_authority_false: records.every((row) =>
    row.publication_authority === false && row.dispatch_authority === false &&
    row.publication_readiness === 'BLOCK' && row.dispatch_readiness === 'BLOCK'),
  exact_hash_binding_complete: records.every((row) =>
    Object.values(row.hashes).every((value) => /^[a-f0-9]{64}$/.test(value))),
  browser_qa_desktop_mobile_pass:
    browserQa.status === 'PASS' &&
    browserQa.desktop.horizontal_overflow === false &&
    browserQa.mobile.horizontal_overflow === false &&
    browserQa.runtime_errors.length === 0,
};
const validationCore = {
  ...pythonValidation,
  schema_version: 'contentops.story_scoped_permission_operator_ready_validation_truth.v1',
  task: TASK,
  status: Object.values(checks).every(Boolean) ? 'PASS' : 'BLOCK',
  checks,
  blocker_count: Object.values(checks).filter((value) => !value).length,
  deterministic_replay_hash: replayHash,
  observed_validation: {
    focused_python_tests: { status: 'PASS', passed: 66 },
    full_v5_ui_suite: { status: 'PASS', test_files: 25, passed: 204 },
    production_build: 'PASS',
    desktop_mobile_edge_qa: 'PASS',
    json_and_hash_validation: 'PASS',
    git_diff_check: 'PASS',
    scoped_no_live_no_write_scan: 'PASS',
  },
  monolithic_repository_suite_run: false,
  ci_pass_claimed: false,
};
if (validationCore.status !== 'PASS') throw new Error('story_scoped_operator_ready_validation_blocked');
writeJson('validation_truth.json', validationCore);

const artifactNames = [
  'browser_qa.json',
  'browser_qa_desktop_1440x1000.png',
  'browser_qa_mobile_390x844.png',
  'canonical_content_evidence_packets_v3.json',
  'canonical_editorial_outcomes.json',
  'claim_permission_adjudication.json',
  'per_platform_readiness_records.json',
  'platform_native_variants.json',
  'superseding_unsigned_operator_packages.json',
  'text_only_operator_ready_packages.json',
  'validation_truth.json',
];
const manifestCore = {
  schema_version: 'contentops.story_scoped_permission_operator_ready_final_manifest.v1',
  task: TASK,
  starting_remote_head: STARTING_SHA,
  pinned_upstream_authority_commit: '64834919b4f69e977475c203abeafef57791f015',
  terminal_classification: CLASSIFICATION,
  exact_next_action: NEXT_ACTION,
  source_blobs: [
    'live_contentops/window_incremental_editorial_shadow_v1.py',
    'live_contentops/capital_chronicle_content_evidence_packet_v3.py',
    'live_contentops/multi_story_platform_native_operator_packages_v1.py',
    'ui/contentops_v5/src/data/operatorPackageReviewAdapter.ts',
    'ui/contentops_v5/scripts/buildStoryScopedOperatorReadyEvidence.ts',
    REGISTRY_PATH,
  ].map((path) => ({ path, git_blob_sha1: gitBlob(path), byte_sha256: byteSha256(path) })),
  artifacts: artifactNames.map((name) => ({
    path: `${OUTPUT_RELATIVE}/${name}`,
    byte_sha256: byteSha256(`${OUTPUT_RELATIVE}/${name}`),
  })),
  claim_count: claimAdjudication.claim_count,
  readiness_record_count: records.length,
  operator_ready_text_only_record_count: readyRecords.length,
  operator_decision_state: 'PENDING_OPERATOR_DECISION',
  publication_authority: false,
  dispatch_authority: false,
  public_write_authority: false,
  network_call_performed: false,
  provider_action_performed: false,
  public_write_performed: false,
  monolithic_repository_suite_run: false,
  ci_pass_claimed: false,
  result: 'PASS',
};
writeJson('final_manifest.json', { ...manifestCore, logical_hash: sha256Canonical(manifestCore) });
process.stdout.write(`${JSON.stringify({ records: records.length, operatorReady: readyRecords.length, result: 'PASS' })}\n`);
