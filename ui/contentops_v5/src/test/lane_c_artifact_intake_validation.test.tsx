import { describe, expect, it } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { createElement } from 'react';
import App from '../App';
import { laneCArtifactIntakePacket as packet } from '../data/laneCArtifactIntakePacket';

function openInventoryView() {
  render(createElement(App));
  const tab = document.getElementById('nav-content_inventory');
  if (tab) {
    fireEvent.click(tab);
  }
}

describe('Lane C Artifact Intake UI', () => {
  it('renders Lane C section, statistics, checks, and candidates', () => {
    openInventoryView();

    expect(screen.getByText('Lane C Artifact Intake Pipeline')).toBeInTheDocument();
    expect(screen.getByText('Lane C artifact intake: review-only')).toBeInTheDocument();

    // Check statistics/labels
    expect(screen.getByText('DQR / Readiness not cleared')).toBeInTheDocument();
    expect(screen.getByText('Proxy / Degraded labels preserved')).toBeInTheDocument();

    // Check candidate columns/shortened IDs are rendered
    expect(screen.getByText('missing_manual_review')).toBeInTheDocument();
    expect(screen.getByText('stale_metadata')).toBeInTheDocument();
    expect(screen.getByText('degraded_proxy')).toBeInTheDocument();

    // Check validation checks exist
    expect(screen.getByText('artifact_identity_present')).toBeInTheDocument();
    expect(screen.getByText('no_network_or_api_call')).toBeInTheDocument();
  });

  it('updates the Inspector Rail when clicking Inspect Packet', () => {
    openInventoryView();

    const btn = document.getElementById('btn-inspect-lane-c-packet')!;
    fireEvent.click(btn);

    const rail = document.getElementById('inspector-rail')!;
    expect(within(rail).getAllByText(/LANE C ARTIFACT INTAKE VALIDATION PACKET/i).length).toBeGreaterThan(0);
    expect(within(rail).getByText(packet.task_label)).toBeInTheDocument();
    expect(within(rail).getAllByText(packet.matrix_version).length).toBeGreaterThan(0);
  });

  it('updates the Inspector Rail when clicking a candidate row', () => {
    openInventoryView();

    const row = document.getElementById('lane-c-candidate-row-valid_shape_but_blocked_missing_manual_review')!;
    fireEvent.click(row);

    const rail = document.getElementById('inspector-rail')!;
    expect(within(rail).getByText(/LANE C ARTIFACT INTAKE CANDIDATE/i)).toBeInTheDocument();
    expect(within(rail).getByText('valid shape but blocked missing manual review')).toBeInTheDocument();
    expect(within(rail).getByText('fixtures/lane_c/artifact_valid_shape.json')).toBeInTheDocument();
  });
});
