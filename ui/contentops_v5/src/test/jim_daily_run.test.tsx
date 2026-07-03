import { describe, expect, it } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { createElement } from 'react';
import App from '../App';

function openView() {
  render(createElement(App));
  fireEvent.click(document.getElementById('nav-jim_daily_run')!);
}

describe('Jim Daily Content Run UI', () => {
  it('renders review-only daily run surface for Jim', () => {
    openView();

    expect(screen.getAllByText(/Jim Daily Content Run/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText('JIM_FINAL_REVIEW_REQUIRED').length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Jim final review required/i).length).toBeGreaterThan(0);
    expect(screen.getByText('No provider API')).toBeInTheDocument();
    expect(screen.getByText('No platform dispatch')).toBeInTheDocument();
  });

  it('renders Lane C as blocked without artifact evidence', () => {
    openView();

    expect(screen.getByText('Artifact-backed macro brief')).toBeInTheDocument();
    expect(screen.getByText('Lane C blocked without approved artifact evidence')).toBeInTheDocument();
    expect(screen.getByText('Attach approved artifact evidence before drafting.')).toBeInTheDocument();
  });

  it('does not add inputs links or enabled publish controls', () => {
    openView();

    expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
    for (const button of screen.getAllByRole('button').filter((b) => !(b as HTMLButtonElement).disabled)) {
      expect(button.textContent ?? '').not.toMatch(/publish now|post now|send now|schedule now|dispatch live|verify public url/i);
    }
  });
});
