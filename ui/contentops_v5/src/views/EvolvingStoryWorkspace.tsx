import { useState } from 'react';
import type { EvolvingStory } from '../dailyAppTypes';

const labels: Record<string, string> = { NEW: 'Câu chuyện mới', FOLLOW_UP: 'Cập nhật có giá trị', NO_MATERIAL_CHANGE: 'Giữ bản hiện tại', HOLD: 'Chờ phần còn thiếu', ADDED: 'Bổ sung', REMOVED: 'Rút khỏi brief', CORRECTED: 'Đã sửa', UNCHANGED: 'Không đổi' };

export function EvolvingStoryWorkspace({ stories }: { stories: EvolvingStory[] }) {
  const [selected, select] = useState('gas-vintage');
  const story = stories.find(s => s.brief_id === selected) ?? stories[0];
  if (!story) return null;
  return <section aria-label="Theo dõi câu chuyện" className="report-copy" style={{ overflowWrap: 'anywhere', minWidth: 0 }}>
    <h3>Theo dõi câu chuyện</h3>
    <label>Câu chuyện <select value={story.brief_id} onChange={e => select(e.target.value)} style={{ maxWidth: '100%' }}>
      {stories.map(s => <option key={s.brief_id} value={s.brief_id}>{s.title}</option>)}
    </select></label>
    <h4>{story.title}</h4>
    <p role="status"><strong>{labels[story.disposition] ?? story.disposition}</strong> · {story.reason}</p>
    <p>Câu hỏi của độc giả: {story.reader_question}</p>
    <p>Giá trị của bản này: {story.follow_up_value}</p>
    <p>{story.work_required ? 'Có việc cần xử lý cho đúng phiên bản này.' : 'Không cần tạo lại bài hoặc media trong lần quét giống hệt.'} Quyết định: {story.current_review?.state ?? 'chưa đọc duyệt'}.</p>
    <details><summary>Bài trước đã nói gì? · {story.package_history.length} bản nghiên cứu chưa xuất bản</summary>
      {story.prior_package ? <><h4>{story.prior_package.title}</h4><div className="report-body">{story.prior_package.full_text.replace(/\[\[SOURCE:(SOURCE_\d+)\]\]/g, '[$1]')}</div><p>Mã bài: {story.prior_package.article_identity}</p></> : <p>Chưa có bản trước khác nội dung trong lịch sử đã giữ.</p>}
      {story.package_history.map(p => <details key={p.article_identity}><summary>Bản {p.package_sequence}: {p.title} · chưa xuất bản</summary><div className="report-body">{p.full_text?.replace(/\[\[SOURCE:(SOURCE_\d+)\]\]/g, '[$1]')}</div></details>)}
    </details>
    <details open><summary>Bằng chứng trước → sau · {story.changed_source_count} luận điểm đổi</summary>
      {!story.evidence_delta.length && <p>Không có bản trước phù hợp để so sánh nguồn.</p>}
      {story.evidence_delta.map(d => <article key={d.item_id} className="report-evidence">
        <strong>{labels[d.state] ?? d.state} · {d.item_id}</strong>
        {d.before && <p>Trước: {d.before.proposition} <a href={d.before.source_url} target="_blank" rel="noreferrer">Nguồn bản trước</a></p>}
        {d.after && <p>Sau: {d.after.proposition} <a href={d.after.source_url} target="_blank" rel="noreferrer">Nguồn bản sau</a> · {d.after.rights_state}</p>}
      </article>)}
      {story.brief_changed && <p>Brief cũng đã thay đổi cách giải thích hoặc câu hỏi; dữ kiện không đổi vẫn giữ nguyên.</p>}
    </details>
    {!!story.main_history.length && <details><summary>Lịch sử Main · phân tích quay về, không tính là xác nhận độc lập</summary>
      {story.main_history.map(h => <article className="report-evidence" key={`${h.report_id}-${h.report_version}`}>
        <h4>{h.report_id} · v{h.report_version} · {h.change_kind}</h4><p>{h.status} · biết tại {h.known_at_cutoff_utc}{h.withdrawn ? ' · các claim bị rút' : ''}</p>
        {!h.changed_claims.length && <p>Bản này chỉ giữ dòng lịch sử hoặc không đổi claim công khai.</p>}
        {h.changed_claims.map(c => <details key={c.claim_id}><summary>{c.claim_id}</summary>
          <p>Trước: {c.before?.text ?? 'Chưa có claim công khai'} · {c.before?.producer_layer}</p>
          <p>Sau: {c.after?.text ?? 'Claim đã rút'} · {c.after?.producer_layer}</p>
        </details>)}
      </article>)}
    </details>}
    <details><summary>Bài đã xuất bản có liên quan · trí nhớ chuẩn {story.canonical_memory_article_count ?? 'chưa đọc'} bài</summary>
      {story.published_prior ? <><a href={story.published_prior.previous_canonical_url} target="_blank" rel="noreferrer">{story.published_prior.previous_title}</a><p>{story.published_prior.previous_published_at_utc}</p><div className="report-body">{story.published_prior.previous_full_text}</div></> : <p>Chưa xác lập bài đã xuất bản có liên quan. Các bản nghiên cứu ở trên không được tính vào lịch sử xuất bản.</p>}
    </details>
    <p>Còn thiếu: {story.missing_inputs.join('; ') || 'Không ghi nhận khoảng trống cho phạm vi hẹp của brief.'}</p>
    <details><summary>Mức xác nhận của từng luận điểm</summary>{story.epistemic_states?.map(s => <p key={s.item_id}>{s.item_id}: {s.state} · {s.context_kind}. Chỉ xác nhận lời nguồn đã giữ, không xác nhận tác động thị trường.</p>)}</details>
    <p>Dữ kiện là lời nguồn được giữ; phân tích và kịch bản phải đọc theo điều kiện. Việc duyệt nghiên cứu không tự xuất bản.</p>
  </section>;
}
