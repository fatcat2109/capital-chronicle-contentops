// Capital Chronicle ContentOps V5 — AI Writer / SEO Lab + Draft Inspector tests.
//
// These tests enforce the 0174CE feature contract:
//   * AI Writer / SEO Lab route exists and is reachable
//   * Draft Inspector route exists and is reachable
//   * the five flagship views remain present (no regression)
//   * every AI Writer output has publish_ready === false (unrepresentable true)
//   * the AI surface states UI-only / review-only and "no provider call"
//   * the Draft Inspector renders no-signal, citation, limitation, claim-risk,
//     and artifact-eligibility check families
//   * selecting AI/SEO/inspection objects updates the inspector rail

import { describe, expect, it } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { createElement } from 'react';
import App from '../App';
import { viewModel } from '../fixtures';

// ---------------------------------------------------------------------------
// Fixture contract — pure data invariants (no DOM)
// ---------------------------------------------------------------------------

describe('AI Writer output contract', () => {
  const allOutputs = [
    ...viewModel.editorial_draft.ai_outputs,
    ...viewModel.ai_writer_lab.outputs,
  ];

  it('has at least one AI variant', () => {
    expect(allOutputs.length).toBeGreaterThan(0);
  });

  it('forces publish_ready === false on every AI variant', () => {
    for (const v of allOutputs) {
      expect(v.publish_ready).toBe(false);
    }
  });

  it('requires human review and a not-public-postable reason on every variant', () => {
    for (const v of allOutputs) {
      expect(v.human_review_required).toBe(true);
      expect(v.not_public_postable_reason.length).toBeGreaterThan(0);
    }
  });

  it('preserves limitations and source references on every variant', () => {
    for (const v of allOutputs) {
      expect(v.limitations_preserved).toBe(true);
      expect(v.source_references_preserved).toBe(true);
    }
  });
});

describe('Draft inspection contract', () => {
  const di = viewModel.draft_inspections[0];

  it('exposes every check family with at least one row', () => {
    expect(di.citation_checks.length).toBeGreaterThan(0);
    expect(di.limitation_checks.length).toBeGreaterThan(0);
    expect(di.claim_risk_items.length).toBeGreaterThan(0);
    expect(di.no_signal_checks.length).toBeGreaterThan(0);
    expect(di.artifact_eligibility_checks.length).toBeGreaterThan(0);
    expect(di.source_lineage.length).toBeGreaterThan(0);
  });

  it('is never publish-ready and always requires human review', () => {
    expect(di.publish_ready).toBe(false);
    expect(di.human_review_required).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// Routing — new views are reachable, flagship views intact
// ---------------------------------------------------------------------------

describe('V5 navigation after 0174CE', () => {
  it('keeps the five flagship views and adds the two new routes', () => {
    render(createElement(App));
    for (const id of [
      'nav-command_center',
      'nav-content_inventory',
      'nav-writer_studio',
      'nav-approval_queue',
      'nav-evidence_vault',
      'nav-ai_writer_seo_lab',
      'nav-draft_inspector',
    ]) {
      expect(document.getElementById(id)).toBeInTheDocument();
    }
  });

  it('routes to the AI Writer / SEO Lab', () => {
    render(createElement(App));
    fireEvent.click(document.getElementById('nav-ai_writer_seo_lab')!);
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
      /ai writer \/ seo lab/i,
    );
  });

  it('routes to the Draft Inspector', () => {
    render(createElement(App));
    fireEvent.click(document.getElementById('nav-draft_inspector')!);
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
      /draft inspector/i,
    );
  });
});

// ---------------------------------------------------------------------------
// AI Writer / SEO Lab — UI-only / review-only safety surface
// ---------------------------------------------------------------------------

describe('AI Writer / SEO Lab safety surface', () => {
  it('states UI-only / review-only and no provider call', () => {
    render(createElement(App));
    fireEvent.click(document.getElementById('nav-ai_writer_seo_lab')!);
    expect(screen.getAllByText(/ui-only/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/review only/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/no provider call/i)).toBeInTheDocument();
    expect(screen.getByText(/never source authority/i)).toBeInTheDocument();
    expect(screen.getAllByText(/publish_ready: false/i).length).toBeGreaterThan(
      0,
    );
  });

  it('updates the inspector when an AI variant is selected', () => {
    render(createElement(App));
    fireEvent.click(document.getElementById('nav-ai_writer_seo_lab')!);
    const variant = viewModel.ai_writer_lab.outputs[1];
    fireEvent.click(document.getElementById(`lab-variant-${variant.variant_id}`)!);
    const rail = document.getElementById('inspector-rail')!;
    expect(within(rail).getByText(variant.variant_id)).toBeInTheDocument();
    expect(within(rail).getAllByText(/publish_ready: false/i).length).toBeGreaterThan(0);
  });

  it('updates the inspector when an SEO keyword group is selected', () => {
    render(createElement(App));
    fireEvent.click(document.getElementById('nav-ai_writer_seo_lab')!);
    const group = viewModel.ai_writer_lab.keyword_groups[0];
    fireEvent.click(document.getElementById(`seo-group-${group.id}`)!);
    const rail = document.getElementById('inspector-rail')!;
    expect(within(rail).getByText(/seo keyword group/i)).toBeInTheDocument();
    expect(within(rail).getByText(group.id)).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Draft Inspector — check families + object-centric inspector
// ---------------------------------------------------------------------------

describe('Draft Inspector surface', () => {
  it('renders all inspection check families', () => {
    render(createElement(App));
    fireEvent.click(document.getElementById('nav-draft_inspector')!);
    expect(screen.getByText(/source lineage/i)).toBeInTheDocument();
    expect(screen.getByText(/citation completeness/i)).toBeInTheDocument();
    expect(screen.getByText(/claim-risk classification/i)).toBeInTheDocument();
    expect(screen.getByText(/limitation notes/i)).toBeInTheDocument();
    expect(screen.getByText(/forbidden-language audit/i)).toBeInTheDocument();
    expect(
      screen.getAllByText(/artifact-backed eligibility/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText(/publish_ready: false/i).length).toBeGreaterThan(
      0,
    );
  });

  it('updates the inspector when a citation check is selected', () => {
    render(createElement(App));
    fireEvent.click(document.getElementById('nav-draft_inspector')!);
    const c = viewModel.draft_inspections[0].citation_checks[0];
    fireEvent.click(document.getElementById(`citation-${c.id}`)!);
    const rail = document.getElementById('inspector-rail')!;
    expect(within(rail).getByText(/citation check/i)).toBeInTheDocument();
    expect(within(rail).getByText(c.id)).toBeInTheDocument();
  });

  it('updates the inspector when a claim-risk item is selected', () => {
    render(createElement(App));
    fireEvent.click(document.getElementById('nav-draft_inspector')!);
    const c = viewModel.draft_inspections[0].claim_risk_items[0];
    fireEvent.click(document.getElementById(`claim-risk-${c.id}`)!);
    const rail = document.getElementById('inspector-rail')!;
    expect(within(rail).getByText(/claim risk item/i)).toBeInTheDocument();
    expect(within(rail).getAllByText(c.id).length).toBeGreaterThan(0);
  });
});
