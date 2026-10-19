import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { EvolvingStoryWorkspace } from '../views/EvolvingStoryWorkspace';
import type { EvolvingStory } from '../dailyAppTypes';

describe('evolving story desk', () => {
  it('separates source delta, unpublished package history and reconciled published memory', () => {
    const story: EvolvingStory = {
      story_identity: 'gas-vintage', update_chain_identity: 'gas-vintage', brief_id: 'gas-vintage', title: 'Gas update', families: ['ENERGY'],
      disposition: 'FOLLOW_UP', reason: 'Cách kiểm chứng đã đổi', reader_question: 'Mùa vụ hay bất ngờ?', follow_up_value: 'So sánh đúng kỳ',
      changed_source_count: 1, brief_changed: true, work_required: true, missing_inputs: ['Kỳ vọng trước công bố'], publication_state: 'UNPUBLISHED_RESEARCH', confirmation_state: 'ATTRIBUTED',
      prior_package: { article_identity: 'old', title: 'Bài nghiên cứu trước', full_text: 'Old exact copy', stage: 'UNPUBLISHED_RESEARCH_PACKAGE' },
      package_history: [{ article_identity: 'old', title: 'Bài nghiên cứu trước', full_text: 'Old exact copy', package_sequence: 1, stage: 'UNPUBLISHED_RESEARCH_PACKAGE' }],
      evidence_delta: [{ item_id: 'gas-source', state: 'CORRECTED', material: true, before: { proposition: 'Previous source', source_url: 'https://eia.gov/old', rights_state: 'PERMITTED' }, after: { proposition: 'Corrected source', source_url: 'https://eia.gov/new', rights_state: 'PERMITTED' } }],
      main_history: [{ report_id: 'asset-report:XNGUSD', report_version: 2, change_kind: 'INVALIDATION', status: 'ADMITTED', known_at_cutoff_utc: '2026-10-19T12:00:00Z', withdrawn: true, changed_claims: [] }],
      canonical_memory_article_count: 7, published_prior: { previous_title: 'Published EIA context', previous_full_text: 'Exact public article', previous_canonical_url: 'https://capitalchronicle.substack.com/p/eia', previous_published_at_utc: '2026-08-12T15:30:00Z' },
    };
    render(<EvolvingStoryWorkspace stories={[story, { ...story, brief_id: 'company', title: 'Company gap', disposition: 'HOLD', reason: 'Issuer rights chưa xác lập' }]} />);
    expect(screen.getByText('Cập nhật có giá trị')).toBeInTheDocument();
    expect(screen.getByText(/1 bản nghiên cứu chưa xuất bản/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Nguồn bản sau' })).toHaveAttribute('href', 'https://eia.gov/new');
    expect(screen.getByText(/trí nhớ chuẩn 7 bài/)).toBeInTheDocument();
    expect(screen.getByText(/các claim bị rút/)).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Câu chuyện'), { target: { value: 'company' } });
    expect(screen.getByText('Chờ phần còn thiếu')).toBeInTheDocument();
    expect(screen.getByText(/Issuer rights chưa xác lập/)).toBeInTheDocument();
  });
});
