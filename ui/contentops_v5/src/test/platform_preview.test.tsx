// Capital Chronicle ContentOps V5 — Platform Payload Preview tests.
//
// These tests enforce the 0174CF dry-run payload preview contract:
//   * the platform_payload_preview route exists and is reachable
//   * a "Platform Preview" nav item is present
//   * all eight platforms are present as fixtures + selectable tabs
//   * every preview is dispatchable === false (true is unrepresentable)
//   * every preview locks live/credential/provider states
//   * the surface states dry-run only / not dispatchable and shows a disabled
//     dispatch action with a future-gated / dry-run reason
//   * selecting a platform tab or a constraint updates the inspector rail
//   * the five flagship views + prior routes remain present (no regression)

import { describe, expect, it } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { createElement } from 'react';
import App from '../App';
import { viewModel } from '../fixtures';

// ---------------------------------------------------------------------------
// Fixture contract — pure data invariants (no DOM)
// ---------------------------------------------------------------------------

describe('Platform payload preview contract', () => {
  const previews = viewModel.platform_payload_previews;

  it('covers all eight target platforms', () => {
    const platforms = previews.map((p) => p.platform).sort();
    expect(platforms).toEqual(
      [
        'Facebook',
        'Instagram',
        'LinkedIn',
        'Substack',
        'Telegram',
        'Threads',
        'TikTok',
        'X',
      ].sort(),
    );
  });

  it('forces dispatchable === false on every preview', () => {
    for (const p of previews) {
      expect(p.dispatchable).toBe(false);
    }
  });

  it('locks live / credential / provider state on every preview', () => {
    for (const p of previews) {
      expect(p.live_status).toBe('LIVE_DISABLED');
      expect(p.credential_status).toBe('NO_CREDENTIAL_READ');
      expect(p.provider_status).toBe('NO_PROVIDER_CALL');
      expect(p.not_dispatchable_reason.length).toBeGreaterThan(0);
    }
  });

  it('exposes payload fields and constraints for every preview', () => {
    for (const p of previews) {
      expect(p.fields.length).toBeGreaterThan(0);
      expect(p.constraints.length).toBeGreaterThan(0);
    }
  });
});

// ---------------------------------------------------------------------------
// Routing — new view reachable, prior views intact
// ---------------------------------------------------------------------------

describe('V5 navigation after 0174CF', () => {
  it('keeps prior routes and adds the platform preview route', () => {
    render(createElement(App));
    for (const id of [
      'nav-command_center',
      'nav-content_inventory',
      'nav-writer_studio',
      'nav-ai_writer_seo_lab',
      'nav-draft_inspector',
      'nav-platform_payload_preview',
      'nav-approval_queue',
      'nav-evidence_vault',
    ]) {
      expect(document.getElementById(id)).toBeInTheDocument();
    }
  });

  it('routes to the Platform Payload Preview', () => {
    render(createElement(App));
    fireEvent.click(document.getElementById('nav-platform_payload_preview')!);
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
      /platform payload preview/i,
    );
  });
});

// ---------------------------------------------------------------------------
// Dry-run safety surface
// ---------------------------------------------------------------------------

describe('Platform Payload Preview dry-run safety surface', () => {
  it('states dry-run only / not dispatchable and locks live status', () => {
    render(createElement(App));
    fireEvent.click(document.getElementById('nav-platform_payload_preview')!);
    expect(screen.getAllByText(/dry-run/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/dispatchable: false/i).length).toBeGreaterThan(
      0,
    );
    expect(screen.getAllByText(/LIVE_DISABLED/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/NO_CREDENTIAL_READ/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/NO_PROVIDER_CALL/).length).toBeGreaterThan(0);
  });

  it('renders a disabled dispatch action with a dry-run reason', () => {
    render(createElement(App));
    fireEvent.click(document.getElementById('nav-platform_payload_preview')!);
    const disabled = screen
      .getAllByRole('button')
      .filter((b) => (b as HTMLButtonElement).disabled);
    expect(disabled.length).toBeGreaterThan(0);
    expect(screen.getByText(/dispatch payload \(disabled\)/i)).toBeInTheDocument();
    // No enabled control offers live posting / scheduling.
    const enabled = screen
      .getAllByRole('button')
      .filter((b) => !(b as HTMLButtonElement).disabled);
    for (const b of enabled) {
      expect(b.textContent ?? '').not.toMatch(/post now|publish now|schedule/i);
    }
  });

  it('exposes every platform as a selectable tab', () => {
    render(createElement(App));
    fireEvent.click(document.getElementById('nav-platform_payload_preview')!);
    for (const p of viewModel.platform_payload_previews) {
      expect(
        document.getElementById(`platform-tab-${p.platform_key}`),
      ).toBeInTheDocument();
    }
  });
});

// ---------------------------------------------------------------------------
// Object-centric inspector
// ---------------------------------------------------------------------------

describe('Platform Payload Preview inspector', () => {
  it('updates the inspector when a platform tab is selected', () => {
    render(createElement(App));
    fireEvent.click(document.getElementById('nav-platform_payload_preview')!);
    const telegram = viewModel.platform_payload_previews.find(
      (p) => p.platform_key === 'telegram',
    )!;
    fireEvent.click(document.getElementById('platform-tab-telegram')!);
    const rail = document.getElementById('inspector-rail')!;
    expect(within(rail).getByText(telegram.id)).toBeInTheDocument();
    expect(
      within(rail).getAllByText(/dispatchable: false/i).length,
    ).toBeGreaterThan(0);
  });

  it('updates the inspector when a constraint row is selected', () => {
    render(createElement(App));
    fireEvent.click(document.getElementById('nav-platform_payload_preview')!);
    const x = viewModel.platform_payload_previews.find(
      (p) => p.platform_key === 'x',
    )!;
    const c = x.constraints[0];
    fireEvent.click(document.getElementById(`constraint-${c.id}`)!);
    const rail = document.getElementById('inspector-rail')!;
    expect(within(rail).getByText(/payload constraint/i)).toBeInTheDocument();
    expect(within(rail).getByText(c.id)).toBeInTheDocument();
  });
});
