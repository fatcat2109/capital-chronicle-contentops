import { describe, expect, it } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { createElement } from 'react';
import App from '../App';
import { dualLaneCoreV0ShadowPacket as p } from '../data/dualLaneCoreV0ShadowPacket';

function openView() {
  render(createElement(App));
  fireEvent.click(document.getElementById('nav-dual_lane_core_v0_shadow')!);
}

describe('Dual-Lane CORE V0 Shadow UI', () => {
  it('shows SHADOW_ONLY mode and locked live actions', () => {
    openView();

    expect(screen.getAllByText(/Dual-Lane Shadow Newsroom/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText('SHADOW_ONLY').length).toBeGreaterThan(0);
    expect(screen.getByText(/LIVE ACTIONS LOCKED/)).toBeInTheDocument();
  });

  it('shows both lane results in one surface', () => {
    openView();

    expect(screen.getAllByText('Newsroom lane').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Capital Chronicle lane').length).toBeGreaterThan(0);
    expect(screen.getAllByText(String(p.newsroom_lane.selected_candidate_id)).length).toBeGreaterThan(0);
    expect(screen.getAllByText(String(p.capital_chronicle_lane.analytical_fidelity_result)).length).toBeGreaterThan(0);
  });

  it('shows the truthful canonical review outcome, not a hardcoded PASS', () => {
    openView();

    expect(screen.getAllByText(String(p.newsroom_review.outcome)).length).toBeGreaterThan(0);
    expect(screen.getAllByText(String(p.capital_chronicle_review.outcome)).length).toBeGreaterThan(0);
    expect(screen.getAllByText(new RegExp(p.review_engine)).length).toBeGreaterThan(0);
  });

  it('shows a blocked visual state when the visual policy blocks', () => {
    openView();

    if (p.newsroom_review.visual_decision_status !== 'BLOCK') return;
    expect(p.newsroom_review.result).toBe('BLOCK');
    expect(p.newsroom_review.blocked_roles).toContain('visual_editor');
    expect(screen.getAllByText(/BLOCK visual_editor/).length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/BLOCK adversarial_final_reviewer/).length,
    ).toBeGreaterThan(0);
  });

  it('shows every canonical role outcome for both lanes', () => {
    openView();

    expect(p.newsroom_review.role_count).toBe(8);
    expect(p.capital_chronicle_review.role_count).toBe(8);
    for (const row of p.newsroom_review.roles) {
      expect(
        screen.getAllByText(new RegExp(`${row.result === 'PASS' ? 'PASS' : 'BLOCK'}\\s+${row.role}`)).length,
      ).toBeGreaterThan(0);
    }
  });

  it('shows the canonical package fabric and per-platform shapes', () => {
    openView();

    expect(screen.getAllByText(new RegExp(p.package_fabric)).length).toBeGreaterThan(0);
    const shapes = p.platform_payload_shapes.map((row) => row.payload_shape);
    expect(new Set(shapes).size).toBe(shapes.length);
    for (const row of p.platform_payload_shapes) {
      expect(
        screen.getByText(new RegExp(`${row.platform_id} — ${row.payload_shape}`)),
      ).toBeInTheDocument();
    }
  });

  it('shows the selection reason and every held candidate blocker', () => {
    openView();

    const reason = 'why_selected' in p.newsroom_selection_reason
      ? String(p.newsroom_selection_reason.why_selected)
      : String((p.newsroom_selection_reason as { why_abstained?: string }).why_abstained);
    expect(screen.getByText(reason)).toBeInTheDocument();
    expect(p.newsroom_held_candidates.length).toBeGreaterThan(0);
    for (const row of p.newsroom_held_candidates) {
      expect(screen.getByText(new RegExp(`HELD ${row.candidate_id}`))).toBeInTheDocument();
    }
  });

  it('shows publication and dispatch authority both false', () => {
    openView();

    expect(p.publication_authority).toBe(false);
    expect(p.dispatch_authority).toBe(false);
    expect(p.public_write_authority).toBe(false);
    expect(screen.getByText('Publication')).toBeInTheDocument();
    expect(screen.getByText('Dispatch')).toBeInTheDocument();
    expect(screen.getByText('Public write')).toBeInTheDocument();
    expect(screen.getAllByText('no authority').length).toBe(3);
  });

  it('shows durable terminal state and replay verification', () => {
    openView();

    expect(screen.getByText('Durable shadow state')).toBeInTheDocument();
    for (const id of p.durable_work_item_ids) {
      expect(screen.getByText(new RegExp(id))).toBeInTheDocument();
    }
    expect(screen.getByText('Replay')).toBeInTheDocument();
    expect(screen.getAllByText('valid').length).toBeGreaterThan(0);
  });

  it('reports unsupported Tier-1 destinations rather than hiding them', () => {
    openView();

    expect(screen.getByText('Unsupported')).toBeInTheDocument();
    expect(
      screen.getByText(new RegExp(p.platform_capability.unsupported_destinations.join(', '))),
    ).toBeInTheDocument();
    expect(screen.getByText('reported, not omitted')).toBeInTheDocument();
  });

  it('never renders a live-authority-granting claim', () => {
    openView();

    expect(screen.queryByText(/PUBLISH NOW/i)).toBeNull();
    expect(screen.queryByText(/DISPATCH READY/i)).toBeNull();
    expect(p.network_call_performed).toBe(false);
    expect(p.credential_read_performed).toBe(false);
    expect(p.browser_or_cdp_action_performed).toBe(false);
  });
});
