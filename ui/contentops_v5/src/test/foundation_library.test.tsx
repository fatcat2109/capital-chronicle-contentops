import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { ReportEditorialWorkspace } from '../views/ReportEditorialWorkspace';
import type { ReportWorkspaceData } from '../dailyAppTypes';

describe('Foundation library evidence boundaries', () => {
  it('keeps undated foundation and named gaps visible, with no fresh or publication credit', () => {
    const data: ReportWorkspaceData = { schema_version: 'contentops.cc_report_editorial_workspace.v1', state: 'UNAVAILABLE',
      report_events_received: 0, article: null, previews: [], history: [], named_blocker: null, public_write_performed: false,
      foundation_library: { research_revision: 'a', observed_at_utc: '2026-10-19T09:00:00Z',
        counts: { independent_items: 2, useful_families: 2, briefs: 0, fresh_provider_drafts: 0, qualified: 0, published: 0 },
        families: ['METALS', 'FX_RATES'].map(family => ({ family, useful_items: 1, briefs: 0, missing_inputs: ['CURRENT_MARKET_NOT_VERIFIED'] })),
        items: ['METALS', 'FX_RATES'].map(family => ({ item_id: family, family, assets: [family], horizons: ['long'],
          proposition: `Exact ${family} source text`, context_kind: 'UNDATED_FOUNDATION_BACKGROUND', source_url: 'https://www.cftc.gov/',
          source_identity: 'CFTC', rights_state: 'VERIFIED_AUTHORED_TEXT_ONLY', permission_sha256: 'b', source_capture_sha256: 'c',
          originality: 'INDEPENDENT_CONTENTOPS_ACQUISITION', known_at_utc: '2026-10-19T09:00:00Z', published_at_utc: null,
          next_editorial_question: 'What remains missing?' })), briefs: [], gaps: [], next_operation: 'Run bounded retained-source admission' } };
    render(<ReportEditorialWorkspace data={data} />);
    expect(screen.getByRole('heading', { name: 'Thư viện nghiên cứu đa tài sản' })).toBeInTheDocument();
    expect(screen.getByText(/0 fresh-provider drafts · 0 qualified · 0 published/)).toBeInTheDocument();
    expect(screen.getAllByText(/chưa xác minh ngày xuất bản/)).toHaveLength(2);
    fireEvent.change(screen.getByRole('combobox', { name: 'Nhóm chủ đề' }), { target: { value: 'METALS' } });
    expect(screen.getByText('Exact METALS source text')).toBeInTheDocument();
    expect(screen.queryByText('Exact FX_RATES source text')).not.toBeInTheDocument();
    expect(screen.getByText(/CURRENT MARKET NOT VERIFIED/)).toBeInTheDocument();
  });
});
