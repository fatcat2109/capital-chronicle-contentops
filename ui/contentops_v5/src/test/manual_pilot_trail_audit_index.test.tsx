import { describe, expect, it } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { createElement } from 'react';
import App from '../App';
import { manualPilotTrailReconciliationAuditPacket as packet } from '../data/manualPilotTrailReconciliationAuditPacket';

function openAuditView() {
  render(createElement(App));
  fireEvent.click(document.getElementById('nav-evidence_vault')!);
  fireEvent.click(document.getElementById('vault-tab-audit')!);
}

describe('Manual Pilot Trail Audit Index UI', () => {
  it('renders Evidence Vault tab and switches to Manual Pilot Audit', () => {
    openAuditView();

    expect(screen.getByText(/Manual Pilot Audit Overview/i)).toBeInTheDocument();
    expect(screen.getByText(/verified blocked\/manual-only/i)).toBeInTheDocument();
    expect(screen.getAllByText(packet.packet_hash).length).toBeGreaterThan(0);
  });

  it('renders all 14 invariants and source packets', () => {
    openAuditView();

    // Verify key invariants from 0175AA list
    expect(screen.getByText('uw_exists_and_manual_only')).toBeInTheDocument();
    expect(screen.getByText('uy_references_uw_correctly')).toBeInTheDocument();
    expect(screen.getByText('uz_references_uy_and_uw_correctly')).toBeInTheDocument();
    expect(screen.getByText('placeholders_remain_empty')).toBeInTheDocument();
    expect(screen.getByText('no_banned_financial_language')).toBeInTheDocument();

    // Verify source packets render
    expect(screen.getByText('0174UW_manual_export')).toBeInTheDocument();
    expect(screen.getByText('0174UY_operator_review')).toBeInTheDocument();
    expect(screen.getByText('0174UZ_reconciliation')).toBeInTheDocument();
  });

  it('renders missing evidence indicators and zero contradictions', () => {
    openAuditView();

    // Verify missing evidence list
    expect(screen.getByText('manual_publish_url')).toBeInTheDocument();
    expect(screen.getByText('manual_publish_timestamp')).toBeInTheDocument();
    expect(screen.getByText('manual_metrics_snapshot')).toBeInTheDocument();

    // Zero contradictions message
    expect(screen.getByText(/No Contradictions/i)).toBeInTheDocument();
    expect(screen.getByText(/Audit chain is internally consistent/i)).toBeInTheDocument();
  });

  it('displays local-only compliance refs and disabled live actions', () => {
    openAuditView();

    // Monospace file paths references
    expect(screen.getByText('docs/automation/0175AA/v5_manual_pilot_trail_reconciliation_audit_contract.md')).toBeInTheDocument();
    expect(screen.getByText('docs/automation/0175AA/v5_manual_pilot_trail_reconciliation_audit_contract_packet.json')).toBeInTheDocument();

    // Hard bounds disabled message
    expect(screen.getByText(/Audit confirms all platform publishing, account connection, credential sync/i)).toBeInTheDocument();

    // Verify buttons do not contain active live trigger text
    const enabledButtons = screen
      .getAllByRole('button')
      .filter((button) => !(button as HTMLButtonElement).disabled);
    for (const button of enabledButtons) {
      expect(button.textContent ?? '').not.toMatch(/publish now|post now|send now|schedule now|connect live|verify credentials now|sync platform now|dispatch live/i);
    }
  });

  it('updates inspector when clicking invariants and audit packet', () => {
    openAuditView();

    // Click invariant row
    fireEvent.click(document.getElementById('audit-invariant-row-uw_exists_and_manual_only')!);
    let rail = document.getElementById('inspector-rail')!;
    expect(within(rail).getByText(/audit invariant/i)).toBeInTheDocument();
    expect(within(rail).getAllByText('uw_exists_and_manual_only').length).toBeGreaterThan(0);

    // Click select packet button
    fireEvent.click(document.getElementById('select-audit-packet-btn')!);
    rail = document.getElementById('inspector-rail')!;
    expect(within(rail).getByText(/manual pilot audit packet/i)).toBeInTheDocument();
    expect(within(rail).getAllByText(packet.audit_id).length).toBeGreaterThan(0);
  });
});
