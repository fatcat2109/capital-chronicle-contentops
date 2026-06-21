import { describe, expect, it } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { createElement } from 'react';
import App from '../App';
import { editorialBriefReviewAdapter as adapter } from '../data/editorialBriefReviewAdapter';

function openWriterStudio() {
  render(createElement(App));
  const tab = document.getElementById('nav-writer_studio');
  if (tab) {
    fireEvent.click(tab);
  }
}

describe('Editorial Brief Review Queue UI', () => {
  it('renders the Editorial Brief Review Queue panel and candidate items', () => {
    openWriterStudio();

    expect(screen.getByText('Editorial Brief Review Queue')).toBeInTheDocument();
    expect(screen.getByText('Local candidate metadata bridge · no article draft')).toBeInTheDocument();

    // Check packet details
    expect(screen.getByText(adapter.packet.packet_hash)).toBeInTheDocument();
    expect(screen.getByText(adapter.packet.source_bridge_task_label)).toBeInTheDocument();

    // Check candidate counts
    expect(screen.getByText(`Candidate review items (${adapter.packet.candidate_count})`)).toBeInTheDocument();

    // Verify candidate rows exist
    expect(screen.getByText('STEP1_OFFICIAL_TEXT_LIVE_PROBE_MANIFEST_V1')).toBeInTheDocument();
    expect(screen.getByText('BEA_BLS_CENSUS_NORMALIZED_CONTRACT_V1')).toBeInTheDocument();
  });

  it('updates the Inspector Rail when clicking Inspect Packet', () => {
    openWriterStudio();

    const btn = document.getElementById('btn-inspect-review-packet')!;
    fireEvent.click(btn);

    const rail = document.getElementById('inspector-rail')!;
    expect(within(rail).getAllByText(/EDITORIAL BRIEF REVIEW PACKET/i).length).toBeGreaterThan(0);
    expect(within(rail).getByText(adapter.packet.task_label)).toBeInTheDocument();
    expect(within(rail).getAllByText(adapter.packet.packet_hash).length).toBeGreaterThan(0);
  });

  it('updates the Inspector Rail when clicking a candidate row', () => {
    openWriterStudio();

    const row = document.getElementById('candidate-row-STEP1_OFFICIAL_TEXT_LIVE_PROBE_MANIFEST_V1')!;
    fireEvent.click(row);

    const rail = document.getElementById('inspector-rail')!;
    expect(within(rail).getByText(/CANDIDATE REVIEW ITEM/i)).toBeInTheDocument();
    expect(within(rail).getByText('docs/research/database_foundation/pre_ia_acceleration/STEP1_OFFICIAL_TEXT_LIVE_PROBE_MANIFEST_V1.json')).toBeInTheDocument();
    expect(within(rail).getByText('manifest')).toBeInTheDocument();
  });
});
