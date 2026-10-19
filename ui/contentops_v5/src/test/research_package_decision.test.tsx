import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import { ResearchPackageDecision } from '../views/ResearchPackageDecision';
import type { ResearchPackage } from '../dailyAppTypes';

const item: ResearchPackage = { brief_id: 'exact-brief', article_identity: 'article', package_revision: 'revision-A',
  source_revision_current: true, stage: 'EDITOR_AUTHORED_RESEARCH_PACKAGE', article: { title: 'Research', dek: 'Bounded', substack_body_markdown: 'Body' },
  validation: { status: 'PASS', semantic_editorial_review: 'REQUIRED', blockers: [] }, previews: {}, media_assets: [],
  review: { state: 'UNREVIEWED', latest_review_id: null, history: [] } };

afterEach(() => vi.unstubAllGlobals());

it('saves only an exact reasoned decision and never presents a conflict as saved', async () => {
  const fetcher = vi.fn().mockResolvedValueOnce({ ok: true, json: async () => ({ review_id: 'review-1' }) })
    .mockResolvedValueOnce({ ok: false, json: async () => ({ error: 'PACKAGE_REVISION_CONFLICT_REFRESH_DESK' }) });
  vi.stubGlobal('fetch', fetcher);
  render(<ResearchPackageDecision item={item} />);
  expect(screen.getByRole('button', { name: 'KEEP' })).toBeDisabled();
  fireEvent.change(screen.getByRole('textbox'), { target: { value: 'Keep as a dated explainer with its current limits visible.' } });
  fireEvent.click(screen.getByRole('button', { name: 'KEEP' }));
  await screen.findByText(/Đã lưu quyết định biên tập/);
  const payload = JSON.parse(fetcher.mock.calls[0][1].body);
  expect(payload).toMatchObject({ brief_id: 'exact-brief', package_revision: 'revision-A', decision: 'KEEP', expected_review_id: null });
  fireEvent.click(screen.getByRole('button', { name: 'REVISE' }));
  await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Chưa lưu: PACKAGE_REVISION_CONFLICT'));
  expect(JSON.parse(fetcher.mock.calls[1][1].body).expected_review_id).toBe('review-1');
});
