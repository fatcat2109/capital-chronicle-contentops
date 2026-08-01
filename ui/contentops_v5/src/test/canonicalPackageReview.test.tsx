// Canonical three-story package review console — evidence and interaction tests.

import { fireEvent, render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import App from '../App';
import sourceCapabilityRegistry from '../../../../docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/source_evidence_capability_registry_v2.json';
import {
  buildCanonicalReviewStories,
  canonicalReviewStories,
  canonicalReviewSummary,
  canonicalVariantEvidenceRecords,
  joinCanonicalVariantEvidence,
  resolvePlatformVisualExpectation,
  sha256Canonical,
  type CapabilityRegistry,
  type CanonicalVariantJoinInput,
} from '../data/operatorPackageReviewAdapter';

describe('canonical package evidence adapter', () => {
  it('joins exactly three packages with eight roles and six variants each', () => {
    expect(canonicalReviewStories).toHaveLength(3);
    expect(canonicalReviewSummary.roleCount).toBe(24);
    expect(canonicalReviewSummary.variantCount).toBe(18);
    for (const story of canonicalReviewStories) {
      expect(story.roles).toHaveLength(8);
      expect(story.variants).toHaveLength(6);
      expect(story.state).toBe('PENDING_OPERATOR_DECISION');
      expect(story.editorialState).toBe('HOLD');
      expect(story.recommendation).toBe('REQUEST_REVISION');
      expect(story.packageHash).toMatch(/^[a-f0-9]{64}$/);
      expect(story.article.hash).toMatch(/^[a-f0-9]{64}$/);
      expect(story.authority.producerCommit).toBe(
        '64834919b4f69e977475c203abeafef57791f015',
      );
    }
  });

  it('preserves exact claim, citation, and authority boundaries', () => {
    for (const story of canonicalReviewStories) {
      expect(story.claims.length).toBeGreaterThan(0);
      for (const claim of story.claims) {
        expect(claim.id).toMatch(/^claim-/);
        expect(claim.authority).toBe('OFFICIAL_VERIFIED');
        expect(claim.permission).toBe('PUBLIC_CLAIM_ALLOWED');
        expect(claim.citations.length).toBeGreaterThan(0);
      }
      expect(story.authority.repository).toBe(
        'fatcat2109/Headline-Raw-data-json',
      );
      expect(story.authority.byteLength).toBe(16646);
      for (const variant of story.variants) {
        expect(variant.text).toHaveLength(variant.characterCount);
        expect(variant.characterCount).toBeLessThanOrEqual(variant.characterLimit);
        expect(variant.dispatchAuthorized).toBe(false);
        expect(variant.citations.length).toBeGreaterThan(0);
        expect(variant.limitations).toEqual(story.limitations);
        expect(variant.authorizedClaimIds).toEqual(
          expect.arrayContaining(story.claims.map((claim) => claim.id)),
        );
      }
    }
  });

  it('rejects missing, duplicate, mismatched hash, and mismatched claim evidence', () => {
    const story = canonicalReviewStories[0];
    const input: CanonicalVariantJoinInput = {
      authorizedClaimIds: story.claims.map((claim) => claim.id),
      candidateId: story.candidateId,
      limitations: story.limitations,
      storyId: story.storyId,
      variantPayloadHashes: Object.fromEntries(
        story.variants.map((variant) => [variant.platform, variant.payloadHash]),
      ),
    };
    const records = canonicalVariantEvidenceRecords.filter(
      (record) => record.story_id === story.storyId,
    );

    expect(() => joinCanonicalVariantEvidence(input, records.slice(1))).toThrow(
      /count mismatch/i,
    );
    expect(() =>
      joinCanonicalVariantEvidence(input, [
        records[0],
        records[0],
        ...records.slice(2),
      ]),
    ).toThrow(/missing or duplicate/i);
    expect(() =>
      joinCanonicalVariantEvidence(input, [
        { ...records[0], payload_hash: '0'.repeat(64) },
        ...records.slice(1),
      ]),
    ).toThrow(/payload hash mismatch/i);
    expect(() =>
      joinCanonicalVariantEvidence(input, [
        { ...records[0], authorized_claim_ids: ['claim-not-authorized'] },
        ...records.slice(1),
      ]),
    ).toThrow(/claim allowlist mismatch/i);
  });

  it('derives article mode and market sensitivity from source capabilities', () => {
    const fomc = canonicalReviewStories.find((story) => story.authority.sourceFamily === 'federal_reserve_fomc')!;
    const apple = canonicalReviewStories.find((story) => story.authority.sourceFamily === 'sec_edgar')!;
    const usgs = canonicalReviewStories.find((story) => story.authority.sourceFamily === 'usgs_comcat')!;

    expect(fomc.readiness).toMatchObject({
      articleMode: 'analysis',
      marketSensitive: true,
      marketSnapshotRequired: true,
      storyType: 'policy_decision',
    });
    expect(apple.readiness).toMatchObject({
      articleMode: 'analysis',
      marketSensitive: true,
      marketSnapshotRequired: true,
      storyType: 'company_sector_event',
    });
    expect(usgs.readiness).toMatchObject({
      articleMode: 'analysis',
      marketSensitive: false,
      marketSnapshotRequired: false,
      storyType: 'physical_event',
    });
  });

  it('does not inherit market-snapshot blockers for the USGS physical event', () => {
    const usgs = canonicalReviewStories.find((story) => story.authority.sourceFamily === 'usgs_comcat')!;
    expect(usgs.readiness.unresolvedBlockers).not.toEqual(
      expect.arrayContaining([
        'market_sensitive_story_snapshot_stale_or_missing',
        'market_sensitive_story_ingest_stale_or_missing',
      ]),
    );
    expect(usgs.readiness.gates.find((gate) => gate.id === 'market_snapshot')).toMatchObject({
      blockers: [],
      status: 'NOT_APPLICABLE',
    });
    expect(usgs.editorialState).toBe('HOLD');
    expect(usgs.readiness.unresolvedBlockers).not.toContain('candidate_public_claim_permission_blocked');
    expect(usgs.blockers.freshness).toEqual([]);
  });

  it('exposes exactly five USGS text-only variants ready for an operator decision', () => {
    const ready = canonicalReviewStories.flatMap((story) =>
      story.variants
        .filter((variant) => variant.readiness.operatorReadyForDecision)
        .map((variant) => ({ story, variant })),
    );
    expect(canonicalReviewSummary.operatorReadyVariantCount).toBe(5);
    expect(ready).toHaveLength(5);
    for (const { story, variant } of ready) {
      expect(story.authority.sourceFamily).toBe('usgs_comcat');
      expect(variant.platform).not.toBe('substack_newsletter');
      expect(variant.readiness).toMatchObject({
        editorialReadiness: 'PASS',
        operatorDecisionState: 'PENDING_OPERATOR_DECISION',
        publicationAuthority: false,
        publicationReadiness: 'BLOCK',
        dispatchAuthority: false,
        dispatchReadiness: 'BLOCK',
      });
    }
  });

  it('separates long-form visual requirements from text-only platform policy', () => {
    for (const story of canonicalReviewStories) {
      const substack = story.variants.find((variant) => variant.platform === 'substack_newsletter')!;
      const community = story.variants.find((variant) => variant.platform === 'youtube_community')!;
      expect(substack.readiness.visualPolicy).toBe('long_form_article');
      expect(substack.readiness.unresolvedBlockers).toContain('fewer_than_three_useful_visuals');
      expect(community.readiness.visualPolicy).toBe('text_only_surface');
      expect(community.readiness.unresolvedBlockers).not.toContain('fewer_than_three_useful_visuals');
      expect(community.readiness.gates.find((gate) => gate.id === 'platform_visuals')).toMatchObject({
        blockers: [],
        status: 'NOT_APPLICABLE',
      });
    }
  });

  it('binds every platform readiness record to exact package, article, V3, and variant hashes', () => {
    for (const story of canonicalReviewStories) {
      for (const variant of story.variants) {
        expect(variant.readiness.hashes).toMatchObject({
          articleHash: story.article.hash,
          packageHash: story.packageHash,
          v3PacketHash: story.v3PacketLogicalHash,
          variantHash: variant.payloadHash,
        });
        expect(variant.readiness.hashes.visualPolicyHash).toMatch(/^[a-f0-9]{64}$/);
        expect(variant.readiness.hashes.readinessHash).toMatch(/^[a-f0-9]{64}$/);
        expect(variant.readiness.readinessOverlay).toBe('DERIVED_READINESS_OVERLAY');
        expect(variant.readiness.canonicalPackageEvidenceUnchanged).toBe(true);
        expect(variant.readiness.publicationAuthority).toBe(false);
        expect(variant.readiness.dispatchAuthority).toBe(false);
        expect(variant.readiness.publicationAuthorityBlocker).toBe('publication_authority_not_granted');
        expect(variant.readiness.dispatchReadiness).toBe('BLOCK');
        expect(variant.readiness.publicationReadiness).toBe('BLOCK');
      }
    }
  });

  it('replays capability-derived readiness deterministically', () => {
    const first = buildCanonicalReviewStories();
    const second = buildCanonicalReviewStories();
    expect(JSON.stringify(second)).toBe(JSON.stringify(first));
  });

  it('keys visual waivers to the exact platform, content surface, and variant mode', () => {
    const registry = sourceCapabilityRegistry as unknown as CapabilityRegistry;
    const textOnly = resolvePlatformVisualExpectation(
      'youtube_community', 'community_text_post', 'dry_run', registry,
    );
    const futureImageMode = resolvePlatformVisualExpectation(
      'youtube_community', 'community_text_post', 'image', registry,
    );
    expect(textOnly).toMatchObject({
      effective_visual_mode: 'text_only',
      minimum_visual_count: 0,
      status: 'PASS',
    });
    expect(futureImageMode).toMatchObject({
      blockers: ['unsupported_platform_visual_mode'],
      effective_visual_mode: 'fail_closed_visual_required',
      status: 'BLOCK',
    });
    expect(futureImageMode.minimum_visual_count).toBeGreaterThan(0);

    const malformedRegistry = structuredClone(registry);
    const malformedRule = malformedRegistry.platform_visual_expectations.youtube_community.rules[0];
    malformedRule.variant_mode = 'image';
    malformedRule.effective_visual_mode = 'image';
    const malformedImageMode = resolvePlatformVisualExpectation(
      'youtube_community', 'community_text_post', 'image', malformedRegistry,
    );
    expect(malformedImageMode).toMatchObject({
      blockers: ['malformed_platform_visual_policy'],
      effective_visual_mode: 'fail_closed_visual_required',
      minimum_visual_count: 1,
      status: 'BLOCK',
    });
  });

  it('binds readiness hashes to policy fields even when blockers remain identical', () => {
    expect(sha256Canonical('abc')).toBe('6cc43f858fbb763301637b5af970e2a46b46f461f27e5a0f41e009c59b827b25');
    const baseline = {
      applicableGates: ['editorial_review'],
      articleMode: 'analysis',
      blockers: ['same_blocker'],
      effectivePlatformVisualMode: 'text_only',
      marketSensitive: true,
      marketSnapshotRequired: false,
      requirements: { minimumVisualCount: 0 },
    };
    const hashes = [
      sha256Canonical(baseline),
      sha256Canonical({ ...baseline, articleMode: 'straight_news' }),
      sha256Canonical({ ...baseline, marketSensitive: false }),
      sha256Canonical({ ...baseline, marketSnapshotRequired: true }),
      sha256Canonical({ ...baseline, effectivePlatformVisualMode: 'mixed_media' }),
      sha256Canonical({ ...baseline, requirements: { minimumVisualCount: 1 } }),
    ];
    expect(new Set(hashes).size).toBe(hashes.length);
  });

  it('changes integrated readiness hashes for independent sensitivity and visual-mode policy mutations', () => {
    const registry = structuredClone(sourceCapabilityRegistry) as unknown as CapabilityRegistry;
    const baseline = buildCanonicalReviewStories(registry);
    const sensitivityMutation = structuredClone(registry);
    sensitivityMutation.story_types.physical_event.market_sensitive = true;
    const sensitivityStories = buildCanonicalReviewStories(sensitivityMutation);
    const visualModeMutation = structuredClone(registry);
    visualModeMutation.platform_visual_expectations.youtube_community.rules[0].effective_visual_mode = 'text_only_v2';
    const visualStories = buildCanonicalReviewStories(visualModeMutation);
    const baselineUsgs = baseline.find((story) => story.authority.sourceFamily === 'usgs_comcat')!;
    const sensitivityUsgs = sensitivityStories.find((story) => story.authority.sourceFamily === 'usgs_comcat')!;
    const visualUsgs = visualStories.find((story) => story.authority.sourceFamily === 'usgs_comcat')!;
    expect(sensitivityUsgs.readiness.marketSnapshotRequired).toBe(false);
    expect(sensitivityUsgs.readiness.marketSensitive).toBe(true);
    expect(sensitivityUsgs.readiness.readinessHash).not.toBe(baselineUsgs.readiness.readinessHash);
    expect(visualUsgs.variants.find((item) => item.platform === 'youtube_community')!.readiness.hashes.readinessHash)
      .not.toBe(baselineUsgs.variants.find((item) => item.platform === 'youtube_community')!.readiness.hashes.readinessHash);
  });
});

describe('canonical package review console', () => {
  it('routes through V5 navigation and forces dark-evidence mode', () => {
    const { container } = render(<App />);
    fireEvent.click(document.getElementById('nav-canonical_package_review')!);

    expect(
      screen.getByRole('heading', {
        level: 1,
        name: /three-story package review console/i,
      }),
    ).toBeInTheDocument();
    expect(container.querySelector('[data-theme]')).toHaveAttribute(
      'data-theme',
      'dark-evidence',
    );
    expect(document.getElementById('theme-toggle')).toBeDisabled();
    expect(screen.getAllByText('REQUEST_REVISION').length).toBeGreaterThan(0);
    expect(screen.getByText('READ_ONLY_EVIDENCE_REVIEW')).toBeInTheDocument();
  });

  it('switches all three packages and exposes package evidence in the inspector', () => {
    render(<App />);
    fireEvent.click(document.getElementById('nav-canonical_package_review')!);

    const target = canonicalReviewStories[1];
    fireEvent.click(
      document.getElementById(`canonical-story-tab-${target.storyId}`)!,
    );
    expect(screen.getAllByText(target.article.title).length).toBeGreaterThan(0);

    const rail = document.getElementById('inspector-rail')!;
    expect(within(rail).getByText(target.packageHash)).toBeInTheDocument();
    expect(within(rail).getByText('canonical operator package')).toBeInTheDocument();
  });

  it('exposes role and payload selections without decision or dispatch controls', () => {
    render(<App />);
    fireEvent.click(document.getElementById('nav-canonical_package_review')!);

    const story = canonicalReviewStories[0];
    const blockedRole = story.roles.find((role) => role.status !== 'PASS')!;
    fireEvent.click(
      document.getElementById(
        `canonical-role-${story.storyId}-${blockedRole.role}`,
      )!,
    );
    expect(
      within(document.getElementById('inspector-rail')!).getByText(
        'canonical editorial role outcome',
      ),
    ).toBeInTheDocument();

    const variant = story.variants[0];
    fireEvent.click(
      document.getElementById(
        `inspect-canonical-variant-${story.storyId}-${variant.platform}`,
      )!,
    );
    const rail = document.getElementById('inspector-rail')!;
    expect(within(rail).getByText(variant.payloadHash)).toBeInTheDocument();
    expect(within(rail).getByText('NOT_AUTHORIZED')).toBeInTheDocument();

    for (const button of screen.getAllByRole('button')) {
      expect(button.textContent ?? '').not.toMatch(
        /approve exact package|publish now|dispatch now|post now/i,
      );
    }
  });

  it('renders the complete copy and character limits for all 18 variants', () => {
    render(<App />);
    fireEvent.click(document.getElementById('nav-canonical_package_review')!);
    expect(screen.getByText('Canonical package/editorial state')).toBeInTheDocument();
    expect(screen.getByText('Derived capability applicability')).toBeInTheDocument();
    expect(screen.getByText('Publication / dispatch authority')).toBeInTheDocument();
    expect(screen.getByText('FALSE / FALSE')).toBeInTheDocument();

    for (const story of canonicalReviewStories) {
      fireEvent.click(
        document.getElementById(`canonical-story-tab-${story.storyId}`)!,
      );
      for (const variant of story.variants) {
        const copy = screen.getByTestId(
          `variant-copy-${story.storyId}-${variant.platform}`,
        );
        expect(copy.textContent).toBe(variant.text);
        expect(
          screen.getByText(`${variant.characterCount.toLocaleString()} characters`),
        ).toBeInTheDocument();
        expect(
          screen.getByText(`Limit ${variant.characterLimit.toLocaleString()}`),
        ).toBeInTheDocument();
      }
    }
  });

  it('renders per-platform blocker matrices for every story', () => {
    render(<App />);
    fireEvent.click(document.getElementById('nav-canonical_package_review')!);

    for (const story of canonicalReviewStories) {
      fireEvent.click(document.getElementById(`canonical-story-tab-${story.storyId}`)!);
      expect(screen.getByText('Capability-driven readiness matrix')).toBeInTheDocument();
      expect(screen.getByText(story.readiness.storyType)).toBeInTheDocument();
      for (const variant of story.variants) {
        const card = screen.getByTestId(`platform-readiness-${variant.platform}`);
        expect(within(card).getAllByText(variant.readiness.publicationAuthorityBlocker).length).toBeGreaterThan(0);
        expect(within(card).getByText(variant.readiness.hashes.variantHash)).toBeInTheDocument();
      }
    }
  });

  it.each([390, 1440])(
    'keeps story and exact-binding navigation operable at %ipx',
    (viewportWidth) => {
      Object.defineProperty(window, 'innerWidth', {
        configurable: true,
        value: viewportWidth,
      });
      window.dispatchEvent(new Event('resize'));
      render(<App />);
      fireEvent.click(document.getElementById('nav-canonical_package_review')!);

      const story = canonicalReviewStories[2];
      fireEvent.click(
        document.getElementById(`canonical-story-tab-${story.storyId}`)!,
      );
      const variant = story.variants[5];
      fireEvent.click(
        document.getElementById(
          `inspect-canonical-variant-${story.storyId}-${variant.platform}`,
        )!,
      );

      const renderedCopy = screen.getByTestId(
        `variant-copy-${story.storyId}-${variant.platform}`,
      );
      expect(renderedCopy.textContent).toBe(variant.text);
      expect(
        within(document.getElementById('inspector-rail')!).getByText(
          variant.payloadHash,
        ),
      ).toBeInTheDocument();
    },
  );
});
