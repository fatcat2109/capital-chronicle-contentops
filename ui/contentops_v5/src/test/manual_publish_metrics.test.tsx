// Capital Chronicle ContentOps V5 — Manual Publish + Metrics Capture tests.
//
// These tests enforce the 0174CI manual publish + metrics capture contract:
//   * the manual_publish_metrics route exists and is reachable
//   * a "Manual Publish" nav item is present
//   * manual publish candidates (approved/blocked/posted/metrics) render
//   * metrics records render and are manual-entry-only
//   * every record is can_post_live === false (true is unrepresentable)
//   * every record locks platform-API / credential / scheduler / autonomous
//   * the surface shows MANUAL_ONLY / NO_PLATFORM_API / NO_CREDENTIAL_READ /
//     NO_SCHEDULER / NO_AUTONOMOUS_POSTING / METRICS_MANUAL_ENTRY_ONLY /
//     HUMAN_REVIEW_REQUIRED policy states
//   * the "mark manual posted" control is disabled and never persists/posts
//   * selecting a record, a metrics snapshot, or a checklist item updates the
//     inspector rail
//   * no enabled control says publish now / post now / schedule / sync metrics
//     / fetch metrics
//   * prior routes remain present (no regression)

import { describe, expect, it } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { createElement } from 'react';
import App from '../App';
import { viewModel } from '../fixtures';

// ---------------------------------------------------------------------------
// Fixture contract — pure data invariants (no DOM)
// ---------------------------------------------------------------------------

describe('Manual publish + metrics contract', () => {
  const records = viewModel.manual_publish_records;

  it('exposes at least one record per lifecycle stage', () => {
    const stages = new Set(records.map((r) => r.stage));
    expect(stages.has('approved_for_manual')).toBe(true);
    expect(stages.has('blocked')).toBe(true);
    expect(stages.has('manually_posted')).toBe(true);
    expect(stages.has('metrics_entered')).toBe(true);
  });

  it('forces can_post_live === false on every record', () => {
    for (const r of records) {
      expect(r.can_post_live).toBe(false);
    }
  });

  it('locks platform-API / credential / scheduler / autonomous on every record', () => {
    for (const r of records) {
      expect(r.live_status).toBe('MANUAL_ONLY');
      expect(r.platform_api_status).toBe('NO_PLATFORM_API');
      expect(r.credential_status).toBe('NO_CREDENTIAL_READ');
      expect(r.scheduler_status).toBe('NO_SCHEDULER');
      expect(r.autonomous_status).toBe('NO_AUTONOMOUS_POSTING');
      expect(r.metrics_status).toBe('METRICS_MANUAL_ENTRY_ONLY');
      expect(r.review_status).toBe('HUMAN_REVIEW_REQUIRED');
    }
  });

  it('carries payload + approval packet refs and hashes on every record', () => {
    for (const r of records) {
      expect(r.payload_ref.length).toBeGreaterThan(0);
      expect(r.payload_hash.length).toBeGreaterThan(0);
      expect(r.approval_packet_ref.length).toBeGreaterThan(0);
      expect(r.approval_packet_hash.length).toBeGreaterThan(0);
      expect(r.checklist.length).toBeGreaterThan(0);
    }
  });

  it('keeps every metrics snapshot manual-entry only', () => {
    const allMetrics = records.flatMap((r) => r.metrics);
    expect(allMetrics.length).toBeGreaterThan(0);
    for (const m of allMetrics) {
      expect(m.source).toBe('MANUAL_ENTRY');
    }
  });
});

// ---------------------------------------------------------------------------
// Routing — new view reachable, prior views intact
// ---------------------------------------------------------------------------

describe('V5 navigation after 0174CI', () => {
  it('keeps prior routes and adds the manual publish route', () => {
    render(createElement(App));
    for (const id of [
      'nav-command_center',
      'nav-content_inventory',
      'nav-writer_studio',
      'nav-ai_writer_seo_lab',
      'nav-draft_inspector',
      'nav-platform_payload_preview',
      'nav-manual_publish_metrics',
      'nav-approval_queue',
      'nav-evidence_vault',
    ]) {
      expect(document.getElementById(id)).toBeInTheDocument();
    }
  });

  it('routes to Manual Publish and renders its heading', () => {
    render(createElement(App));
    fireEvent.click(document.getElementById('nav-manual_publish_metrics')!);
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
      /manual publish/i,
    );
  });
});

// ---------------------------------------------------------------------------
// Manual-only safety surface
// ---------------------------------------------------------------------------

describe('Manual Publish manual-only safety surface', () => {
  it('states manual-only and locks the policy states', () => {
    render(createElement(App));
    fireEvent.click(document.getElementById('nav-manual_publish_metrics')!);
    expect(screen.getAllByText(/manual only/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/can_post_live: false/i).length).toBeGreaterThan(
      0,
    );
    expect(screen.getAllByText(/MANUAL_ONLY/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/NO_PLATFORM_API/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/NO_CREDENTIAL_READ/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/NO_SCHEDULER/).length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/NO_AUTONOMOUS_POSTING/).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/METRICS_MANUAL_ENTRY_ONLY/).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/HUMAN_REVIEW_REQUIRED/).length,
    ).toBeGreaterThan(0);
  });

  it('renders a disabled mark-manual-posted action that never posts', () => {
    render(createElement(App));
    fireEvent.click(document.getElementById('nav-manual_publish_metrics')!);
    const disabled = screen
      .getAllByRole('button')
      .filter((b) => (b as HTMLButtonElement).disabled);
    expect(disabled.length).toBeGreaterThan(0);
    expect(
      screen.getByText(/mark manual posted \(disabled\)/i),
    ).toBeInTheDocument();
    // No enabled control offers live posting / scheduling / metrics sync.
    const enabled = screen
      .getAllByRole('button')
      .filter((b) => !(b as HTMLButtonElement).disabled);
    for (const b of enabled) {
      expect(b.textContent ?? '').not.toMatch(
        /publish now|post now|schedule|sync metrics|fetch metrics/i,
      );
    }
  });

  it('shows manual candidates and a blocked candidate via stage tabs', () => {
    render(createElement(App));
    fireEvent.click(document.getElementById('nav-manual_publish_metrics')!);
    // Approved-for-manual candidate visible by default.
    expect(
      document.getElementById('manual-record-MP-X-0042'),
    ).toBeInTheDocument();
    // Switch to the blocked tab — blocked candidate appears.
    fireEvent.click(document.getElementById('manual-tab-blocked')!);
    expect(
      document.getElementById('manual-record-MP-TT-0042'),
    ).toBeInTheDocument();
  });

  it('renders manually-entered metrics with no metrics API', () => {
    render(createElement(App));
    fireEvent.click(document.getElementById('nav-manual_publish_metrics')!);
    fireEvent.click(document.getElementById('manual-tab-metrics_entered')!);
    fireEvent.click(document.getElementById('manual-record-MP-TG-0042')!);
    const tg = viewModel.manual_publish_records.find(
      (r) => r.id === 'MP-TG-0042',
    )!;
    const m = tg.metrics[0];
    expect(document.getElementById(`metrics-snapshot-${m.id}`)).toBeInTheDocument();
    expect(screen.getAllByText(/manual entry only/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/MANUAL_ENTRY/).length).toBeGreaterThan(0);
  });
});

// ---------------------------------------------------------------------------
// Object-centric inspector
// ---------------------------------------------------------------------------

describe('Manual Publish inspector', () => {
  it('updates the inspector when a record is selected', () => {
    render(createElement(App));
    fireEvent.click(document.getElementById('nav-manual_publish_metrics')!);
    fireEvent.click(document.getElementById('manual-tab-manually_posted')!);
    fireEvent.click(document.getElementById('manual-record-MP-LI-0042')!);
    const rail = document.getElementById('inspector-rail')!;
    expect(within(rail).getByText('MP-LI-0042')).toBeInTheDocument();
    expect(
      within(rail).getAllByText(/can_post_live: false/i).length,
    ).toBeGreaterThan(0);
  });

  it('updates the inspector when a metrics snapshot is selected', () => {
    render(createElement(App));
    fireEvent.click(document.getElementById('nav-manual_publish_metrics')!);
    fireEvent.click(document.getElementById('manual-tab-metrics_entered')!);
    fireEvent.click(document.getElementById('manual-record-MP-TG-0042')!);
    const tg = viewModel.manual_publish_records.find(
      (r) => r.id === 'MP-TG-0042',
    )!;
    const m = tg.metrics[0];
    fireEvent.click(document.getElementById(`metrics-snapshot-${m.id}`)!);
    const rail = document.getElementById('inspector-rail')!;
    expect(within(rail).getByText(/metrics snapshot/i)).toBeInTheDocument();
    expect(within(rail).getByText(m.id)).toBeInTheDocument();
  });

  it('updates the inspector when a checklist item is selected', () => {
    render(createElement(App));
    fireEvent.click(document.getElementById('nav-manual_publish_metrics')!);
    const x = viewModel.manual_publish_records.find((r) => r.id === 'MP-X-0042')!;
    const c = x.checklist[0];
    fireEvent.click(document.getElementById(`manual-checklist-${c.id}`)!);
    const rail = document.getElementById('inspector-rail')!;
    expect(
      within(rail).getByText(/manual checklist item/i),
    ).toBeInTheDocument();
    expect(within(rail).getByText(c.id)).toBeInTheDocument();
  });
});
