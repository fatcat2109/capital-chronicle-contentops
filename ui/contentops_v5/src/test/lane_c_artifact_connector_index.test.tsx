import { describe, expect, it } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { createElement } from 'react';
import App from '../App';
import { laneCArtifactConnectorIndexPacket as packet } from '../data/laneCArtifactConnectorIndexPacket';

function openInventoryView() {
  render(createElement(App));
  const tab = document.getElementById('nav-content_inventory');
  if (tab) {
    fireEvent.click(tab);
  }
}

describe('Lane C Connector Index UI', () => {
  it('renders Lane C connector index title, stats, and families list', () => {
    openInventoryView();

    expect(screen.getByText('Lane C Connector Index')).toBeInTheDocument();
    expect(screen.getByText(/Connectors: 6 registered · review-only/i)).toBeInTheDocument();

    // Check stats and safety labels
    expect(screen.getByText('No live connector enabled')).toBeInTheDocument();
    expect(screen.getByText('Ingestion repo mutation: false')).toBeInTheDocument();
    expect(screen.getByText('DQR/Readiness not cleared')).toBeInTheDocument();

    // Check custom short connector names are rendered
    expect(screen.getByText('artifact')).toBeInTheDocument();
    expect(screen.getByText('lineage')).toBeInTheDocument();
    expect(screen.getByText('dqr')).toBeInTheDocument();

    // Check proof lists
    expect(screen.getByText('cryptographic_manifest_proof')).toBeInTheDocument();
    expect(screen.getByText('manual_operator_review_proof')).toBeInTheDocument();
  });

  it('updates the Inspector Rail when clicking Inspect Index', () => {
    openInventoryView();

    const btn = document.getElementById('btn-inspect-lane-c-connector-packet')!;
    fireEvent.click(btn);

    const rail = document.getElementById('inspector-rail')!;
    expect(within(rail).getAllByText(/LANE C ARTIFACT CONNECTOR INDEX PACKET/i).length).toBeGreaterThan(0);
    expect(within(rail).getByText(packet.task_label)).toBeInTheDocument();
    expect(within(rail).getAllByText(packet.matrix_version).length).toBeGreaterThan(0);
  });

  it('updates the Inspector Rail when clicking a connector family row', () => {
    openInventoryView();

    const row = document.getElementById('lane-c-connector-row-local_capital_chronicle_artifact_packet')!;
    fireEvent.click(row);

    const rail = document.getElementById('inspector-rail')!;
    expect(within(rail).getAllByText(/LANE C CONNECTOR FAMILY/i).length).toBeGreaterThan(0);
    expect(within(rail).getByText('local capital chronicle artifact packet')).toBeInTheDocument();
    expect(within(rail).getByText('fixtures/lane_c/connectors/artifact_packet/*.json')).toBeInTheDocument();
  });
});
