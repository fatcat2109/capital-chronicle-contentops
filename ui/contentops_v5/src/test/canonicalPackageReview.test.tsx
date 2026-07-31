// Canonical three-story package review console — evidence and interaction tests.

import { fireEvent, render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import App from '../App';
import {
  canonicalReviewStories,
  canonicalReviewSummary,
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
    }
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
        `canonical-variant-${story.storyId}-${variant.platform}`,
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
});
