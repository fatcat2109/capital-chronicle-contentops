// Capital Chronicle ContentOps V5 — app shell smoke tests.
// Verifies the foundation renders, navigation switches views, and the
// Evidence Vault theme invariant (always dark-evidence) holds.

import { describe, expect, it } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import App from '../App';

function rootThemeEl(container: HTMLElement): HTMLElement {
  const el = container.querySelector('[data-theme]');
  if (!el) throw new Error('No [data-theme] root element found');
  return el as HTMLElement;
}

describe('ContentOps V5 app shell', () => {
  it('renders the brand and default Command Center view', () => {
    render(<App />);
    expect(screen.getByText('ContentOps')).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: 'Command Center', level: 1 }),
    ).toBeInTheDocument();
  });

  it('defaults to light theme and exposes all nav items', () => {
    const { container } = render(<App />);
    expect(rootThemeEl(container).getAttribute('data-theme')).toBe('light');
    for (const id of [
      'nav-command_center',
      'nav-content_inventory',
      'nav-writer_studio',
      'nav-approval_queue',
      'nav-evidence_vault',
    ]) {
      expect(document.getElementById(id)).toBeInTheDocument();
    }
  });

  it('switches views when a nav item is clicked', () => {
    render(<App />);
    fireEvent.click(document.getElementById('nav-writer_studio')!);
    expect(
      screen.getByRole('heading', { level: 1 }),
    ).toHaveTextContent(/writer studio/i);
  });

  it('forces dark-evidence theme in the Evidence Vault regardless of toggle', () => {
    const { container } = render(<App />);
    fireEvent.click(document.getElementById('nav-evidence_vault')!);
    expect(rootThemeEl(container).getAttribute('data-theme')).toBe(
      'dark-evidence',
    );
    // Theme toggle must be disabled while in the vault.
    const toggle = document.getElementById('theme-toggle') as HTMLButtonElement;
    expect(toggle).toBeDisabled();
  });

  it('shows a default selected object in the inspector on first render', () => {
    render(<App />);
    const rail = document.getElementById('inspector-rail')!;
    // Inspector must never be empty on first render: Command Center defaults
    // to the system verdict object, so the empty-state copy is absent.
    expect(within(rail).queryByText(/select an object/i)).toBeNull();
    expect(within(rail).getByText(/system verdict/i)).toBeInTheDocument();
  });
});
