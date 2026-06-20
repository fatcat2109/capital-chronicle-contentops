import { describe, expect, it } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { createElement } from 'react';
import App from '../App';
import { preflightBundlePacket } from '../data/preflightBundlePacket';

describe('Preflight Bundle view routing', () => {
  it('has a preflight bundle route that is reachable', () => {
    render(createElement(App));
    expect(document.getElementById('nav-preflight_bundle')).toBeInTheDocument();
  });

  it('routes to Preflight Bundle and renders its header and safety strip', () => {
    render(createElement(App));
    fireEvent.click(document.getElementById('nav-preflight_bundle')!);

    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
      /preflight bundle & readiness gate/i
    );
    expect(screen.getByText(/LOCAL ONLY \/ NOT LIVE \/ NOT PUBLIC-POSTABLE/i)).toBeInTheDocument();
  });
});

describe('Preflight Bundle Platform Safety Matrix tab', () => {
  it('covers all 10 target platforms in the safety matrix table', () => {
    render(createElement(App));
    fireEvent.click(document.getElementById('nav-preflight_bundle')!);
    fireEvent.click(screen.getByRole('tab', { name: /platform safety matrix/i }));

    const expectedPlatforms = [
      'x',
      'telegram_remote_operator',
      'telegram_channel_destination',
      'substack_newsletter',
      'linkedin',
      'threads',
      'instagram',
      'facebook_page',
      'tiktok',
      'youtube',
    ];

    for (const platformId of expectedPlatforms) {
      expect(document.getElementById(`platform-row-${platformId}`)).toBeInTheDocument();
    }
  });

  it('renders platform blockers and missing proofs summaries', () => {
    render(createElement(App));
    fireEvent.click(document.getElementById('nav-preflight_bundle')!);
    fireEvent.click(screen.getByRole('tab', { name: /platform safety matrix/i }));

    expect(screen.getByText(/platform blockers summary/i)).toBeInTheDocument();
    expect(screen.getByText(/missing proofs summary/i)).toBeInTheDocument();

    // Check specific blockers/proofs from packet json
    expect(screen.getAllByText(/x_app_access_gap/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/youtube_oauth_flow_closed/i).length).toBeGreaterThan(0);
  });

  it('selects a platform state and updates the inspector rail', () => {
    render(createElement(App));
    fireEvent.click(document.getElementById('nav-preflight_bundle')!);
    fireEvent.click(screen.getByRole('tab', { name: /platform safety matrix/i }));

    const xRow = document.getElementById('platform-row-x')!;
    fireEvent.click(xRow);

    const rail = document.getElementById('inspector-rail')!;
    expect(within(rail).getByText(/primary_distribution/i)).toBeInTheDocument();
    expect(within(rail).getByText(/key_names_only/i)).toBeInTheDocument();
  });
});

describe('Preflight Bundle Room Binding Matrix tab', () => {
  it('renders the 13 room binding prechecks and display policy summaries', () => {
    render(createElement(App));
    fireEvent.click(document.getElementById('nav-preflight_bundle')!);
    fireEvent.click(screen.getByRole('tab', { name: /room binding matrix/i }));

    // Verify 13 room rows are rendered
    const rooms = [
      'command_center',
      'evidence_vault',
      'approval_queue',
      'platform_payload_preview',
      'substack_manual_export',
      'credential_boundary',
      'account_binding',
      'live_readiness_gate',
      'manual_publish_metrics',
      'content_performance_review',
      'internal_alpha_artifact_intake',
      'writer_studio',
      'grounded_news_workbench',
    ];

    for (const roomId of rooms) {
      expect(document.getElementById(`room-row-${roomId}`)).toBeInTheDocument();
    }

    // Verify safe/redacted/hidden fields counts are showing
    expect(screen.getByText(/safe display fields/i)).toBeInTheDocument();
    expect(screen.getAllByText(/redacted fields/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/hidden fields/i).length).toBeGreaterThan(0);
  });

  it('verifies that no secret credential values are visible', () => {
    render(createElement(App));
    fireEvent.click(document.getElementById('nav-preflight_bundle')!);
    fireEvent.click(screen.getByRole('tab', { name: /room binding matrix/i }));

    // Hidden credential/secret values must not be visible anywhere.
    // Instead we see the display policy count of hidden/redacted fields.
    const rawText = document.body.textContent ?? '';
    expect(rawText).not.toContain('real_secret_token');
    expect(rawText).not.toContain('env_value');
  });

  it('selects a room binding precheck and updates the inspector rail', () => {
    render(createElement(App));
    fireEvent.click(document.getElementById('nav-preflight_bundle')!);
    fireEvent.click(screen.getByRole('tab', { name: /room binding matrix/i }));

    const commandCenterRow = document.getElementById('room-row-command_center')!;
    fireEvent.click(commandCenterRow);

    const rail = document.getElementById('inspector-rail')!;
    expect(within(rail).getByText(/ready_for_read_model_design/i)).toBeInTheDocument();
  });

  it('asserts that future-gate buttons are present and disabled', () => {
    render(createElement(App));
    fireEvent.click(document.getElementById('nav-preflight_bundle')!);
    fireEvent.click(screen.getByRole('tab', { name: /room binding matrix/i }));

    const disabledButtons = screen
      .getAllByRole('button')
      .filter((b) => (b as HTMLButtonElement).disabled);

    expect(disabledButtons.length).toBeGreaterThan(0);

    const labels = disabledButtons.map((b) => b.textContent ?? '');
    expect(labels.some((l) => l.includes('Connect Account'))).toBe(true);
    expect(labels.some((l) => l.includes('Verify Credentials'))).toBe(true);
    expect(labels.some((l) => l.includes('Publish Now'))).toBe(true);
  });
});

describe('Preflight Bundle Source Inventory tab', () => {
  it('lists the 17 precedent dry-run contract references', () => {
    render(createElement(App));
    fireEvent.click(document.getElementById('nav-preflight_bundle')!);
    fireEvent.click(screen.getByRole('tab', { name: /source inventory/i }));

    // Confirm a sample of the 17 source ref IDs are listed
    const sampleSourceRefs = [
      'platform_universe_registry_v2',
      'platform_account_binding_registry_v2_contract',
      'credential_handle_dotenv_secret_boundary_v2_contract',
      'live_read_only_research_approval_packet_schema_contract',
      'live_read_only_research_evidence_packet_dry_run_schema_contract',
      'live_read_only_research_runbook_approval_gate_dry_run_contract',
    ];

    for (const refId of sampleSourceRefs) {
      expect(document.getElementById(`source-row-${refId}`)).toBeInTheDocument();
    }

    // Verify baseline commit and packet hash are rendered
    expect(screen.getByText(/verification signatures/i)).toBeInTheDocument();
    expect(screen.getByText(/acceptance baseline commit/i)).toBeInTheDocument();
    expect(screen.getAllByText(preflightBundlePacket.source_baseline_commit).length).toBeGreaterThan(0);
  });

  it('selects a source reference and updates the inspector rail', () => {
    render(createElement(App));
    fireEvent.click(document.getElementById('nav-preflight_bundle')!);
    fireEvent.click(screen.getByRole('tab', { name: /source inventory/i }));

    const registryRow = document.getElementById('source-row-platform_universe_registry_v2')!;
    fireEvent.click(registryRow);

    const rail = document.getElementById('inspector-rail')!;
    expect(within(rail).getAllByText(/platform_universe_registry_v2/i).length).toBeGreaterThan(0);
    expect(within(rail).getAllByText(/universe_registry/i).length).toBeGreaterThan(0);
    expect(within(rail).getByText(/live_contentops\.platform_universe_registry_v2/i)).toBeInTheDocument();
  });
});
