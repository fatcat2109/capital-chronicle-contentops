import { fireEvent, render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { ReportEditorialWorkspace } from '../views/ReportEditorialWorkspace';
import type { ReportWorkspaceData } from '../dailyAppTypes';

function data(): ReportWorkspaceData {
  return { schema_version: 'contentops.cc_report_editorial_workspace.v1', state: 'AVAILABLE', report_events_received: 2,
    latest_report: { report_id: 'asset-report:XNGUSD', report_version: 2, change_kind: 'CORRECTION', source_report_sha256: 'a'.repeat(64),
      known_at_cutoff_utc: '2026-10-18T13:03:41Z', claims: [], horizon_blocks: [], missing_claims: [], materiality_rationale: 'Controlled UI correction example.' },
    latest_simple_result: { classification: 'DRAFT_READY', model_execution_state: 'INJECTED_REPLAY_ONLY', draft_count: 1, preview_count: 8 },
    article: { title: 'Controlled canonical draft', dek: 'Controlled test output only.', substack_body_markdown: 'Dated report context. [[SOURCE:SOURCE_1]]' },
    previews: ['telegram', 'discord', 'x', 'linkedin', 'facebook_page', 'instagram_business', 'threads', 'youtube'].map(destination => ({
      destination, preview_id: `preview-${destination}`, article_identity: 'article-control', claim_lineage: [{ report_id: 'asset-report:XNGUSD', report_version: 2 }],
      payload: { text: `${destination}: controlled native text\n\nhttps://capitalchronicle.substack.com/p/pending-publication-abcd` } })),
    history: [{ report_version: 1, state: 'SUPERSEDED', article_identity: 'old-article', preview_ids: ['old-preview'], superseded_by_version: 2 }],
    named_blocker: null, public_write_performed: false };
}

describe('Main report editorial workspace', () => {
  it('shows multi-asset feed coverage, lifecycle and exact headline permission gaps', () => {
    const gas = data();
    gas.report_history = [{ report_id: 'asset-report:XNGUSD', report_version: 1, status: 'ADMITTED', change_kind: 'NEW_REPORT' }];
    const oil = data();
    oil.latest_report = { ...oil.latest_report!, report_id: 'asset-report:USOIL', contract_revision: 'asset-analysis-report-v1.1.0' };
    oil.article = { ...oil.article!, title: 'Oil report controlled article' };
    const combined = { ...gas, workspaces: [gas, oil],
      feed: { producer_commit: 'producer-control', observed_at_utc: '2026-10-18T17:00:00Z', configured_bundle_count: 4, new_events: 4,
        coverage: 'CONFIGURED_IMMUTABLE_EXPORTS_ONLY', events: [{ report_id: 'asset-report:USOIL', report_version: 1, state: 'LINEAGE_ONLY_NOOP' }], gaps: [] },
      headline_export: { source_rows_scanned: 500, eligible_rows: 2, missing_rows: 500, coverage: 'BOUNDED_INCREMENTAL_PREFIXES_NOT_HISTORICAL_COMPLETENESS', observed_at_utc: '2026-10-18T17:00:00Z' } };
    render(<ReportEditorialWorkspace data={combined} />);
    expect(screen.getByText(/500 source rows inspected/)).toHaveTextContent('2 permitted projections');
    expect(screen.getByText(/LINEAGE_ONLY_NOOP/)).toBeInTheDocument();
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'asset-report:USOIL' } });
    expect(screen.getByText('Oil report controlled article')).toBeInTheDocument();
    expect(screen.getByText('asset-analysis-report-v1.1.0')).toBeInTheDocument();
    expect(screen.queryByText('Controlled canonical draft')).not.toBeInTheDocument();
  });
  it('shows canonical copy, eight native previews and lineage with controlled-output label', () => {
    render(<ReportEditorialWorkspace data={data()} />);
    expect(screen.getByText('Controlled canonical draft')).toBeInTheDocument();
    expect(screen.getByText(/no fresh Gemini writer execution/)).toBeInTheDocument();
    for (const destination of ['telegram', 'discord', 'x', 'linkedin', 'facebook page', 'instagram business', 'threads', 'youtube']) {
      expect(screen.getByText(`${destination} · Compiled preview`)).toBeInTheDocument();
    }
    expect(screen.getAllByText(/Canonical link pending/)).toHaveLength(8);
    expect(screen.queryByRole('link', { name: /pending-publication/ })).not.toBeInTheDocument();
    expect(screen.getByText(/old-article/)).toBeInTheDocument();
  });

  it('shows the exact pause blocker and zero created previews without claiming a draft', () => {
    const paused = data(); paused.article = null; paused.previews = []; paused.history = [];
    paused.named_blocker = 'LLM_OPERATOR_PAUSED'; paused.latest_simple_result = { classification: 'DRAFT_BLOCKED', model_execution_state: 'PAUSED_BEFORE_PROVIDER_CALL' };
    render(<ReportEditorialWorkspace data={paused} />);
    expect(screen.getByText('Draft unavailable')).toBeInTheDocument();
    expect(screen.getByRole('status')).toHaveTextContent('LLM_OPERATOR_PAUSED');
    expect(screen.getAllByText(/· Not created/)).toHaveLength(8);
    expect(screen.queryByText('Controlled canonical draft')).not.toBeInTheDocument();
  });

  it('withdraws current copy while retaining historical identities', () => {
    const withdrawn = data(); withdrawn.article = null; withdrawn.previews = []; withdrawn.latest_simple_result = null;
    withdrawn.latest_report = { ...withdrawn.latest_report!, report_version: 3, withdrawal_only: true };
    withdrawn.named_blocker = 'CLAIMS_WITHDRAWN'; withdrawn.history[0].state = 'WITHDRAWN';
    render(<ReportEditorialWorkspace data={withdrawn} />);
    expect(screen.getByText('Claims withdrawn')).toBeInTheDocument();
    expect(screen.getByText(/no replacement article is generated/)).toBeInTheDocument();
    const history = screen.getByText(/old-article/);
    expect(within(history).getByText('WITHDRAWN')).toBeInTheDocument();
    expect(screen.queryByText('Controlled canonical draft')).not.toBeInTheDocument();
  });
});
