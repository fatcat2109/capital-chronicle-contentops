import { describe, expect, it } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { createElement } from 'react';
import App from '../App';

function openView() {
  render(createElement(App));
  fireEvent.click(document.getElementById('nav-v6_command_center')!);
}

describe('V6 Command Center', () => {
  it('renders Jim source-to-audit operator flow', () => {
    openView();
    expect(screen.getByText('Jim Source-to-Audit Command Center')).toBeInTheDocument();
    expect(screen.getByLabelText('Jim Source-to-Audit Operator Flow')).toBeInTheDocument();
    for (const label of ['Source intake', 'Canonical draft', 'Hash approval', 'Platform variants', 'Media selection', 'Manual dispatch / audit']) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
  });

  it('renders the full north-star platform universe', () => {
    openView();
    expect(screen.getByText('Full Platform Universe')).toBeInTheDocument();
    for (const platform of ['Substack', 'LinkedIn', 'X', 'Discord', 'Telegram', 'Facebook Page', 'Threads', 'Instagram', 'TikTok', 'Generic Manual']) {
      expect(screen.getAllByText(platform).length).toBeGreaterThan(0);
    }
    expect(screen.getByText('Meta-family page distribution lane')).toBeInTheDocument();
    expect(screen.getByText('High-friction short-video lane')).toBeInTheDocument();
  });

  it('renders source-aware media candidate lanes', () => {
    openView();
    expect(screen.getByText('News Image Candidate Lane')).toBeInTheDocument();
    expect(screen.getByText('Official CPI release visual context')).toBeInTheDocument();
    expect(screen.getByText('metadata-only://official-release-thumbnail')).toBeInTheDocument();
    expect(screen.getByText(/google_scrape=false/i)).toBeInTheDocument();

    expect(screen.getByText('Internal Report Chart/Card Lane')).toBeInTheDocument();
    expect(screen.getByText('Internal alpha dispersion card')).toBeInTheDocument();
    expect(screen.getByText('Forecast-readiness checklist card')).toBeInTheDocument();
    expect(screen.getByText(/built_in_chart_preferred=true/i)).toBeInTheDocument();
  });

  it('renders hash-bound operator decision intake without unlocking dispatch', () => {
    openView();
    expect(screen.getByText('Operator Decision Intake')).toBeInTheDocument();
    for (const decision of ['approve', 'hold', 'reject']) {
      expect(screen.getByText(decision)).toBeInTheDocument();
    }
    expect(screen.getByText('Canonical Substack payload approved for manual export evidence only.')).toBeInTheDocument();
    expect(screen.getByText('X wording needs another operator pass before any manual copy.')).toBeInTheDocument();
    expect(screen.getByText('Instagram lane is rejected until rights/account constraints are solved.')).toBeInTheDocument();
    expect(screen.getAllByText(/local-[0-9a-f]{8}-[0-9a-f]{8}/i).length).toBeGreaterThan(2);
    expect(screen.getAllByText(/decision_packet_id=decision_/i).length).toBe(3);
    expect(screen.getAllByText(/dispatch_permission_granted=false/i).length).toBe(3);
    expect(screen.getAllByText(/live_write_allowed=false/i).length).toBeGreaterThan(2);
  });

  it('keeps unsafe actions disabled and avoids inputs/links', () => {
    openView();
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
    const locked = screen.getByRole('button', { name: /Publish \/ Dispatch \/ Scrape \/ Download \/ Verify public URL/i });
    expect(locked).toBeDisabled();
    for (const button of screen.getAllByRole('button').filter((b) => !(b as HTMLButtonElement).disabled)) {
      expect(button.textContent ?? '').not.toMatch(/publish now|post now|send now|schedule now|dispatch live|verify credentials|verify public url|scrape|download/i);
    }
  });
});
