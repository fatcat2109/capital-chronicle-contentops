// Capital Chronicle ContentOps V5 — V6 approval/evidence integration tests.
// Fixture-only. No network, no storage, no credentials, no live controls.

import { describe, expect, it } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import App from '../App';

describe('V6 operator approval/evidence integration in canonical V5 dashboard', () => {
  it('renders V6 fixture-only approval queue inside Approval & Dispatch', () => {
    render(<App />);
    fireEvent.click(document.getElementById('nav-approval_queue')!);

    expect(
      screen.getByText('V6 operator approval queue · fixture-only'),
    ).toBeInTheDocument();
    expect(screen.getAllByText('sample_fixture_only').length).toBeGreaterThan(0);
    expect(screen.getByText('preview_discord_1cd58fd896f19c77')).toBeInTheDocument();
    expect(screen.getAllByText('live blocked').length).toBeGreaterThan(0);

    const disabledButtons = Array.from(document.querySelectorAll('button')).filter(
      (button) => (button as HTMLButtonElement).disabled,
    );
    expect(disabledButtons.length).toBeGreaterThan(0);
  });

  it('renders V6 fixture-only evidence in Evidence Vault with blocked live pilot state', () => {
    render(<App />);
    fireEvent.click(document.getElementById('nav-evidence_vault')!);

    expect(
      screen.getByText('V6 operator evidence vault · fixture-only'),
    ).toBeInTheDocument();
    expect(screen.getAllByText('sample_fixture_only').length).toBeGreaterThan(0);
    expect(screen.getByText('Live pilot blocked · no runtime proof')).toBeInTheDocument();
    expect(screen.getByText('operator_approval_declaration_missing')).toBeInTheDocument();
    expect(screen.getByText('evidence_article_d4a5afd3ecf03b1b')).toBeInTheDocument();
  });
});
