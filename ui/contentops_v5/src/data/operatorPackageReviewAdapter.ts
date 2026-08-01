// Capital Chronicle ContentOps V5 — canonical package review read model.
// Static imports only. No network, storage, credentials, or decision execution.

import editorialEvidence from '../../../../docs/automation/CONTENTOPS_FAST_SHIP_STORY_SCOPED_PERMISSION_AND_FIRST_TEXT_ONLY_OPERATOR_READY_PACKAGE_V1/canonical_editorial_outcomes.json';
import packageEvidence from '../../../../docs/automation/CONTENTOPS_FAST_SHIP_STORY_SCOPED_PERMISSION_AND_FIRST_TEXT_ONLY_OPERATOR_READY_PACKAGE_V1/superseding_unsigned_operator_packages.json';
import variantEvidence from '../../../../docs/automation/CONTENTOPS_FAST_SHIP_STORY_SCOPED_PERMISSION_AND_FIRST_TEXT_ONLY_OPERATOR_READY_PACKAGE_V1/platform_native_variants.json';
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
  readinessHash: string;
  v3PacketHash: string;
  variantHash: string;
  visualPolicyHash: string;
}

export interface CanonicalPlatformReadiness {
  applicableGates: string[];
  articleMode: string;
  canonicalPackageEvidenceUnchanged: true;
  contentSurface: string;
  dispatchAuthority: false;
  dispatchReadiness: ReadinessGateStatus;
  editorialReadiness: ReadinessGateStatus;
  effectivePlatformVisualMode: string;
  freshnessPolicy: string;
  gates: CanonicalReadinessGate[];
  hashes: CanonicalReadinessHashes;
  marketSensitive: boolean;
  marketSnapshotRequired: boolean;
  operatorDecisionState: 'PENDING_OPERATOR_DECISION';
  operatorReadyForDecision: boolean;
  passedGates: string[];
  platform: string;
  publicationAuthority: false;
  publicationAuthorityBlocker: string;
  publicationReadiness: ReadinessGateStatus;
  readinessOverlay: 'DERIVED_READINESS_OVERLAY';
  unresolvedBlockers: string[];
  variantMode: string;
  visualPolicy: string;
}

export interface CanonicalStoryReadiness {
  applicableGates: string[];
  articleMode: string;
  canonicalEditorialState: string;
  canonicalPackageEvidenceUnchanged: true;
  canonicalPackageState: string;
  dispatchAuthority: false;
  dispatchReadiness: ReadinessGateStatus;
  editorialReadiness: ReadinessGateStatus;
  freshnessPolicy: string;
  gates: CanonicalReadinessGate[];
  marketSensitive: boolean;
  marketSnapshotRequired: boolean;
  passedGates: string[];
  publicationAuthority: false;
  publicationAuthorityBlocker: string;
  publicationReadiness: ReadinessGateStatus;
  readinessHash: string;
  readinessOverlay: 'DERIVED_READINESS_OVERLAY';
  storyType: string;
  unresolvedBlockers: string[];
  visualPolicyHash: string;
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

export interface CapabilityRow {
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

export interface PlatformVisualRule {
    content_surface: string;
    effective_visual_mode: string;
    minimum_visual_count: number;
    policy: string;
    requires_lead_visual: boolean;
    requires_visual_diversity: boolean;
    variant_mode: string;
}

export interface CapabilityRegistry {
  platform_visual_expectations: Record<string, {
    rules: PlatformVisualRule[];
  }>;
  story_types: Record<string, CapabilityRow>;
}

const capabilityRegistry = sourceCapabilityRegistry as unknown as CapabilityRegistry;

const SHA256_INITIAL = [
  0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
  0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19,
];
const SHA256_K = [
  0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
  0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
  0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
  0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
  0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
  0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
  0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
  0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
];

function canonicalJson(value: unknown): string {
  if (value === undefined) return 'null';
  if (value === null || typeof value !== 'object') return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(',')}]`;
  const row = value as Record<string, unknown>;
  return `{${Object.keys(row).sort().map((key) => `${JSON.stringify(key)}:${canonicalJson(row[key])}`).join(',')}}`;
}

export function sha256Canonical(value: unknown): string {
  const bytes = [...new TextEncoder().encode(canonicalJson(value))];
  const bitLength = bytes.length * 8;
  bytes.push(0x80);
  while (bytes.length % 64 !== 56) bytes.push(0);
  for (let shift = 56; shift >= 32; shift -= 8) bytes.push(0);
  for (let shift = 24; shift >= 0; shift -= 8) bytes.push((bitLength >>> shift) & 0xff);
  const hash = [...SHA256_INITIAL];
  const rotateRight = (value32: number, bits: number) => (value32 >>> bits) | (value32 << (32 - bits));
  for (let offset = 0; offset < bytes.length; offset += 64) {
    const words = new Array<number>(64).fill(0);
    for (let index = 0; index < 16; index += 1) {
      const cursor = offset + index * 4;
      words[index] = ((bytes[cursor] << 24) | (bytes[cursor + 1] << 16) | (bytes[cursor + 2] << 8) | bytes[cursor + 3]) >>> 0;
    }
    for (let index = 16; index < 64; index += 1) {
      const s0 = rotateRight(words[index - 15], 7) ^ rotateRight(words[index - 15], 18) ^ (words[index - 15] >>> 3);
      const s1 = rotateRight(words[index - 2], 17) ^ rotateRight(words[index - 2], 19) ^ (words[index - 2] >>> 10);
      words[index] = (words[index - 16] + s0 + words[index - 7] + s1) >>> 0;
    }
    let [a, b, c, d, e, f, g, h] = hash;
    for (let index = 0; index < 64; index += 1) {
      const sum1 = rotateRight(e, 6) ^ rotateRight(e, 11) ^ rotateRight(e, 25);
      const choice = (e & f) ^ (~e & g);
      const temp1 = (h + sum1 + choice + SHA256_K[index] + words[index]) >>> 0;
      const sum0 = rotateRight(a, 2) ^ rotateRight(a, 13) ^ rotateRight(a, 22);
      const majority = (a & b) ^ (a & c) ^ (b & c);
      const temp2 = (sum0 + majority) >>> 0;
      [a, b, c, d, e, f, g, h] = [(temp1 + temp2) >>> 0, a, b, c, (d + temp1) >>> 0, e, f, g];
    }
    [a, b, c, d, e, f, g, h].forEach((value32, index) => {
      hash[index] = (hash[index] + value32) >>> 0;
    });
  }
  return hash.map((value32) => value32.toString(16).padStart(8, '0')).join('');
}

export interface ResolvedPlatformVisualExpectation extends PlatformVisualRule {
  blockers: string[];
  status: 'PASS' | 'BLOCK';
}

const VALID_ARTICLE_MODES = new Set([
  'analysis',
  'correction',
  'data_release',
  'deep_analysis',
  'explainer',
  'live_update',
  'market_move',
  'policy_decision',
  'retrospective',
  'scenario_outlook',
  'straight_news',
]);

export function resolvePlatformVisualExpectation(
  platform: string,
  contentSurface: string,
  variantMode: string,
  registryInput: CapabilityRegistry = capabilityRegistry,
): ResolvedPlatformVisualExpectation {
  const matches = (registryInput.platform_visual_expectations[platform]?.rules ?? []).filter(
    (rule) => rule.content_surface === contentSurface && rule.variant_mode === variantMode,
  );
  if (matches.length !== 1) {
    return {
      blockers: [matches.length > 1 ? 'ambiguous_platform_visual_mode' : 'unsupported_platform_visual_mode'],
      content_surface: contentSurface,
      effective_visual_mode: 'fail_closed_visual_required',
      minimum_visual_count: 1,
      policy: 'fail_closed_unregistered_visual_mode',
      requires_lead_visual: false,
      requires_visual_diversity: false,
      status: 'BLOCK',
      variant_mode: variantMode,
    };
  }
  const rule = matches[0];
  const malformed = !rule.effective_visual_mode ||
    !rule.policy ||
    !Number.isInteger(rule.minimum_visual_count) ||
    rule.minimum_visual_count < 0 ||
    (rule.effective_visual_mode !== 'text_only' && rule.minimum_visual_count === 0);
  if (malformed) {
    return {
      blockers: ['malformed_platform_visual_policy'],
      content_surface: contentSurface,
      effective_visual_mode: 'fail_closed_visual_required',
      minimum_visual_count: 1,
      policy: 'fail_closed_unregistered_visual_mode',
      requires_lead_visual: false,
      requires_visual_diversity: false,
      status: 'BLOCK',
      variant_mode: variantMode,
    };
  }
  return { ...rule, blockers: [], status: 'PASS' };
}

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

function resolveStoryCapability(
  sourceFamily: string,
  articleMode: string,
  registryInput: CapabilityRegistry,
): { row: CapabilityRow; storyType: string } {
  const matches = Object.entries(registryInput.story_types).filter(([, row]) =>
    row.source_family_ids?.includes(sourceFamily),
  );
  if (matches.length !== 1) {
    throw new Error(`Capability registry mismatch for source family: ${sourceFamily}`);
  }
  const [storyType, row] = matches[0];
  if (!articleMode) throw new Error(`Capability article mode unresolved: ${sourceFamily}`);
  if (!VALID_ARTICLE_MODES.has(articleMode)) {
    throw new Error(`Caller capability article mode invalid: ${sourceFamily}`);
  }
  if (row.article_mode && !VALID_ARTICLE_MODES.has(row.article_mode)) {
    throw new Error(`Registry capability article mode invalid: ${sourceFamily}`);
  }
  if (row.article_mode && row.article_mode !== articleMode) {
    throw new Error(`Capability article mode mismatch: ${sourceFamily}`);
  }
  return { row: { ...row, article_mode: row.article_mode ?? articleMode }, storyType };
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
  canonicalEditorialState: string,
  canonicalPackageState: string,
  roleOutcomes: EditorialOutcome['role_outcomes'],
  registryInput: CapabilityRegistry,
): { story: CanonicalStoryReadiness; platforms: Map<string, CanonicalPlatformReadiness> } {
  const capability = resolveStoryCapability(sourceFamily, article.mode, registryInput);
  const articleVisualRequirements = capability.row.visual_requirements ?? {};
  const marketSnapshotRequired = Boolean(
    capability.row.market_snapshot_required ?? capability.row.market_context_required,
  );
  const marketSensitive = Boolean(
    capability.row.market_sensitive ?? capability.row.market_snapshot_required ?? capability.row.market_context_required,
  );
  const rawFreshnessBlockers: string[] = [
    ...operatorPackage.editorial_binding.freshness_disposition.blockers,
  ];
  const nonMarketFreshnessBlockers = rawFreshnessBlockers.filter((blocker) =>
    !isMarketSnapshotBlocker(blocker) && !blocker.includes('permission'),
  );
  const visualBlockers: string[] = [
    ...operatorPackage.editorial_binding.visual_disposition.blockers,
  ];
  const unresolvedBlockers = unique(
    operatorPackage.editorial_binding.unresolved_blockers.filter((blocker) =>
      marketSnapshotRequired || !isMarketSnapshotBlocker(blocker),
    ),
  );
  const canonicalAdversarialBlockers: string[] = [
    ...operatorPackage.editorial_binding.final_adversarial_review_disposition.blockers,
  ];
  const editorialReviewBlockers = unresolvedBlockers.filter((blocker) =>
    !rawFreshnessBlockers.includes(blocker) &&
    !visualBlockers.includes(blocker) &&
    !blocker.includes('visual_editor') &&
    !canonicalAdversarialBlockers.includes(blocker) &&
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
      id: 'adversarial_review',
      category: 'editorial',
      detail: 'Canonical adversarial review across all story-level gates',
      blockers: canonicalAdversarialBlockers,
      status: canonicalAdversarialBlockers.length ? 'BLOCK' : 'PASS',
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
    (['editorial', 'freshness', 'visual'].includes(gate.category) || gate.id === 'claim_permissions') &&
    gate.status === 'BLOCK',
  ) ? 'BLOCK' : 'PASS';
  const storyUnresolved = unique([
    ...unresolvedBlockers,
    ...storyGates.flatMap((gate) => gate.blockers),
  ]);
  const storyVisualPolicyHash = sha256Canonical({
    articleMode: article.mode,
    marketSensitive,
    marketSnapshotRequired,
    storyType: capability.storyType,
    visualPolicy: capability.row.visual_policy ?? 'long_form_article',
    visualRequirements: articleVisualRequirements,
  });
  const storyReadinessHash = sha256Canonical({
    applicableGates: storyApplicable,
    articleHash: article.hash,
    articleMode: article.mode,
    canonicalEditorialState,
    canonicalPackageState,
    dispatchAuthority: false,
    editorialReadiness: storyEditorialReadiness,
    gates: storyGates,
    marketSensitive,
    marketSnapshotRequired,
    packageHash: operatorPackage.package_hash,
    publicationAuthority: false,
    readinessOverlay: 'DERIVED_READINESS_OVERLAY',
    storyType: capability.storyType,
    unresolvedBlockers: storyUnresolved,
    v3PacketHash: operatorPackage.editorial_binding.v3_packet_logical_hash,
    visualPolicyHash: storyVisualPolicyHash,
  });
  const storyReadiness: CanonicalStoryReadiness = {
    applicableGates: storyApplicable,
    articleMode: article.mode,
    canonicalEditorialState,
    canonicalPackageEvidenceUnchanged: true,
    canonicalPackageState,
    dispatchAuthority: false,
    dispatchReadiness: 'BLOCK',
    editorialReadiness: storyEditorialReadiness,
    freshnessPolicy: String(capability.row.freshness_policy ?? 'registry'),
    gates: storyGates,
    marketSensitive,
    marketSnapshotRequired,
    passedGates: storyPassed,
    publicationAuthority: false,
    publicationAuthorityBlocker: 'publication_authority_not_granted',
    publicationReadiness: 'BLOCK',
    readinessHash: storyReadinessHash,
    readinessOverlay: 'DERIVED_READINESS_OVERLAY',
    storyType: capability.storyType,
    unresolvedBlockers: storyUnresolved,
    visualPolicyHash: storyVisualPolicyHash,
    visualPolicy: String(capability.row.visual_policy ?? 'long_form_article'),
  };
  const platforms = new Map<string, CanonicalPlatformReadiness>();
  for (const variant of variants) {
    const expectation = resolvePlatformVisualExpectation(
      variant.platform,
      variant.surface,
      variant.mode,
      registryInput,
    );
    const visualApplicable = expectation.status === 'BLOCK' || expectation.minimum_visual_count > 0;
    const finalAdversarial =
      operatorPackage.editorial_binding.final_adversarial_review_disposition;
    const finalChecks = finalAdversarial.structured_review.checks;
    const nonVisualPriorRoleBlocked = roleOutcomes.some((role) =>
      role.role !== 'visual_editor' &&
      role.role !== 'adversarial_final_reviewer' &&
      role.status !== 'PASS',
    );
    const nonVisualAdversarialChecksPass = Object.entries(finalChecks).every(
      ([name, passed]) => name === 'prior_roles_clear' || passed === true,
    );
    const textOnlyVisualWaiverResolvesAdversarial =
      !visualApplicable &&
      !nonVisualPriorRoleBlocked &&
      nonVisualAdversarialChecksPass &&
      finalAdversarial.structured_review.blockers.every(
        (blocker) => blocker === 'prior_roles_clear',
      );
    const platformAdversarialBlockers = textOnlyVisualWaiverResolvesAdversarial
      ? []
      : canonicalAdversarialBlockers;
    const platformBaseBlockers = unresolvedBlockers.filter((blocker) =>
      (visualApplicable || (
        !visualBlockers.includes(blocker) && !blocker.includes('visual_editor')
      )) &&
      (!textOnlyVisualWaiverResolvesAdversarial || !canonicalAdversarialBlockers.includes(blocker)),
    );
    const visualGate: CanonicalReadinessGate = {
      id: 'platform_visuals',
      category: 'visual',
      detail: expectation.status === 'BLOCK'
        ? 'Unregistered platform, surface, and variant-mode combination fails closed'
        : visualApplicable
          ? 'Registered visual mode inherits the applicable article visual gate'
          : 'Exact registered text-only mode does not require article visuals',
      blockers: expectation.status === 'BLOCK' ? expectation.blockers : (visualApplicable ? visualBlockers : []),
      status: expectation.status === 'BLOCK'
        ? 'BLOCK'
        : visualApplicable
          ? (visualBlockers.length ? 'BLOCK' : 'PASS')
          : 'NOT_APPLICABLE',
    };
    const platformGates: CanonicalReadinessGate[] = storyGates
      .filter((gate) => gate.id !== 'article_visuals' && gate.id !== 'adversarial_review')
      .concat({
        id: 'adversarial_review',
        category: 'editorial',
        detail: textOnlyVisualWaiverResolvesAdversarial
          ? 'Applicable nonvisual adversarial checks pass; canonical long-form visual HOLD remains unchanged'
          : 'Canonical adversarial review remains blocked by an applicable gate',
        blockers: platformAdversarialBlockers,
        status: platformAdversarialBlockers.length ? 'BLOCK' : 'PASS',
      })
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
      (['editorial', 'freshness', 'visual'].includes(gate.category) || gate.id === 'claim_permissions') &&
      gate.status === 'BLOCK',
    ) ? 'BLOCK' : 'PASS';
    const platformUnresolved = unique([
      ...platformBaseBlockers,
      ...platformGates.flatMap((gate) => gate.blockers),
    ]);
    const visualPolicyHash = sha256Canonical({
      articleMode: article.mode,
      contentSurface: variant.surface,
      effectivePlatformVisualMode: expectation.effective_visual_mode,
      marketSensitive,
      marketSnapshotRequired,
      platform: variant.platform,
      requirements: {
        minimumVisualCount: expectation.minimum_visual_count,
        requiresLeadVisual: expectation.requires_lead_visual,
        requiresVisualDiversity: expectation.requires_visual_diversity,
      },
      storyType: capability.storyType,
      variantMode: variant.mode,
      visualPolicy: expectation.policy,
    });
    const readinessHash = sha256Canonical({
      applicableGates: platformApplicable,
      articleHash: article.hash,
      articleMode: article.mode,
      canonicalEditorialState,
      canonicalPackageState,
      contentSurface: variant.surface,
      dispatchAuthority: false,
      editorialReadiness: platformEditorial,
      effectivePlatformVisualMode: expectation.effective_visual_mode,
      gates: platformGates,
      marketSensitive,
      marketSnapshotRequired,
      operatorDecisionState: 'PENDING_OPERATOR_DECISION',
      operatorReadyForDecision: platformEditorial === 'PASS',
      packageHash: operatorPackage.package_hash,
      platform: variant.platform,
      publicationAuthority: false,
      readinessOverlay: 'DERIVED_READINESS_OVERLAY',
      storyType: capability.storyType,
      unresolvedBlockers: platformUnresolved,
      v3PacketHash: operatorPackage.editorial_binding.v3_packet_logical_hash,
      variantHash: variant.payloadHash,
      variantMode: variant.mode,
      visualPolicyHash,
    });
    platforms.set(variant.platform, {
      applicableGates: platformApplicable,
      articleMode: article.mode,
      canonicalPackageEvidenceUnchanged: true,
      contentSurface: variant.surface,
      dispatchAuthority: false,
      dispatchReadiness: 'BLOCK',
      editorialReadiness: platformEditorial,
      effectivePlatformVisualMode: expectation.effective_visual_mode,
      freshnessPolicy: String(capability.row.freshness_policy ?? 'registry'),
      gates: platformGates,
      hashes: {
        articleHash: article.hash,
        packageHash: operatorPackage.package_hash,
        readinessHash,
        v3PacketHash: operatorPackage.editorial_binding.v3_packet_logical_hash,
        variantHash: variant.payloadHash,
        visualPolicyHash,
      },
      marketSensitive,
      marketSnapshotRequired,
      operatorDecisionState: 'PENDING_OPERATOR_DECISION',
      operatorReadyForDecision: platformEditorial === 'PASS',
      passedGates: platformPassed,
      platform: variant.platform,
      publicationAuthority: false,
      publicationAuthorityBlocker: 'publication_authority_not_granted',
      publicationReadiness: 'BLOCK',
      readinessOverlay: 'DERIVED_READINESS_OVERLAY',
      unresolvedBlockers: platformUnresolved,
      variantMode: variant.mode,
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
  registryInput: CapabilityRegistry,
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
    operatorPackage.editorial_binding.editorial_state,
    operatorPackage.state,
    outcome.role_outcomes,
    registryInput,
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

export function buildCanonicalReviewStories(
  registryInput: CapabilityRegistry = capabilityRegistry,
): CanonicalReviewStory[] {
  return packageEvidence.packages.map((operatorPackage) => {
    const outcome = editorialEvidence.outcomes.find(
      (item) => item.story_id === operatorPackage.story_id,
    );
    if (!outcome) {
      throw new Error(`Missing canonical editorial outcome: ${operatorPackage.story_id}`);
    }
    return joinStory(operatorPackage, outcome, registryInput);
  });
}

export const canonicalReviewStories: CanonicalReviewStory[] = buildCanonicalReviewStories();

export const canonicalReviewSummary = {
  blockerCount: canonicalReviewStories.reduce(
    (count, story) => count + story.blockers.unresolved.length,
    0,
  ),
  packageCount: canonicalReviewStories.length,
  operatorReadyVariantCount: canonicalReviewStories.reduce(
    (count, story) => count + story.variants.filter(
      (variant) => variant.readiness.operatorReadyForDecision,
    ).length,
    0,
  ),
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
