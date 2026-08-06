import { describe, expect, it } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { createElement } from 'react';
import App from '../App';
import { coreV0CohortSnapshot as s } from '../data/coreV0CohortSnapshot';

function openView() {
  render(createElement(App));
  fireEvent.click(document.getElementById('nav-core_v0_cohort_closure')!);
}

describe('CORE V0 Cohort Closure UI', () => {
  it('shows SHADOW_ONLY mode and locked live actions', () => {
    openView();

    expect(screen.getAllByText(/Diversified Cohort Shadow Run/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText('SHADOW_ONLY').length).toBeGreaterThan(0);
    expect(screen.getByText(/LIVE ACTIONS LOCKED/)).toBeInTheDocument();
  });

  it('renders a snapshot generated from a real run', () => {
    openView();

    expect(s.generated_from_real_run).toBe(true);
    expect(s.schema_version).toBe('contentops.core_v0_cohort_shadow_run.v1');
  });

  it('shows every required domain family with a case count', () => {
    openView();

    expect(s.corpus.coverage.all_families_represented).toBe(true);
    for (const [family, ids] of Object.entries(s.corpus.coverage.cases_by_family)) {
      expect(
        screen.getByText(new RegExp(`${family} · ${(ids as readonly string[]).length}`)),
      ).toBeInTheDocument();
    }
  });

  it('gives every cohort case an explicit outcome and terminal state', () => {
    openView();

    expect(s.cases.length).toBe(s.corpus.case_count);
    for (const c of s.cases) {
      expect(screen.getAllByText(c.case_id).length).toBeGreaterThan(0);
      expect(screen.getAllByText(c.outcome).length).toBeGreaterThan(0);
      expect(c.terminal_state).toBeTruthy();
    }
  });

  it('shows a passing package for both input lanes', () => {
    openView();

    const passing = s.cases.filter((c) => c.outcome === 'PACKAGE_REVIEW_PASSED');
    expect(new Set(passing.map((c) => c.lane))).toEqual(
      new Set(['newsroom', 'capital_chronicle']),
    );
    for (const c of passing) {
      expect(
        screen.getByText(new RegExp(`PASS ${c.lane} — ${c.case_id}`)),
      ).toBeInTheDocument();
    }
  });

  it('shows truthful held, blocked, and no-publication outcomes', () => {
    openView();

    const counts = s.outcome_counts;
    expect(counts.no_publication).toBeGreaterThan(0);
    expect(counts.duplicate_or_low_delta).toBeGreaterThan(0);
    expect(counts.visual_rights_blocked).toBeGreaterThan(0);
    expect(screen.getAllByText('No publication').length).toBeGreaterThan(0);
    expect(screen.getByText('Rights blocked')).toBeInTheDocument();
  });

  it('never marks a blocked case as review-ready', () => {
    openView();

    for (const c of s.cases) {
      if (c.outcome !== 'PACKAGE_REVIEW_PASSED') {
        expect(c.terminal_state).not.toBe('REVIEW_READY');
      }
    }
  });

  it('shows portfolio concentration per dimension', () => {
    openView();

    for (const dimension of Object.keys(s.portfolio_daily.dimensions)) {
      expect(screen.getByText(dimension)).toBeInTheDocument();
    }
    expect(screen.getByText(/Threshold/)).toBeInTheDocument();
  });

  it('shows a chart that passed methodology QA', () => {
    openView();

    const charted = s.cases.filter((c) => c.chart_qa_status === 'PASS');
    expect(charted.length).toBeGreaterThan(0);
    for (const c of charted) {
      expect(
        screen.getAllByText(new RegExp(String(c.chart_title))).length,
      ).toBeGreaterThan(0);
    }
  });

  it('lists all nine Tier-1 destinations', () => {
    openView();

    expect(s.tier1_destination_count).toBe(9);
    expect(s.tier1_destinations.length).toBe(9);
    for (const platform of s.tier1_destinations) {
      expect(screen.getByText(platform)).toBeInTheDocument();
    }
    expect(screen.getAllByText(new RegExp(s.package_fabric)).length).toBeGreaterThan(0);
  });

  it('shows the canonical review engine and durable replay', () => {
    openView();

    expect(s.review_engine).toBe('editorial_review_orchestrator_v2.run_editorial_review');
    expect(screen.getAllByText(new RegExp(s.review_engine)).length).toBeGreaterThan(0);
    expect(s.replay_verification.all_replays_valid).toBe(true);
    expect(screen.getAllByText('valid').length).toBeGreaterThan(0);
    for (const id of Object.keys(s.durable.terminal_states)) {
      expect(screen.getByText(new RegExp(id))).toBeInTheDocument();
    }
  });

  it('never renders a live-authority-granting claim', () => {
    openView();

    expect(screen.queryByText(/PUBLISH NOW/i)).toBeNull();
    expect(screen.queryByText(/DISPATCH READY/i)).toBeNull();
    expect(s.publication_authority).toBe(false);
    expect(s.dispatch_authority).toBe(false);
    expect(s.public_write_authority).toBe(false);
    expect(s.network_call_performed).toBe(false);
    expect(s.credential_read_performed).toBe(false);
    expect(s.browser_or_cdp_action_performed).toBe(false);
    expect(s.scheduler_or_outbox_action_performed).toBe(false);
    expect(s.public_write_performed).toBe(false);
    expect(s.shadow_readback.public_objects_created).toBe(0);
  });

  it('shows daily and rolling windows as genuinely different reports', () => {
    openView();

    expect(s.portfolio_daily.report_id).not.toBe(s.portfolio_rolling.report_id);
    expect(s.portfolio_daily.report_logical_hash).not.toBe(
      s.portfolio_rolling.report_logical_hash,
    );
    expect(screen.getByText(s.portfolio_daily.report_id)).toBeInTheDocument();
    expect(screen.getByText(s.portfolio_rolling.report_id)).toBeInTheDocument();
    expect(
      screen.getByText(new RegExp(String(s.portfolio_rolling.history_window_start_utc))),
    ).toBeInTheDocument();
  });

  it('shows the accepted publication history the rolling window is built from', () => {
    openView();

    expect(s.accepted_publication_history.length).toBeGreaterThan(0);
    for (const row of s.accepted_publication_history) {
      expect(screen.getByText(new RegExp(row.case_id))).toBeInTheDocument();
    }
  });

  it('shows base versus adjusted rank and a concentration-caused reorder', () => {
    openView();

    const reordered = s.portfolio_decision.decisions.filter(
      (d) => d.rank_changed_by_concentration,
    );
    expect(reordered.length).toBeGreaterThan(0);
    expect(screen.getAllByText(/REORDERED/).length).toBeGreaterThan(0);
    for (const row of reordered) {
      expect(row.base_rank).not.toBe(row.adjusted_rank);
      expect(row.adjusted_score).toBeLessThanOrEqual(row.base_score);
    }
  });

  it('shows DEFER_FOR_PORTFOLIO_BALANCE with no package produced', () => {
    openView();

    const deferred = s.cases.filter((c) => c.outcome === 'DEFER_FOR_PORTFOLIO_BALANCE');
    expect(deferred.length).toBeGreaterThan(0);
    expect(screen.getAllByText('DEFER_FOR_PORTFOLIO_BALANCE').length).toBeGreaterThan(0);
    expect(screen.getByText('Deferred for balance')).toBeInTheDocument();
    for (const c of deferred) {
      expect(c.terminal_state).toBe('DEFERRED_FOR_PORTFOLIO_BALANCE');
      expect(c.deferred_by_portfolio_concentration).toBe(true);
      expect(c.hard_gate_failure).toBe(false);
    }
  });

  it('shows platform visual adaptation status, dimensions and hashes', () => {
    openView();

    const adapted = s.cases.filter((c) => c.visual_adaptation_bindings.length > 0);
    expect(adapted.length).toBeGreaterThan(0);
    for (const c of adapted) {
      for (const b of c.visual_adaptation_bindings) {
        expect(
          screen.getAllByText(
            new RegExp(`${b.platform_id}.*${b.target_width}×${b.target_height}`),
          ).length,
        ).toBeGreaterThan(0);
        expect(b.crop_applied).toBe(false);
        expect(b.derivative_sha256).toBeTruthy();
      }
    }
  });
});
