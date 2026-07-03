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

    expect(screen.getAllByText('Artifact-backed macro brief').length).toBeGreaterThan(0);
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

  it('renders intent to variant preview bundle as placeholders only', () => {
    openView();

    expect(screen.getByText('Content Intent + Platform Variant Preview Bundle')).toBeInTheDocument();
    expect(screen.getAllByText('JIM_REVIEW_REQUIRED_PREVIEW_ONLY').length).toBeGreaterThan(0);
    expect(screen.getByText('Platform previews')).toBeInTheDocument();
    expect(screen.getAllByText('manual_export_ready=false · dispatch_ready=false').length).toBeGreaterThan(0);
    expect(screen.getAllByText('PREVIEW_PLACEHOLDER_READY_FOR_JIM_REVIEW').length).toBeGreaterThan(0);
    expect(screen.getAllByText('BLOCKED_WAITING_FOR_INPUTS').length).toBeGreaterThan(0);
  });

  it('renders variant preview safety flags without live readiness', () => {
    openView();

    expect(screen.getByText('Variant Preview Safety Flags')).toBeInTheDocument();
    expect(screen.getByText('final_public_copy_created')).toBeInTheDocument();
    expect(screen.getByText('llm_provider_called')).toBeInTheDocument();
    expect(screen.getByText('platform_api_called')).toBeInTheDocument();
    expect(screen.getAllByText('publish_ready').length).toBeGreaterThan(0);
    expect(screen.getAllByText('dispatch_ready').length).toBeGreaterThan(0);
  });

});
