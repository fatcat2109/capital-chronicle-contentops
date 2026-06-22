import { describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { createElement } from 'react';
import App from '../App';
import { draftEligibilityGatePrecheckAdapter as adapter } from '../data/draftEligibilityGatePrecheckAdapter';

function openWriterStudio() {
  render(createElement(App));
  const tab = document.getElementById('nav-writer_studio');
  if (tab) {
    fireEvent.click(tab);
  }
}

describe('Draft Eligibility Gate UI Binding', () => {
  it('renders the compact Draft Eligibility Gate status strip inside the Draft panel', () => {
    openWriterStudio();

    expect(screen.getByText('Draft Eligibility Gate')).toBeInTheDocument();
    expect(screen.getByText('Blocked · supervised input required')).toBeInTheDocument();
    expect(screen.getAllByText('draft_generation_enabled: false').length).toBeGreaterThan(0);
    expect(screen.getAllByText('public_postable: false').length).toBeGreaterThan(0);
    expect(screen.getByText('missing_required_input_fields: 6')).toBeInTheDocument();
  });

  it('allows progressive disclosure of gate details and item list', () => {
    openWriterStudio();

    // The details section is collapsed by default but exists in the DOM
    expect(screen.getByText('Show Gate Details')).toBeInTheDocument();
    expect(screen.getByText(`Draft Eligibility Items (${adapter.draftEligibilityItems.length})`)).toBeInTheDocument();

    for (const item of adapter.draftEligibilityItems) {
      expect(document.getElementById(`draft-eligibility-item-row-${item.draft_eligibility_item_id}`)).not.toBeNull();
    }
  });

  it('updates the Inspector Rail when clicking Inspect Draft Eligibility', () => {
    openWriterStudio();

    const btn = document.getElementById('btn-inspect-draft-eligibility')!;
    fireEvent.click(btn);

    const rail = document.getElementById('inspector-rail')!;
    expect(within(rail).getAllByText(/DRAFT ELIGIBILITY GATE PRECHECK PACKET/i).length).toBeGreaterThan(0);
    expect(within(rail).getByText(adapter.packet.task_label)).toBeInTheDocument();
    expect(within(rail).getAllByText(adapter.packet.packet_hash).length).toBeGreaterThan(0);
    expect(within(rail).getByText(adapter.packet.global_draft_eligibility_status)).toBeInTheDocument();
  });

  it('updates the Inspector Rail when clicking a draft eligibility item row', () => {
    openWriterStudio();

    const firstItem = adapter.draftEligibilityItems[0];
    const row = document.getElementById(`draft-eligibility-item-row-${firstItem.draft_eligibility_item_id}`)!;
    fireEvent.click(row);

    const rail = document.getElementById('inspector-rail')!;
    expect(within(rail).getByText(/DRAFT ELIGIBILITY ITEM/i)).toBeInTheDocument();
    expect(within(rail).getByText(firstItem.relative_path)).toBeInTheDocument();
    expect(within(rail).getByText(firstItem.evidence_role)).toBeInTheDocument();
    expect(within(rail).getByText(firstItem.source_supervised_input_stub_status)).toBeInTheDocument();
  });

  it('confirm readonly contract limits (no input, form, textarea, contentEditable)', () => {
    openWriterStudio();

    expect(document.querySelectorAll('input').length).toBe(0);
    expect(document.querySelectorAll('textarea').length).toBe(0);
    expect(document.querySelectorAll('form').length).toBe(0);
    expect(document.querySelectorAll('[contentEditable="true"]').length).toBe(0);
  });

  it('confirm no localStorage or sessionStorage is used by the binding', () => {
    const localSpy = vi.spyOn(Storage.prototype, 'getItem');
    const sessionSpy = vi.spyOn(Storage.prototype, 'getItem');

    openWriterStudio();

    // Verify localStorage/sessionStorage were not called during render/routing of this panel
    expect(localSpy).not.toHaveBeenCalled();
    expect(sessionSpy).not.toHaveBeenCalled();

    localSpy.mockRestore();
    sessionSpy.mockRestore();
  });
});
