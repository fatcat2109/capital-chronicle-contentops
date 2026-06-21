import { describe, expect, it } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { createElement } from 'react';
import App from '../App';
import { manualExportPilotVerificationPacket as packet } from '../data/manualExportPilotVerificationPacket';

function openView() {
  render(createElement(App));
  fireEvent.click(document.getElementById('nav-manual_export_pilot_verification')!);
}

describe('Manual Export / Pilot Verification contract data', () => {
  it('keeps all targets manual-only, no-api, no-credential, not dispatchable', () => {
    for (const target of packet.platform_targets) {
      expect(target.manual_only).toBe(true);
      expect(target.not_live).toBe(true);
      expect(target.no_api).toBe(true);
      expect(target.no_credentials).toBe(true);
      expect(target.no_scheduler).toBe(true);
      expect(target.public_postable).toBe(false);
      expect(target.dispatch_ready).toBe(false);
    }
  });

  it('keeps manual URL, metrics, and signature placeholders empty', () => {
    expect(packet.manual_publish_url_placeholder.value).toBe('');
    expect(packet.manual_metrics_placeholder.value).toBe('');
    expect(packet.review_signature_placeholder.signature_value).toBe('');
    expect(packet.review_signature_placeholder.cryptographic_signature).toBe(false);
    expect(packet.review_signature_placeholder.uses_secret_material).toBe(false);
  });
});

describe('Manual Export / Pilot Verification UI', () => {
  it('adds navigation and renders safety-first heading', () => {
    openView();

    expect(document.getElementById('nav-manual_export_pilot_verification')).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(/manual export/i);
    expect(screen.getAllByText(/Manual Export Only/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/No platform API/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/No credentials loaded/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/No live dispatch/i).length).toBeGreaterThan(0);
  });

  it('renders source hash and active platform copy blocks', () => {
    openView();

    expect(screen.getAllByText(packet.source_read_model_packet_hash).length).toBeGreaterThan(0);
    expect(screen.getByText(/X manual post draft/i)).toBeInTheDocument();
    expect(screen.getByText(/Telegram Channel manual message draft/i)).toBeInTheDocument();
    expect(screen.getByText(/Substack manual newsletter\/export draft/i)).toBeInTheDocument();
    expect(screen.getByText(/LinkedIn manual post draft/i)).toBeInTheDocument();
  });

  it('shows disabled live-action controls and no enabled live affordance', () => {
    openView();

    for (const id of [
      'manual-export-disabled-publish',
      'manual-export-disabled-send',
      'manual-export-disabled-schedule',
      'manual-export-disabled-connect-account',
      'manual-export-disabled-verify-credentials',
      'manual-export-disabled-sync-platform',
      'manual-export-disabled-live-dispatch',
    ]) {
      expect(document.getElementById(id)).toBeInTheDocument();
    }

    const enabledButtons = screen
      .getAllByRole('button')
      .filter((button) => !(button as HTMLButtonElement).disabled);
    for (const button of enabledButtons) {
      expect(button.textContent ?? '').not.toMatch(/publish now|post now|send now|schedule now|connect live|verify credentials now|sync platform now|dispatch live/i);
    }
  });

  it('updates inspector for target, copy block, and checklist item', () => {
    openView();

    fireEvent.click(document.getElementById('manual-export-target-x_manual_post_copy')!);
    let rail = document.getElementById('inspector-rail')!;
    expect(within(rail).getByText(/manual export target/i)).toBeInTheDocument();
    expect(within(rail).getAllByText('x_manual_post_copy').length).toBeGreaterThan(0);

    fireEvent.click(document.getElementById('manual-copy-block-copy_x_manual_post_draft')!);
    rail = document.getElementById('inspector-rail')!;
    expect(within(rail).getByText(/manual copy block/i)).toBeInTheDocument();
    expect(within(rail).getAllByText('copy_x_manual_post_draft').length).toBeGreaterThan(0);

    fireEvent.click(document.getElementById('manual-export-check-check_no_credentials')!);
    rail = document.getElementById('inspector-rail')!;
    expect(within(rail).getByText(/manual export checklist item/i)).toBeInTheDocument();
    expect(within(rail).getAllByText('check_no_credentials').length).toBeGreaterThan(0);
  });
});
