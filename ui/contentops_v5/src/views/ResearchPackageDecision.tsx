import { useEffect, useState } from 'react';
import type { ResearchPackage } from '../dailyAppTypes';

const API_ROOT = (import.meta as unknown as { env: Record<string, string | undefined> }).env.VITE_DAILY_APP_API_ROOT || 'http://127.0.0.1:5174';

export function ResearchPackageDecision({ item }: { item: ResearchPackage }) {
  const readOnlyPreview = window.location.protocol === 'file:';
  const [rationale, setRationale] = useState('');
  const [status, setStatus] = useState('');
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(item.review);
  useEffect(() => { setSaved(item.review); setStatus(''); }, [item.package_revision, item.review?.latest_review_id]);
  async function decide(decision: string) {
    setBusy(true); setStatus('Đang lưu vào store hiện có…');
    try {
      const response = await fetch(`${API_ROOT}/api/daily-app/editorial-review`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ brief_id: item.brief_id, package_revision: item.package_revision,
          expected_review_id: saved?.latest_review_id ?? null, decision, rationale }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || `HTTP ${response.status}`);
      setSaved({ ...saved, state: decision, latest_review_id: result.review_id, rationale, history: saved?.history ?? [] });
      setStatus('Đã lưu quyết định biên tập. Không cấp quyền xuất bản hoặc gọi provider.');
    } catch (error) { setStatus(`Chưa lưu: ${error instanceof Error ? error.message : String(error)}. Tải lại desk nếu phiên bản đã đổi.`); }
    finally { setBusy(false); }
  }
  return <section aria-label={`Quyết định ${item.brief_id}`} style={{ overflowWrap: 'anywhere' }}>
    <p><strong>{item.editorial_kind ?? 'BACKGROUND'} · {saved?.state ?? 'UNREVIEWED'}</strong> · {saved?.rationale ?? 'Chưa có quyết định cho phiên bản này.'}</p>
    <p>KEEP giữ dùng cho nghiên cứu; REVISE yêu cầu sửa; HOLD giữ chờ đầu vào. Mọi trạng thái đều chưa phải duyệt xuất bản.</p>
    {readOnlyPreview && <p>Bản xem trước tệp chỉ đọc; lưu quyết định qua Daily App đang kết nối.</p>}
    <details><summary>Nguồn hỗ trợ và bằng chứng giới hạn</summary>
      {item.supporting_claims?.map(c => <article key={c.item_id}><strong>{c.item_id}</strong><p>{c.proposition}</p>
        <p>{c.context_kind} · ngày nguồn {c.published_at_utc ?? 'chưa xác minh'} · biết lúc {c.known_at_utc} · {c.rights_state}</p>
        <a href={c.source_url} target="_blank" rel="noreferrer">Nguồn của claim</a>
        <p style={{ overflowWrap: 'anywhere' }}>Claim {c.text_sha256} · capture {c.source_capture_sha256} · quyền {c.permission_sha256}</p></article>)}
      {item.counterevidence?.map((c, i) => <article key={i}><strong>Giới hạn hoặc phản chứng đối với cách diễn giải quá rộng</strong><p>{c.text}</p><p>{c.editorial_inference}</p>
        <p>Claim: {(c.source_item_ids ?? []).join(', ')}. {c.external_counterevidence_observed ? 'Có đối chứng bên ngoài đã đọc.' : 'Giới hạn từ chính nguồn; không ghi nhận phủ nhận độc lập bên ngoài.'}</p></article>)}
    </details>
    <p>Đầu vào hiện tại còn thiếu: {item.missing_current_inputs?.join('; ')}</p>
    <details><summary>Phiên bản và lịch sử quyết định</summary><p style={{ overflowWrap: 'anywhere' }}>Package {item.package_revision}<br />Bài {item.article_identity}</p>
      {saved?.history?.map(r => <p key={r.review_id}>{r.reviewed_at} · {r.decision} · {r.rationale} · {r.package_revision === item.package_revision ? 'đúng phiên bản gói này' : 'phiên bản cũ, không còn hiệu lực'}</p>)}
    </details>
    <label>Lý do quyết định cho {item.brief_id}<textarea value={rationale} maxLength={3000} onChange={e => setRationale(e.target.value)} rows={3} style={{ width: '100%' }} /></label>
    <div>{['KEEP', 'REVISE', 'HOLD'].map(d => <button type="button" key={d} disabled={readOnlyPreview || busy || !item.source_revision_current || !item.package_revision || rationale.trim().length < 20} onClick={() => void decide(d)}>{d}</button>)}</div>
    {status && <p role="status">{status}</p>}
  </section>;
}
