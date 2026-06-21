import { describe, expect, it } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { createElement } from 'react';
import App from '../App';
import { contentIntentGatePrecheckAdapter as adapter } from '../data/contentIntentGatePrecheckAdapter';

function openWriterStudio() {
  render(createElement(App));
  const tab = document.getElementById('nav-writer_studio');
  if (tab) {
    fireEvent.click(tab);
  }
}

describe('Content Intent Gate Precheck UI', () => {
  it('renders the Content Intent Gate Precheck panel and candidate items', () => {
    openWriterStudio();

    expect(screen.getByText('Content Intent Gate Precheck')).toBeInTheDocument();
    expect(screen.getByText('Local intent precheck · blocked until operator review')).toBeInTheDocument();

    // Check packet details
    expect(screen.getByText(adapter.packet.packet_hash)).toBeInTheDocument();
    expect(screen.getByText(adapter.packet.source_editorial_brief_review_packet_hash)).toBeInTheDocument();

    // Check candidate counts
    expect(screen.getByText(`Candidate Gate Items (${adapter.packet.source_candidate_count})`)).toBeInTheDocument();

    // Verify candidate rows exist and READY_FOR_OPERATOR_INTENT_REVIEW is rendered
    expect(screen.getAllByText('READY_FOR_OPERATOR_INTENT_REVIEW').length).toBeGreaterThan(0);
  });

  it('updates the Inspector Rail when clicking Inspect Precheck', () => {
    openWriterStudio();

    const btn = document.getElementById('btn-inspect-precheck-packet')!;
    fireEvent.click(btn);

    const rail = document.getElementById('inspector-rail')!;
    expect(within(rail).getAllByText(/CONTENT INTENT GATE PRECHECK/i).length).toBeGreaterThan(0);
    expect(within(rail).getByText(adapter.packet.task_label)).toBeInTheDocument();
    expect(within(rail).getAllByText(adapter.packet.packet_hash).length).toBeGreaterThan(0);
  });

  it('updates the Inspector Rail when clicking a candidate row', () => {
    openWriterStudio();

    const row = document.getElementById('precheck-candidate-row-STEP1_OFFICIAL_TEXT_LIVE_PROBE_MANIFEST_V1')!;
    fireEvent.click(row);

    const rail = document.getElementById('inspector-rail')!;
    expect(within(rail).getByText(/CANDIDATE GATE ITEM/i)).toBeInTheDocument();
    expect(within(rail).getByText('docs/research/database_foundation/pre_ia_acceleration/STEP1_OFFICIAL_TEXT_LIVE_PROBE_MANIFEST_V1.json')).toBeInTheDocument();
    expect(within(rail).getByText('manifest')).toBeInTheDocument();
  });
});
