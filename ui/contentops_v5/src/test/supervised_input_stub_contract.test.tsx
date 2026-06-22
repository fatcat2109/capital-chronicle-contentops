import { describe, expect, it } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { createElement } from 'react';
import App from '../App';
import { supervisedInputStubContractAdapter as adapter } from '../data/supervisedInputStubContractAdapter';

function openWriterStudio() {
  render(createElement(App));
  const tab = document.getElementById('nav-writer_studio');
  if (tab) {
    fireEvent.click(tab);
  }
}

describe('Supervised Input Stub Contract UI', () => {
  it('renders the readonly supervised input stub panel and field policy', () => {
    openWriterStudio();

    expect(screen.getByText('Supervised Input Stub Contract')).toBeInTheDocument();
    expect(screen.getByText('Readonly supervised input stub · future capture only')).toBeInTheDocument();
    expect(screen.getByText('BLOCKED_SUPERVISED_INPUT_CAPTURE_NOT_ENABLED')).toBeInTheDocument();
    expect(screen.getByText('Supervised Capture Locked')).toBeInTheDocument();
    expect(screen.getAllByText('PENDING_OPERATOR_INPUT').length).toBeGreaterThanOrEqual(
      adapter.requiredInputFields.length,
    );
    expect(screen.getAllByText('current_value: null').length).toBeGreaterThanOrEqual(
      adapter.requiredInputFields.length,
    );
    expect(screen.getAllByText('capture_enabled_in_this_task: false').length).toBeGreaterThanOrEqual(
      adapter.requiredInputFields.length,
    );
    expect(screen.getAllByText('editable_in_this_task: false').length).toBeGreaterThanOrEqual(
      adapter.requiredInputFields.length,
    );
    expect(screen.getAllByText('persistence_enabled: false').length).toBeGreaterThanOrEqual(
      adapter.requiredInputFields.length,
    );
    expect(screen.getByText('future_capture_modes_enabled_in_this_task: false')).toBeInTheDocument();
  });

  it('renders all supervised input stub rows and compliance strips', () => {
    openWriterStudio();

    expect(screen.getByText(`Supervised Stub Items (${adapter.packet.source_input_capture_precheck_item_count})`)).toBeInTheDocument();
    for (const item of adapter.supervisedInputStubItems) {
      expect(document.getElementById(`supervised-input-stub-row-${item.stub_item_id}`)).not.toBeNull();
    }
    expect(screen.getByText('Forbidden current actions (Strict no-capture locks)')).toBeInTheDocument();
    expect(screen.getAllByText('Disallowed output enforcement (Strict compliance locks)').length).toBeGreaterThan(0);
    expect(screen.getAllByText('actual_input_capture').length).toBeGreaterThan(0);
    expect(screen.getAllByText('content_generation').length).toBeGreaterThan(0);
  });

  it('updates the Inspector Rail when clicking Inspect Stub Contract', () => {
    openWriterStudio();

    const btn = document.getElementById('btn-inspect-supervised-input-stub-contract')!;
    fireEvent.click(btn);

    const rail = document.getElementById('inspector-rail')!;
    expect(within(rail).getAllByText(/SUPERVISED INPUT STUB CONTRACT PACKET/i).length).toBeGreaterThan(0);
    expect(within(rail).getByText(adapter.packet.task_label)).toBeInTheDocument();
    expect(within(rail).getAllByText(adapter.packet.packet_hash).length).toBeGreaterThan(0);
    expect(within(rail).getByText(adapter.packet.global_supervised_input_stub_status)).toBeInTheDocument();
  });

  it('updates the Inspector Rail when clicking a supervised input stub item row', () => {
    openWriterStudio();

    const firstItem = adapter.supervisedInputStubItems[0];
    const row = document.getElementById(`supervised-input-stub-row-${firstItem.stub_item_id}`)!;
    fireEvent.click(row);

    const rail = document.getElementById('inspector-rail')!;
    expect(within(rail).getByText(/SUPERVISED INPUT STUB ITEM/i)).toBeInTheDocument();
    expect(within(rail).getByText(firstItem.relative_path)).toBeInTheDocument();
    expect(within(rail).getByText(firstItem.evidence_role)).toBeInTheDocument();
    expect(within(rail).getByText('current_value: null')).toBeInTheDocument();
    expect(within(rail).getByText('placeholder_value: PENDING_OPERATOR_INPUT')).toBeInTheDocument();
    expect(within(rail).getByText('capture_enabled_in_this_task: false')).toBeInTheDocument();
  });

  it('does not introduce input, textarea, or form elements', () => {
    openWriterStudio();

    expect(document.querySelectorAll('input').length).toBe(0);
    expect(document.querySelectorAll('textarea').length).toBe(0);
    expect(document.querySelectorAll('form').length).toBe(0);
  });
});
