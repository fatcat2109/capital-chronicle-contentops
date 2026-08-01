// Deterministic local evidence writer for the canonical V5 derived-readiness overlay.
// No network, credentials, approval, publication, dispatch, or provider calls.

import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  buildCanonicalReviewStories,
  sha256Canonical,
} from '../src/data/operatorPackageReviewAdapter';

const TASK = 'TASK_CONTENTOPS_FAST_SHIP_CAPABILITY_POLICY_GENERICITY_AND_READINESS_RECEIPT_REPAIR_V1';
const CLASSIFICATION = 'PASS_CAPABILITY_POLICY_GENERICITY_AND_READINESS_RECEIPT_REPAIR_V1_AWAITING_CHATGPT_AUDIT';
const NEXT_ACTION = 'INDEPENDENT_CHATGPT_AUDIT_CAPABILITY_POLICY_GENERICITY_AND_READINESS_RECEIPT_REPAIR_V1';
const STARTING_SHA = '6de0a8c8fc3cfc510b9ffa0e840e701fabd6e466';
const REGISTRY_PATH = 'docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/source_evidence_capability_registry_v2.json';
const PACKAGE_PATH = 'docs/automation/CONTENTOPS_FAST_SHIP_BIND_THREE_V3_PACKETS_TO_CANONICAL_EDITORIAL_AND_OPERATOR_PACKAGES_V1/superseding_unsigned_operator_packages.json';
const EDITORIAL_PATH = 'docs/automation/CONTENTOPS_FAST_SHIP_BIND_THREE_V3_PACKETS_TO_CANONICAL_EDITORIAL_AND_OPERATOR_PACKAGES_V1/canonical_editorial_outcomes.json';
const VARIANT_PATH = 'docs/automation/CONTENTOPS_FAST_SHIP_MULTI_STORY_PLATFORM_NATIVE_OPERATOR_PACKAGES_V1/platform_native_variants.json';

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(here, '../../..');
const outputDir = resolve(
  repoRoot,
  'docs/automation/CONTENTOPS_FAST_SHIP_CAPABILITY_POLICY_GENERICITY_AND_READINESS_RECEIPT_REPAIR_V1',
);

function byteSha256(path: string): string {
  return createHash('sha256').update(readFileSync(resolve(repoRoot, path))).digest('hex');
}

function writeJson(name: string, value: unknown): void {
  writeFileSync(resolve(outputDir, name), `${JSON.stringify(value, null, 2)}\n`, 'utf8');
}

const registryGitBlob = execFileSync('git', ['hash-object', REGISTRY_PATH], {
  cwd: repoRoot,
  encoding: 'utf8',
}).trim();
if (!/^[a-f0-9]{40}$/.test(registryGitBlob)) throw new Error('capability_registry_git_blob_invalid');

const first = buildCanonicalReviewStories();
const second = buildCanonicalReviewStories();
const deterministicReplay = JSON.stringify(first) === JSON.stringify(second);

const records = first.flatMap((story) => story.variants.map((variant) => ({
  schema_version: 'contentops.capability_readiness_record.v1',
  record_id: `capability-readiness:${story.storyId}:${variant.platform}`,
  readiness_overlay: variant.readiness.readinessOverlay,
  capability_registry: {
    path: REGISTRY_PATH,
    git_blob_sha1: registryGitBlob,
  },
  story_id: story.storyId,
  story_type: story.readiness.storyType,
  effective_article_mode: variant.readiness.articleMode,
  market_sensitive: variant.readiness.marketSensitive,
  market_snapshot_required: variant.readiness.marketSnapshotRequired,
  platform_id: variant.platform,
  content_surface: variant.readiness.contentSurface,
  variant_mode: variant.readiness.variantMode,
  effective_platform_visual_mode: variant.readiness.effectivePlatformVisualMode,
  visual_policy: variant.readiness.visualPolicy,
  hashes: {
    package_hash: variant.readiness.hashes.packageHash,
    article_hash: variant.readiness.hashes.articleHash,
    v3_packet_hash: variant.readiness.hashes.v3PacketHash,
    variant_hash: variant.readiness.hashes.variantHash,
    visual_policy_hash: variant.readiness.hashes.visualPolicyHash,
    readiness_hash: variant.readiness.hashes.readinessHash,
  },
  applicable_gates: variant.readiness.applicableGates,
  passed_gates: variant.readiness.passedGates,
  unresolved_blockers: variant.readiness.unresolvedBlockers,
  canonical_package_evidence: {
    unchanged: variant.readiness.canonicalPackageEvidenceUnchanged,
    package_state: story.state,
    editorial_state: story.editorialState,
    recommendation: story.recommendation,
  },
  publication_authority: variant.readiness.publicationAuthority,
  dispatch_authority: variant.readiness.dispatchAuthority,
  publication_readiness: variant.readiness.publicationReadiness,
  dispatch_readiness: variant.readiness.dispatchReadiness,
  editorial_readiness: variant.readiness.editorialReadiness,
})));

const recordsCore = {
  schema_version: 'contentops.capability_readiness_records.v1',
  task: TASK,
  readiness_overlay: 'DERIVED_READINESS_OVERLAY',
  capability_registry: { path: REGISTRY_PATH, git_blob_sha1: registryGitBlob },
  record_count: records.length,
  records,
};
const recordsPacket = { ...recordsCore, logical_hash: sha256Canonical(recordsCore) };

const storyMap = Object.fromEntries(first.map((story) => [story.authority.sourceFamily, story]));
const validationChecks = {
  deterministic_replay: deterministicReplay,
  exact_story_count_three: first.length === 3,
  exact_platform_record_count_eighteen: records.length === 18,
  fomc_analysis_market_sensitive_snapshot_required:
    storyMap.federal_reserve_fomc?.readiness.articleMode === 'analysis' &&
    storyMap.federal_reserve_fomc?.readiness.marketSensitive === true &&
    storyMap.federal_reserve_fomc?.readiness.marketSnapshotRequired === true,
  apple_analysis_market_sensitive_snapshot_required:
    storyMap.sec_edgar?.readiness.articleMode === 'analysis' &&
    storyMap.sec_edgar?.readiness.marketSensitive === true &&
    storyMap.sec_edgar?.readiness.marketSnapshotRequired === true,
  usgs_analysis_nonmarket_snapshot_not_required:
    storyMap.usgs_comcat?.readiness.articleMode === 'analysis' &&
    storyMap.usgs_comcat?.readiness.marketSensitive === false &&
    storyMap.usgs_comcat?.readiness.marketSnapshotRequired === false,
  all_records_derived_overlay: records.every((row) => row.readiness_overlay === 'DERIVED_READINESS_OVERLAY'),
  all_canonical_package_evidence_unchanged: records.every((row) => row.canonical_package_evidence.unchanged),
  all_publication_authority_false: records.every((row) => row.publication_authority === false),
  all_dispatch_authority_false: records.every((row) => row.dispatch_authority === false),
  all_hashes_sha256: records.every((row) => Object.values(row.hashes).every((value) => /^[a-f0-9]{64}$/.test(value))),
  exact_current_text_only_waivers_only: records.every((row) =>
    row.effective_platform_visual_mode !== 'text_only' ||
    (row.variant_mode === 'dry_run' && row.platform_id !== 'substack_newsletter'),
  ),
};
const validationCore = {
  schema_version: 'contentops.capability_policy_genericity_validation_truth.v1',
  task: TASK,
  checks: validationChecks,
  blocker_count: Object.values(validationChecks).filter((value) => !value).length,
  result: Object.values(validationChecks).every(Boolean) ? 'PASS' : 'BLOCK',
  replay_hash: sha256Canonical(first),
  protected_state: {
    canonical_package_evidence_unchanged: true,
    publication_authority: false,
    dispatch_authority: false,
    approval_execution_performed: false,
    network_call_performed: false,
    provider_call_performed: false,
    public_write_performed: false,
  },
};
const validationPacket = { ...validationCore, logical_hash: sha256Canonical(validationCore) };
if (validationPacket.result !== 'PASS') throw new Error('capability_readiness_validation_blocked');

mkdirSync(outputDir, { recursive: true });
writeJson('capability_readiness_records.json', recordsPacket);
writeJson('validation_truth.json', validationPacket);

const manifestCore = {
  schema_version: 'contentops.capability_policy_genericity_readiness_receipt_final_manifest.v1',
  task: TASK,
  starting_remote_head: STARTING_SHA,
  terminal_classification: CLASSIFICATION,
  exact_next_action: NEXT_ACTION,
  capability_registry: {
    path: REGISTRY_PATH,
    git_blob_sha1: registryGitBlob,
    byte_sha256: byteSha256(REGISTRY_PATH),
  },
  canonical_evidence_unchanged: [PACKAGE_PATH, EDITORIAL_PATH, VARIANT_PATH].map((path) => ({
    path,
    byte_sha256: byteSha256(path),
  })),
  output_artifacts: [
    'capability_readiness_records.json',
    'validation_truth.json',
  ].map((name) => ({
    path: `docs/automation/CONTENTOPS_FAST_SHIP_CAPABILITY_POLICY_GENERICITY_AND_READINESS_RECEIPT_REPAIR_V1/${name}`,
    byte_sha256: byteSha256(`docs/automation/CONTENTOPS_FAST_SHIP_CAPABILITY_POLICY_GENERICITY_AND_READINESS_RECEIPT_REPAIR_V1/${name}`),
  })),
  record_count: records.length,
  readiness_overlay: 'DERIVED_READINESS_OVERLAY',
  publication_authority: false,
  dispatch_authority: false,
  public_write_performed: false,
  monolithic_repository_suite_run: false,
  ci_pass_claimed: false,
  result: 'PASS',
};
writeJson('final_manifest.json', { ...manifestCore, logical_hash: sha256Canonical(manifestCore) });

process.stdout.write(`${JSON.stringify({ outputDir, recordCount: records.length, registryGitBlob, result: 'PASS' })}\n`);
