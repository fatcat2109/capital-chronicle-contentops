import { describe, expect, it } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { createElement } from 'react';
import App from '../App';
import { operatorRunbookIndexPacket as packet } from '../data/operatorRunbookIndexPacket';

function openRunbookView() {
  render(createElement(App));
  fireEvent.click(document.getElementById('nav-operator_runbook_index')!);
}

describe('Local Operator Runbook Index UI', () => {
  it('renders header, state tags, and all 5 workflow steps', () => {
    openRunbookView();

    expect(screen.getByText(/Local Operator Runbook/i)).toBeInTheDocument();
    expect(screen.getAllByText('LOCAL_PRE_ALPHA').length).toBeGreaterThan(0);
    expect(screen.getAllByText('LOCAL ONLY').length).toBeGreaterThan(0);

    // Verify all 5 step titles/ids exist
    expect(screen.getAllByText('preflight_bundle').length).toBeGreaterThan(0);
    expect(screen.getAllByText('manual_export_pilot_verification').length).toBeGreaterThan(0);
    expect(screen.getAllByText('operator_review_queue').length).toBeGreaterThan(0);
    expect(screen.getAllByText('manual_pilot_reconciliation').length).toBeGreaterThan(0);
    expect(screen.getAllByText('evidence_vault_manual_pilot_audit').length).toBeGreaterThan(0);

    // Verify card titles
    expect(screen.getAllByText('Preflight Bundle Validation').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Manual Export & Verification').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Operator Review Queue').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Manual Pilot Reconciliation').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Evidence Vault Audit').length).toBeGreaterThan(0);
  });

  it('renders step details, human actions, and system limits', () => {
    openRunbookView();

    // Check preflight step details
    expect(screen.getAllByText(/Automated preflight checks for the content bundle/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Inspect all active gates, bundle properties/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Modify live server states or communicate/i).length).toBeGreaterThan(0);
  });

  it('displays blocked status, missing evidence and references', () => {
    openRunbookView();

    // Operational Blocker section
    expect(screen.getByText('Operational Blocker Summary')).toBeInTheDocument();
    expect(screen.getAllByText('Reconciliation Blocked').length).toBeGreaterThan(0);

    // Missing evidence list
    expect(screen.getAllByText('manual_publish_url').length).toBeGreaterThan(0);
    expect(screen.getAllByText('manual_publish_timestamp').length).toBeGreaterThan(0);
    expect(screen.getAllByText('manual_metrics_snapshot').length).toBeGreaterThan(0);

    // References
    expect(screen.getAllByText('docs/automation/0175AD/v5_local_operator_runbook_index_contract.md').length).toBeGreaterThan(0);
    expect(screen.getAllByText('docs/automation/0175AD/v5_local_operator_runbook_index_contract_packet.json').length).toBeGreaterThan(0);
  });

  it('proves all platform publishing and dispatch actions are fully disabled', () => {
    openRunbookView();

    // Locked boundary text
    expect(screen.getByText(/Runbook index confirms all automated publishing, scheduler execution/i)).toBeInTheDocument();

    // Verify active buttons have no live publish/dispatch strings
    const enabledButtons = screen
      .getAllByRole('button')
      .filter((button) => !(button as HTMLButtonElement).disabled);
    for (const button of enabledButtons) {
      expect(button.textContent ?? '').not.toMatch(/publish now|post now|send now|schedule now|connect live|verify credentials now|sync platform now|dispatch live/i);
    }
  });

  it('updates the Inspector Rail when clicking a step card or map button', () => {
    openRunbookView();

    // Click inspect on step 2 card
    const card2 = document.getElementById('runbook-step-card-manual_export_pilot_verification')!;
    fireEvent.click(within(card2).getByText('Inspect evidence'));

    const rail = document.getElementById('inspector-rail')!;
    expect(within(rail).getByText(/RUNBOOK STEP/i)).toBeInTheDocument();
    expect(within(rail).getAllByText('manual_export_pilot_verification').length).toBeGreaterThan(0);
  });

  it('navigates locally when clicking Open local view without mutating state', () => {
    openRunbookView();

    // Click Open local view on preflight step
    const card1 = document.getElementById('runbook-step-card-preflight_bundle')!;
    fireEvent.click(within(card1).getByText('Open local view'));

    // App view should switch to preflight_bundle
    expect(screen.getByText('Preflight Bundle')).toBeInTheDocument();
  });
});
