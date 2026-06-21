import { describe, expect, it } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { createElement } from 'react';
import App from '../App';
import { operatorReviewQueuePacket as packet } from '../data/operatorReviewQueuePacket';

function openView() {
  render(createElement(App));
  fireEvent.click(document.getElementById('nav-operator_review_queue')!);
}

describe('Operator Review Queue UI', () => {
  it('adds navigation and renders safety-first heading', () => {
    openView();

    expect(document.getElementById('nav-operator_review_queue')).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(/operator review queue/i);
    expect(screen.getAllByText(/Manual Export Only/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/No platform API/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/No credentials loaded/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/No live dispatch/i).length).toBeGreaterThan(0);
  });

  it('renders queue details and review items', () => {
    openView();

    expect(screen.getAllByText(packet.packet_hash).length).toBeGreaterThan(0);
    expect(screen.getByText(/X manual post draft review/i)).toBeInTheDocument();
    expect(screen.getByText(/Telegram Channel manual message review/i)).toBeInTheDocument();
    expect(screen.getByText(/Substack manual newsletter\/export review/i)).toBeInTheDocument();
    expect(screen.getByText(/LinkedIn manual post review/i)).toBeInTheDocument();
  });

  it('renders timeline entries', () => {
    openView();

    expect(screen.getByText(/Created local review items for X, Telegram, Substack, LinkedIn./i)).toBeInTheDocument();
    expect(screen.getByText(/Operator checklist is pending manual verification./i)).toBeInTheDocument();
    expect(screen.getByText(/Live dispatch disabled — proof of local-only safety bounds verified./i)).toBeInTheDocument();
  });

  it('shows disabled actions and no enabled live affordance', () => {
    openView();

    for (const id of [
      'operator-queue-disabled-publish',
      'operator-queue-disabled-send',
      'operator-queue-disabled-schedule',
      'operator-queue-disabled-connect-account',
      'operator-queue-disabled-verify-credentials',
      'operator-queue-disabled-sync-platform',
      'operator-queue-disabled-live-dispatch',
    ]) {
      expect(document.getElementById(id)).toBeInTheDocument();
    }

    const enabledButtons = screen
      .getAllByRole('button')
      .filter((button) => !(button as HTMLButtonElement).disabled);
    for (const button of enabledButtons) {
      expect(button.textContent ?? '').not.toMatch(/publish now|post now|send now|schedule now|connect live|verify credentials now|sync platform now|dispatch live/i);
    }
  });

  it('updates inspector on clicking review items and timeline items', () => {
    openView();

    fireEvent.click(document.getElementById('item_x_manual_post_draft_review') || document.getElementById('operator-review-item-item_x_manual_post_draft_review')!);
    let rail = document.getElementById('inspector-rail')!;
    expect(within(rail).getByText(/operator review item/i)).toBeInTheDocument();
    expect(within(rail).getAllByText('item_x_manual_post_draft_review').length).toBeGreaterThan(0);

    fireEvent.click(document.getElementById('operator-trail-entry-trail_live_dispatch_disabled')!);
    rail = document.getElementById('inspector-rail')!;
    expect(within(rail).getByText(/local review trail entry/i)).toBeInTheDocument();
    expect(within(rail).getAllByText('trail_live_dispatch_disabled').length).toBeGreaterThan(0);
  });

  it('renders content lifecycle spine and updates inspector on click', () => {
    openView();

    expect(screen.getByText(/Content Lifecycle Spine/i)).toBeInTheDocument();
    expect(screen.getByText(/16 stages canonical lifecycle & operator read-model/i)).toBeInTheDocument();

    expect(screen.getByText(/Artifact or Brief Intake/i)).toBeInTheDocument();
    expect(screen.getByText(/Operator Approval Gate/i)).toBeInTheDocument();

    fireEvent.click(screen.getByText(/Artifact or Brief Intake/i));
    const rail = document.getElementById('inspector-rail')!;
    expect(within(rail).getByText(/lifecycle stage/i)).toBeInTheDocument();
    expect(within(rail).getAllByText('artifact_or_brief_intake').length).toBeGreaterThan(0);
  });
});
