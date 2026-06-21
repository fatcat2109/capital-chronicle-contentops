import { describe, expect, it } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { createElement } from 'react';
import App from '../App';
import { reviewOnlyContentIntentAdapter as adapter } from '../data/reviewOnlyContentIntentAdapter';

function openWriterStudio() {
  render(createElement(App));
  const tab = document.getElementById('nav-writer_studio');
  if (tab) {
    fireEvent.click(tab);
  }
}

describe('Review-Only Content Intent UI', () => {
  it('renders the Review-Only Content Intent panel and candidate items', () => {
    openWriterStudio();

    expect(screen.getByText('Review-Only Content Intent')).toBeInTheDocument();
    expect(screen.getByText('Local intent packet · blocked pending operator input')).toBeInTheDocument();

    // Check packet details
    expect(screen.getByText(adapter.packet.packet_hash)).toBeInTheDocument();
    expect(screen.getByText(adapter.packet.source_content_intent_gate_precheck_packet_hash)).toBeInTheDocument();

    // Check candidate counts
    expect(screen.getByText(`Review-Only Intent Items (${adapter.packet.source_candidate_count})`)).toBeInTheDocument();

    // Verify candidate rows exist and REVIEW_ONLY_INTENT_PENDING_OPERATOR_INPUT is rendered
    expect(screen.getAllByText('REVIEW_ONLY_INTENT_PENDING_OPERATOR_INPUT').length).toBeGreaterThan(0);
  });

  it('updates the Inspector Rail when clicking Inspect Intent', () => {
    openWriterStudio();

    const btn = document.getElementById('btn-inspect-intent-packet')!;
    fireEvent.click(btn);

    const rail = document.getElementById('inspector-rail')!;
    expect(within(rail).getAllByText(/REVIEW-ONLY CONTENT INTENT PACKET/i).length).toBeGreaterThan(0);
    expect(within(rail).getByText(adapter.packet.task_label)).toBeInTheDocument();
    expect(within(rail).getAllByText(adapter.packet.packet_hash).length).toBeGreaterThan(0);
  });

  it('updates the Inspector Rail when clicking a candidate row', () => {
    openWriterStudio();

    const row = document.getElementById('intent-item-row-intent_item_STEP1_OFFICIAL_TEXT_LIVE_PROBE_MANIFEST_V1')!;
    fireEvent.click(row);

    const rail = document.getElementById('inspector-rail')!;
    expect(within(rail).getByText(/REVIEW ONLY INTENT ITEM/i)).toBeInTheDocument();
    expect(within(rail).getByText('docs/research/database_foundation/pre_ia_acceleration/STEP1_OFFICIAL_TEXT_LIVE_PROBE_MANIFEST_V1.json')).toBeInTheDocument();
    expect(within(rail).getByText('manifest')).toBeInTheDocument();
  });
});
