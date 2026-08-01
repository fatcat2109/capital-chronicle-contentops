// Capital Chronicle ContentOps V5 — canonical package review read model.
// Static imports only. No network, storage, credentials, or decision execution.

import editorialEvidence from '../../../../docs/automation/CONTENTOPS_FAST_SHIP_BIND_THREE_V3_PACKETS_TO_CANONICAL_EDITORIAL_AND_OPERATOR_PACKAGES_V1/canonical_editorial_outcomes.json';
import packageEvidence from '../../../../docs/automation/CONTENTOPS_FAST_SHIP_BIND_THREE_V3_PACKETS_TO_CANONICAL_EDITORIAL_AND_OPERATOR_PACKAGES_V1/superseding_unsigned_operator_packages.json';
import variantEvidence from '../../../../docs/automation/CONTENTOPS_FAST_SHIP_MULTI_STORY_PLATFORM_NATIVE_OPERATOR_PACKAGES_V1/platform_native_variants.json';
import sourceCapabilityRegistry from '../../../../docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/source_evidence_capability_registry_v2.json';
import type { SelectableObject, StatusKind } from '../types';

export const CANONICAL_REVIEW_RECOMMENDATION = 'REQUEST_REVISION' as const;
export const CANONICAL_REVIEW_SURFACE_MODE = 'READ_ONLY_EVIDENCE_REVIEW' as const;

export interface CanonicalReviewClaim {
  authority: string;
  citations: string[];
  id: string;
  permission: string;
  text: string;
}

export interface CanonicalReviewRole {
  blockers: string[];
  decision: string;
  outputHash: string;
  role: string;
  status: string;
}

export interface CanonicalVariantEvidenceRecord {
  authorized_claim_ids: string[];
  candidate_id: string;
  character_count: number;
  character_limit_max: number;
  citation_urls: string[];
  content_surface: string;
  dispatch_ready: boolean;
  limitation_fingerprints: string[];
  mode: string;
  payload_hash: string;
  platform_id: string;
  story_id: string;
  text: string;
  valid_for_dispatch: boolean;
}

export interface CanonicalReviewVariant {
  authorizedClaimIds: string[];
  characterCount: number;
  characterLimit: number;
  citations: string[];
  dispatchAuthorized: false;
  limitationFingerprints: string[];
  limitations: string[];
  mode: string;
  payloadHash: string;
  platform: string;
  surface: string;
  text: string;
  readiness: CanonicalPlatformReadiness;
}

export type CanonicalJoinedVariant = Omit<CanonicalReviewVariant, 'readiness'>;

export type ReadinessGateStatus = 'PASS' | 'BLOCK' | 'NOT_APPLICABLE';
export type ReadinessGateCategory = 'editorial' | 'freshness' | 'visual' | 'authority' | 'dispatch';

export interface CanonicalReadinessGate {
  blockers: string[];
  category: ReadinessGateCategory;
  detail: string;
  id: string;
  status: ReadinessGateStatus;
}

export interface CanonicalReadinessHashes {
  articleHash: string;
  packageHash: string;
  v3PacketHash: string;
  variantHash: string;
}

export interface CanonicalPlatformReadiness {
  applicableGates: string[];
  articleMode: string;
  dispatchReadiness: ReadinessGateStatus;
  editorialReadiness: ReadinessGateStatus;
  freshnessPolicy: string;
  gates: CanonicalReadinessGate[];
  hashes: CanonicalReadinessHashes;
  marketSensitive: boolean;
  marketSnapshotRequired: boolean;
  passedGates: string[];
  platform: string;
  publicationAuthorityBlocker: string;
  publicationReadiness: ReadinessGateStatus;
  unresolvedBlockers: string[];
  visualPolicy: string;
}

export interface CanonicalStoryReadiness {
  applicableGates: string[];
  articleMode: string;
  dispatchReadiness: ReadinessGateStatus;
  editorialReadiness: ReadinessGateStatus;
  freshnessPolicy: string;
  gates: CanonicalReadinessGate[];
  marketSensitive: boolean;
  marketSnapshotRequired: boolean;
  passedGates: string[];
  publicationAuthorityBlocker: string;
  publicationReadiness: ReadinessGateStatus;
  storyType: string;
  unresolvedBlockers: string[];
  visualPolicy: string;
}

export interface CanonicalReviewStory {
  article: { body: string; hash: string; id: string; mode: string; title: string };
  authority: {
    artifactPath: string;
    byteLength: number;
    byteSha256: string;
    gitBlobSha1: string;
    packetId: string;
    packetLogicalHash: string;
    producerCommit: string;
    repository: string;
    sourceFamily: string;
    sourceUrl: string;
    storyLogicalHash: string;
  };
  blockers: {
    adversarial: string[];
    freshness: string[];
    unresolved: string[];
    visual: string[];
  };
  candidateId: string;
  claims: CanonicalReviewClaim[];
  editorialState: string;
  limitations: string[];
  packageHash: string;
  readiness: CanonicalStoryReadiness;
  recommendation: typeof CANONICAL_REVIEW_RECOMMENDATION;
  roles: CanonicalReviewRole[];
  state: string;
  storyId: string;
  variants: CanonicalReviewVariant[];
  v3PacketId: string;
  v3PacketLogicalHash: string;
}

type EditorialOutcome = (typeof editorialEvidence.outcomes)[number];
type OperatorPackage = (typeof packageEvidence.packages)[number];

interface CapabilityRow {
  article_mode?: string;
  freshness_policy?: string;
  freshness_requirements?: Record<string, unknown>;
  market_context_required?: boolean;
  market_sensitive?: boolean;
  market_snapshot_required?: boolean;
  source_family_ids?: string[];
  visual_policy?: string;
  visual_requirements?: Record<string, unknown>;
}

interface CapabilityRegistry {
  platform_visual_expectations: Record<string, {
    minimum_visual_count: number;
    policy: string;
    requires_lead_visual: boolean;
    requires_visual_diversity: boolean;
  }>;
  story_types: Record<string, CapabilityRow>;
}

const capabilityRegistry = sourceCapabilityRegistry as unknown as CapabilityRegistry;

export interface CanonicalVariantJoinInput {
  authorizedClaimIds: string[];
  candidateId: string;
  limitations: string[];
  storyId: string;
  variantPayloadHashes: Record<string, string>;
}

export const canonicalVariantEvidenceRecords =
  variantEvidence.variants as CanonicalVariantEvidenceRecord[];

function exactStringSet(left: readonly string[], right: readonly string[]): boolean {
  return (
    left.length === right.length &&
    [...left].sort().every((value, index) => value === [...right].sort()[index])
  );
}

function unique(values: readonly string[]): string[] {
  return [...new Set(values)];
}

function resolveStoryCapability(sourceFamily: string, articleMode: string): { row: CapabilityRow; storyType: string } {
  const matches = Object.entries(capabilityRegistry.story_types).filter(([, row]) =>
    row.source_family_ids?.includes(sourceFamily),
  );
  if (matches.length !== 1) {
    throw new Error(`Capability registry mismatch for source family: ${sourceFamily}`);
  }
  const [storyType, row] = matches[0];
  if (row.article_mode && row.article_mode !== articleMode) {
    throw new Error(`Capability article mode mismatch: ${sourceFamily}`);
  }
  return { row, storyType };
}

function isMarketSnapshotBlocker(value: string): boolean {
  return value === 'market_sensitive_story_snapshot_stale_or_missing' ||
    value === 'market_sensitive_story_ingest_stale_or_missing';
}

function buildReadiness(
  operatorPackage: OperatorPackage,
  variants: CanonicalJoinedVariant[],
  article: CanonicalReviewStory['article'],
  sourceFamily: string,
): { story: CanonicalStoryReadiness; platforms: Map<string, CanonicalPlatformReadiness> } {
  const capability = resolveStoryCapability(sourceFamily, article.mode);
  const articleVisualRequirements = capability.row.visual_requirements ?? {};
  const marketSnapshotRequired = Boolean(
    capability.row.market_snapshot_required ?? capability.row.market_context_required,
  );
  const marketSensitive = Boolean(
    capability.row.market_sensitive ?? capability.row.market_snapshot_required ?? capability.row.market_context_required,
  );
  const rawFreshnessBlockers = operatorPackage.editorial_binding.freshness_disposition.blockers;
  const nonMarketFreshnessBlockers = rawFreshnessBlockers.filter((blocker) =>
    !isMarketSnapshotBlocker(blocker) && !blocker.includes('permission'),
  );
  const visualBlockers = operatorPackage.editorial_binding.visual_disposition.blockers;
  const unresolvedBlockers = unique(
    operatorPackage.editorial_binding.unresolved_blockers.filter((blocker) =>
      marketSnapshotRequired || !isMarketSnapshotBlocker(blocker),
    ),
  );
  const editorialReviewBlockers = unresolvedBlockers.filter((blocker) =>
    !rawFreshnessBlockers.includes(blocker) &&
    !visualBlockers.includes(blocker) &&
    !blocker.includes('visual_editor') &&
    !blocker.includes('permission'),
  );
  const storyGates: CanonicalReadinessGate[] = [
    {
      id: 'article_mode',
      category: 'editorial',
      detail: `${article.mode} derived from ${capability.storyType} capability`,
      blockers: [],
      status: 'PASS',
    },
    {
      id: 'editorial_review',
      category: 'editorial',
      detail: 'Existing canonical editorial review remains authoritative',
      blockers: editorialReviewBlockers,
      status: editorialReviewBlockers.length ? 'BLOCK' : 'PASS',
    },
    {
      id: 'claim_permissions',
      category: 'authority',
      detail: 'Exact approved claim permission remains authoritative',
      blockers: unresolvedBlockers.filter((blocker) => blocker.includes('permission')),
      status: unresolvedBlockers.some((blocker) => blocker.includes('permission')) ? 'BLOCK' : 'PASS',
    },
    {
      id: 'freshness',
      category: 'freshness',
      detail: `${capability.row.freshness_policy ?? 'registry'} freshness policy`,
      blockers: nonMarketFreshnessBlockers,
      status: nonMarketFreshnessBlockers.length ? 'BLOCK' : 'PASS',
    },
    {
      id: 'market_snapshot',
      category: 'freshness',
      detail: marketSnapshotRequired ? 'Current market snapshot required by capability' : 'Not required for this physical-event capability',
      blockers: marketSnapshotRequired ? rawFreshnessBlockers.filter(isMarketSnapshotBlocker) : [],
      status: marketSnapshotRequired
        ? (rawFreshnessBlockers.some(isMarketSnapshotBlocker) ? 'BLOCK' : 'PASS')
        : 'NOT_APPLICABLE',
    },
    {
      id: 'article_visuals',
      category: 'visual',
      detail: `${capability.row.visual_policy ?? 'long_form_article'} visual policy; minimum ${String(articleVisualRequirements.minimum_visual_count ?? 0)} visuals`,
      blockers: visualBlockers,
      status: visualBlockers.length ? 'BLOCK' : 'PASS',
    },
    {
      id: 'publication_authority',
      category: 'authority',
      detail: 'Unsigned package has no publication authority',
      blockers: ['publication_authority_not_granted'],
      status: 'BLOCK',
    },
  ];
  const storyPassed = storyGates.filter((gate) => gate.status === 'PASS').map((gate) => gate.id);
  const storyApplicable = storyGates.filter((gate) => gate.status !== 'NOT_APPLICABLE').map((gate) => gate.id);
  const storyEditorialReadiness: ReadinessGateStatus = storyGates.some((gate) =>
    ['editorial', 'freshness', 'visual'].includes(gate.category) && gate.status === 'BLOCK',
  ) ? 'BLOCK' : 'PASS';
  const storyReadiness: CanonicalStoryReadiness = {
    applicableGates: storyApplicable,
    articleMode: article.mode,
    dispatchReadiness: 'BLOCK',
    editorialReadiness: storyEditorialReadiness,
    freshnessPolicy: String(capability.row.freshness_policy ?? 'registry'),
    gates: storyGates,
    marketSensitive,
    marketSnapshotRequired,
    passedGates: storyPassed,
    publicationAuthorityBlocker: 'publication_authority_not_granted',
    publicationReadiness: 'BLOCK',
    storyType: capability.storyType,
    unresolvedBlockers: unique([
      ...unresolvedBlockers,
      ...storyGates.flatMap((gate) => gate.blockers),
    ]),
    visualPolicy: String(capability.row.visual_policy ?? 'long_form_article'),
  };
  const platforms = new Map<string, CanonicalPlatformReadiness>();
  for (const variant of variants) {
    const expectation = capabilityRegistry.platform_visual_expectations[variant.platform];
    if (!expectation) throw new Error(`Platform capability missing: ${variant.platform}`);
    const visualApplicable = expectation.minimum_visual_count > 0;
    const platformBaseBlockers = unresolvedBlockers.filter((blocker) =>
      visualApplicable || (
        !visualBlockers.includes(blocker) && !blocker.includes('visual_editor')
      ),
    );
    const visualGate: CanonicalReadinessGate = {
      id: 'platform_visuals',
      category: 'visual',
      detail: visualApplicable ? 'Long-form platform inherits article visual gate' : 'Text-only surface does not require article visuals',
      blockers: visualApplicable ? visualBlockers : [],
      status: visualApplicable ? (visualBlockers.length ? 'BLOCK' : 'PASS') : 'NOT_APPLICABLE',
    };
    const platformGates: CanonicalReadinessGate[] = storyGates
      .filter((gate) => gate.id !== 'article_visuals')
      .concat(visualGate, {
        id: 'dispatch_authorization',
        category: 'dispatch',
        detail: 'Variant is review-only and not dispatch-ready',
        blockers: ['dispatch_not_authorized'],
        status: 'BLOCK',
      });
    const platformPassed = platformGates.filter((gate) => gate.status === 'PASS').map((gate) => gate.id);
    const platformApplicable = platformGates.filter((gate) => gate.status !== 'NOT_APPLICABLE').map((gate) => gate.id);
    const platformEditorial: ReadinessGateStatus = platformGates.some((gate) =>
      ['editorial', 'freshness', 'visual'].includes(gate.category) && gate.status === 'BLOCK',
    ) ? 'BLOCK' : 'PASS';
    platforms.set(variant.platform, {
      applicableGates: platformApplicable,
      articleMode: article.mode,
      dispatchReadiness: 'BLOCK',
      editorialReadiness: platformEditorial,
      freshnessPolicy: String(capability.row.freshness_policy ?? 'registry'),
      gates: platformGates,
      hashes: {
        articleHash: article.hash,
        packageHash: operatorPackage.package_hash,
        v3PacketHash: operatorPackage.editorial_binding.v3_packet_logical_hash,
        variantHash: variant.payloadHash,
      },
      marketSensitive,
      marketSnapshotRequired,
      passedGates: platformPassed,
      platform: variant.platform,
      publicationAuthorityBlocker: 'publication_authority_not_granted',
      publicationReadiness: 'BLOCK',
      unresolvedBlockers: unique([
        ...platformBaseBlockers,
        ...platformGates.flatMap((gate) => gate.blockers),
      ]),
      visualPolicy: expectation.policy,
    });
  }
  return { story: storyReadiness, platforms };
}

export function joinCanonicalVariantEvidence(
  input: CanonicalVariantJoinInput,
  records: readonly CanonicalVariantEvidenceRecord[],
): CanonicalJoinedVariant[] {
  const expectedPlatforms = Object.keys(input.variantPayloadHashes);
  const storyRecords = records.filter((record) => record.story_id === input.storyId);
  if (storyRecords.length !== expectedPlatforms.length) {
    throw new Error(`Canonical variant count mismatch: ${input.storyId}`);
  }

  return expectedPlatforms.map((platform) => {
    const matches = storyRecords.filter(
      (record) =>
        record.candidate_id === input.candidateId &&
        record.platform_id === platform,
    );
    if (matches.length !== 1) {
      throw new Error(
        `Canonical variant missing or duplicate: ${input.storyId}:${platform}`,
      );
    }
    const record = matches[0];
    if (record.payload_hash !== input.variantPayloadHashes[platform]) {
      throw new Error(`Canonical variant payload hash mismatch: ${input.storyId}:${platform}`);
    }
    if (!exactStringSet(record.authorized_claim_ids, input.authorizedClaimIds)) {
      throw new Error(`Canonical variant claim allowlist mismatch: ${input.storyId}:${platform}`);
    }
    if (record.character_count !== record.text.length) {
      throw new Error(`Canonical variant character count mismatch: ${input.storyId}:${platform}`);
    }
    if (record.character_count > record.character_limit_max) {
      throw new Error(`Canonical variant character limit exceeded: ${input.storyId}:${platform}`);
    }
    if (record.dispatch_ready || record.valid_for_dispatch) {
      throw new Error(`Canonical variant dispatch boundary mismatch: ${input.storyId}:${platform}`);
    }

    return {
      authorizedClaimIds: [...record.authorized_claim_ids],
      characterCount: record.character_count,
      characterLimit: record.character_limit_max,
      citations: [...record.citation_urls],
      dispatchAuthorized: false,
      limitationFingerprints: [...record.limitation_fingerprints],
      limitations: [...input.limitations],
      mode: record.mode,
      payloadHash: record.payload_hash,
      platform: record.platform_id,
      surface: record.content_surface,
      text: record.text,
    };
  });
}

function claimSentences(outcome: EditorialOutcome): string[] {
  return outcome.canonical_article.rendered_body
    .split(/\n+/)
    .map((line) => line.trim())
    .filter((line) => line.length > 0 && line !== 'Not financial advice.');
}

function buildClaims(outcome: EditorialOutcome): CanonicalReviewClaim[] {
  const sentences = claimSentences(outcome);
  const authorities = outcome.canonical_article.claim_authority_used as unknown as Record<string, string>;
  const citations = outcome.citations as unknown as Record<string, string[]>;
  const permissions = outcome.canonical_article.claim_permissions_used as unknown as Record<string, string>;
  return outcome.article_used_approved_claim_ids.map((id, index) => ({
    authority: authorities[id] ?? 'UNKNOWN',
    citations: citations[id] ?? [],
    id,
    permission: permissions[id] ?? 'UNKNOWN',
    text: sentences[index] ?? outcome.canonical_article.summary,
  }));
}

function joinStory(
  operatorPackage: OperatorPackage,
  outcome: EditorialOutcome,
): CanonicalReviewStory {
  if (operatorPackage.story_id !== outcome.story_id) {
    throw new Error(`Canonical story identity mismatch: ${operatorPackage.story_id}`);
  }
  if (
    operatorPackage.editorial_binding.canonical_article_hash !==
    outcome.canonical_article_hash
  ) {
    throw new Error(`Canonical article hash mismatch: ${operatorPackage.story_id}`);
  }

  const receipt = operatorPackage.authority_binding.exact_git_receipt;
  const article = {
      body: outcome.canonical_article.rendered_body,
      hash: outcome.canonical_article_hash,
      id: outcome.canonical_article_id,
      mode: outcome.canonical_article.article_mode,
      title: outcome.canonical_article.title,
  };
  const variants = joinCanonicalVariantEvidence(
    {
      authorizedClaimIds: [...operatorPackage.authority_binding.authorized_claim_ids],
      candidateId: operatorPackage.candidate_id,
      limitations: [...operatorPackage.editorial_binding.limitations],
      storyId: operatorPackage.story_id,
      variantPayloadHashes: operatorPackage.variant_payload_hashes,
    },
    canonicalVariantEvidenceRecords,
  );
  const readiness = buildReadiness(
    operatorPackage,
    variants,
    article,
    operatorPackage.authority_binding.source_family,
  );
  return {
    article,
    authority: {
      artifactPath: receipt.artifact_path,
      byteLength: receipt.byte_length,
      byteSha256: receipt.byte_sha256,
      gitBlobSha1: receipt.git_blob_sha1,
      packetId: operatorPackage.authority_binding.authority_packet_id,
      packetLogicalHash: operatorPackage.authority_binding.authority_packet_logical_hash,
      producerCommit: receipt.producer_commit,
      repository: receipt.repository,
      sourceFamily: operatorPackage.authority_binding.source_family,
      sourceUrl: operatorPackage.authority_binding.official_url,
      storyLogicalHash: operatorPackage.authority_binding.story_logical_hash,
    },
    blockers: {
      adversarial:
        operatorPackage.editorial_binding.final_adversarial_review_disposition.blockers,
      freshness: operatorPackage.editorial_binding.freshness_disposition.blockers,
      unresolved: operatorPackage.editorial_binding.unresolved_blockers,
      visual: operatorPackage.editorial_binding.visual_disposition.blockers,
    },
    candidateId: operatorPackage.candidate_id,
    claims: buildClaims(outcome),
    editorialState: operatorPackage.editorial_binding.editorial_state,
    limitations: operatorPackage.editorial_binding.limitations,
    packageHash: operatorPackage.package_hash,
    recommendation: CANONICAL_REVIEW_RECOMMENDATION,
    readiness: readiness.story,
    roles: outcome.role_outcomes.map((role) => ({
      blockers: role.blockers,
      decision: role.structured_review.decision,
      outputHash: role.output_hash,
      role: role.role,
      status: role.status,
    })),
    state: operatorPackage.state,
    storyId: operatorPackage.story_id,
    variants: variants.map((variant) => ({
      ...variant,
      readiness: readiness.platforms.get(variant.platform)!,
    })),
    v3PacketId: operatorPackage.editorial_binding.v3_packet_id,
    v3PacketLogicalHash: operatorPackage.editorial_binding.v3_packet_logical_hash,
  };
}

export function buildCanonicalReviewStories(): CanonicalReviewStory[] {
  return packageEvidence.packages.map((operatorPackage) => {
    const outcome = editorialEvidence.outcomes.find(
      (item) => item.story_id === operatorPackage.story_id,
    );
    if (!outcome) {
      throw new Error(`Missing canonical editorial outcome: ${operatorPackage.story_id}`);
    }
    return joinStory(operatorPackage, outcome);
  });
}

export const canonicalReviewStories: CanonicalReviewStory[] = buildCanonicalReviewStories();

export const canonicalReviewSummary = {
  blockerCount: canonicalReviewStories.reduce(
    (count, story) => count + story.blockers.unresolved.length,
    0,
  ),
  packageCount: canonicalReviewStories.length,
  recommendation: CANONICAL_REVIEW_RECOMMENDATION,
  roleCount: canonicalReviewStories.reduce(
    (count, story) => count + story.roles.length,
    0,
  ),
  surfaceMode: CANONICAL_REVIEW_SURFACE_MODE,
  variantCount: canonicalReviewStories.reduce(
    (count, story) => count + story.variants.length,
    0,
  ),
};

function roleStatus(status: string): StatusKind {
  return status === 'PASS' ? 'verified' : 'blocked';
}

export function selectCanonicalReviewStory(
  story: CanonicalReviewStory,
): SelectableObject {
  return {
    fields: [
      { label: 'State', value: story.state, status: 'review' },
      { label: 'Recommendation', value: story.recommendation, status: 'blocked' },
      { label: 'Editorial', value: story.editorialState, status: 'blocked' },
      { label: 'Source family', value: story.authority.sourceFamily },
      { label: 'V3 packet', value: story.v3PacketId, mono: true },
      { label: 'Article', value: story.article.id, mono: true },
      { label: 'Package hash', value: story.packageHash, mono: true },
    ],
    id: story.storyId,
    kind: 'canonical_operator_package',
    title: story.article.title,
  };
}

export function selectCanonicalReviewRole(
  story: CanonicalReviewStory,
  role: CanonicalReviewRole,
): SelectableObject {
  return {
    fields: [
      { label: 'Story', value: story.storyId, mono: true },
      { label: 'Status', value: role.status, status: roleStatus(role.status) },
      { label: 'Decision', value: role.decision, status: roleStatus(role.status) },
      { label: 'Blockers', value: role.blockers.join(', ') || 'None' },
      { label: 'Output hash', value: role.outputHash, mono: true },
    ],
    id: `${story.storyId}:${role.role}`,
    kind: 'canonical_editorial_role_outcome',
    title: role.role,
  };
}

export function selectCanonicalReviewVariant(
  story: CanonicalReviewStory,
  variant: CanonicalReviewVariant,
): SelectableObject {
  return {
    fields: [
      { label: 'Story', value: story.storyId, mono: true },
      { label: 'Platform', value: variant.platform },
      { label: 'Surface', value: variant.surface },
      { label: 'Mode', value: variant.mode },
      {
        label: 'Characters',
        value: `${variant.characterCount} / ${variant.characterLimit}`,
      },
      { label: 'Claims', value: variant.authorizedClaimIds.join(', '), mono: true },
      { label: 'Dispatch', value: 'NOT_AUTHORIZED', status: 'blocked' },
      { label: 'Payload hash', value: variant.payloadHash, mono: true },
      { label: 'Package hash', value: story.packageHash, mono: true },
    ],
    id: `${story.storyId}:${variant.platform}`,
    kind: 'canonical_platform_variant',
    title: variant.platform,
  };
}
