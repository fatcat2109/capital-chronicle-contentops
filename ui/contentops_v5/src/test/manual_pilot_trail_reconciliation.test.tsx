import { describe, expect, it } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { createElement } from 'react';
import App from '../App';
import { manualPilotTrailReconciliationPacket as packet } from '../data/manualPilotTrailReconciliationPacket';

function openView() {
  render(createElement(App));
  fireEvent.click(document.getElementById('nav-manual_pilot_trail_reconciliation')!);
}

describe('Manual Pilot Trail Reconciliation UI', () => {
  it('adds navigation and renders safety-first heading', () => {
    openView();

    expect(document.getElementById('nav-manual_pilot_trail_reconciliation')).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(/manual pilot trail reconciliation/i);
    expect(screen.getAllByText(/local only/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/manual only/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/no platform api/i).length).toBeGreaterThan(0);
  });

  it('renders reconciliation details and lifecycle steps', () => {
    openView();

    expect(screen.getAllByText(packet.packet_hash).length).toBeGreaterThan(0);
    expect(screen.getByText(/Export Packet Prepared/i)).toBeInTheDocument();
    expect(screen.getByText(/Operator Review Pending/i)).toBeInTheDocument();
    expect(screen.getByText(/Checklist Pending/i)).toBeInTheDocument();
    expect(screen.getByText(/Manual Publish URL Empty/i)).toBeInTheDocument();
    expect(screen.getByText(/Manual Metrics Empty/i)).toBeInTheDocument();
    expect(screen.getByText(/Off-System Operator Action Required/i)).toBeInTheDocument();
    expect(screen.getByText(/Reconciliation Blocked Until Evidence Recorded/i)).toBeInTheDocument();
    expect(screen.getByText(/Live Dispatch Disabled/i)).toBeInTheDocument();
  });

  it('renders placeholder fields and warning', () => {
    openView();

    expect(screen.getByText("Reconciliation Blocked")).toBeInTheDocument();
    expect(screen.getByText("Manual Publish URL")).toBeInTheDocument();
    expect(screen.getByText("Manual Publish Timestamp")).toBeInTheDocument();
    expect(screen.getByText("Manual Metrics Snapshot")).toBeInTheDocument();
    expect(screen.getByText("Platform Post ID")).toBeInTheDocument();
    expect(screen.getByText("Platform Permalink")).toBeInTheDocument();
    expect(screen.getByText("Operator Notes")).toBeInTheDocument();
  });

  it('shows disabled actions and no enabled live affordance', () => {
    openView();

    for (const id of [
      'reconciliation-disabled-publish',
      'reconciliation-disabled-send',
      'reconciliation-disabled-schedule',
      'reconciliation-disabled-connect-account',
      'reconciliation-disabled-verify-credentials',
      'reconciliation-disabled-sync-platform',
      'reconciliation-disabled-live-dispatch',
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

  it('updates inspector on clicking steps and placeholders', () => {
    openView();

    fireEvent.click(document.getElementById('reconciliation-step-export_packet_prepared')!);
    let rail = document.getElementById('inspector-rail')!;
    expect(within(rail).getByText(/reconciliation lifecycle step/i)).toBeInTheDocument();
    expect(within(rail).getAllByText('export_packet_prepared').length).toBeGreaterThan(0);

    fireEvent.click(document.getElementById('reconciliation-field-manual_publish_url')!);
    rail = document.getElementById('inspector-rail')!;
    expect(within(rail).getByText(/reconciliation placeholder field/i)).toBeInTheDocument();
    expect(within(rail).getAllByText('manual_publish_url').length).toBeGreaterThan(0);
  });
});
