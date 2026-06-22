import { describe, expect, it } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { createElement } from 'react';
import App from '../App';
import { operatorInputCapturePrecheckAdapter as adapter } from '../data/operatorInputCapturePrecheckAdapter';

function openWriterStudio() {
  render(createElement(App));
  const tab = document.getElementById('nav-writer_studio');
  if (tab) {
    fireEvent.click(tab);
  }
}

describe('Operator Input Capture Precheck UI', () => {
  it('renders the readonly capture-disabled panel and field policy', () => {
    openWriterStudio();

    expect(screen.getByText('Operator Input Capture Precheck')).toBeInTheDocument();
    expect(screen.getByText('Readonly schema-only input surface · capture disabled')).toBeInTheDocument();
    expect(screen.getByText('BLOCKED_OPERATOR_INPUT_CAPTURE_NOT_ENABLED')).toBeInTheDocument();
    expect(screen.getAllByText('PENDING_OPERATOR_INPUT').length).toBeGreaterThanOrEqual(
      adapter.requiredInputFields.length,
    );
    expect(screen.getAllByText('capture_enabled: false').length).toBeGreaterThanOrEqual(
      adapter.requiredInputFields.length,
    );
    expect(screen.getAllByText('editable_in_this_task: false').length).toBeGreaterThanOrEqual(
      adapter.requiredInputFields.length,
    );
  });

  it('updates the Inspector Rail when clicking Inspect Input Precheck', () => {
    openWriterStudio();

    const btn = document.getElementById('btn-inspect-input-precheck-packet')!;
    fireEvent.click(btn);

    const rail = document.getElementById('inspector-rail')!;
    expect(within(rail).getAllByText(/OPERATOR INPUT CAPTURE PRECHECK PACKET/i).length).toBeGreaterThan(0);
    expect(within(rail).getByText(adapter.packet.task_label)).toBeInTheDocument();
    expect(within(rail).getAllByText(adapter.packet.packet_hash).length).toBeGreaterThan(0);
    expect(within(rail).getByText(adapter.packet.global_operator_input_capture_status)).toBeInTheDocument();
  });

  it('updates the Inspector Rail when clicking an input precheck item row', () => {
    openWriterStudio();

    const firstItem = adapter.inputCapturePrecheckItems[0];
    const row = document.getElementById(`input-precheck-item-row-${firstItem.intent_item_id}`)!;
    fireEvent.click(row);

    const rail = document.getElementById('inspector-rail')!;
    expect(within(rail).getByText(/INPUT CAPTURE PRECHECK ITEM/i)).toBeInTheDocument();
    expect(within(rail).getByText(firstItem.relative_path)).toBeInTheDocument();
    expect(within(rail).getByText(firstItem.evidence_role)).toBeInTheDocument();
    expect(within(rail).getByText('capture_enabled: false')).toBeInTheDocument();
    expect(within(rail).getByText('editable_in_this_task: false')).toBeInTheDocument();
  });

  it('does not introduce input, textarea, or form elements', () => {
    openWriterStudio();

    expect(document.querySelectorAll('input').length).toBe(0);
    expect(document.querySelectorAll('textarea').length).toBe(0);
    expect(document.querySelectorAll('form').length).toBe(0);
  });
});
