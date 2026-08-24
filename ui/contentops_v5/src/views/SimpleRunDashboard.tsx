import { useEffect, useMemo, useState } from 'react';
import type { CSSProperties } from 'react';
import {
  Activity, AlertTriangle, Check, CheckCircle2, ChevronRight, Clock3, FileCheck2,
  History, Leaf, LoaderCircle, RefreshCw, ShieldCheck, Sparkles, WifiOff, X,
} from 'lucide-react';
import type { DailyAppSnapshot, RuntimeCockpit, RuntimePrimaryState } from '../dailyAppTypes';
import { useDailyAppSnapshot } from './DailyAppConsole';
import './simple-run-dashboard.css';

const BANGKOK_ZONE = 'Asia/Bangkok';

const RUNNING_STATES = new Set<RuntimePrimaryState>([
  'STARTING', 'INGESTING', 'PREPARING', 'RESEARCHING', 'WRITING',
  'MEDIA_BUILDING', 'PACKAGING', 'PUBLISHING', 'READING_BACK', 'RECONCILING',
]);

const STAGE_LABELS: Record<string, string> = {
  HEADLINE_INGESTION: 'Tin mới',
  CANDIDATE_SELECTION: 'Chọn chủ đề',
  CC_CONTEXT: 'Bối cảnh',
  GROUNDED_RESEARCH: 'Kiểm chứng',
  ARTICLE_WRITING: 'Viết bài',
  MEDIA_BUILD: 'Hình ảnh',
  PACKAGE_BUILD: 'Chuẩn bị kênh',
  CANONICAL_DISPATCH: 'Chờ duyệt đăng',
  CANONICAL_READBACK: 'Đối soát',
};

const RESULT_LABELS: Record<string, string> = {
  PASS_PUBLICATION_PLAN_READY: 'Đã chuẩn bị xong',
  COMPLETE: 'Đã hoàn tất',
  NO_NEW_HEADLINE: 'Chưa có tin mới phù hợp',
  NO_QUALIFIED_CANDIDATE: 'Chưa có chủ đề đủ điều kiện',
  EVIDENCE_BLOCKED: 'Đang chờ thêm nguồn tin',
  NO_PUBLICATION: 'Không tạo bài cho lượt này',
};

const DAY_LABELS: Record<string, string> = {
  DEFICIT_RECOVERABLE: 'còn cơ hội trong ngày',
  ON_TRACK: 'đúng tiến độ',
  TARGET_MET: 'đã đạt mục tiêu',
  DEGRADED_DAILY_OUTPUT_DEFICIT: 'chưa đạt tiến độ',
};

const WINDOWS = [
  { time: '17:00', label: 'London', minute: 17 * 60 },
  { time: '21:00', label: 'New York', minute: 21 * 60 },
  { time: '23:00', label: 'New York', minute: 23 * 60 },
  { time: '01:00', label: 'Ngày mai', minute: 25 * 60 },
];

function bangkokParts(date: Date) {
  const parts = new Intl.DateTimeFormat('en-GB', {
    timeZone: BANGKOK_ZONE, hour: '2-digit', minute: '2-digit', second: '2-digit',
    hourCycle: 'h23', weekday: 'short', day: '2-digit', month: 'short',
  }).formatToParts(date);
  return Object.fromEntries(parts.map(part => [part.type, part.value]));
}

function bangkokClock(date: Date) {
  const p = bangkokParts(date);
  return `${p.hour}:${p.minute}:${p.second}`;
}

function bangkokDate(date: Date) {
  const p = bangkokParts(date);
  return `${p.weekday}, ${p.day} ${p.month}`;
}

function timeUntil(value: string | null | undefined, now: Date) {
  if (!value) return 'Chưa có lịch';
  const target = new Date(value);
  const minutes = Math.max(0, Math.round((target.getTime() - now.getTime()) / 60_000));
  if (minutes < 1) return 'Sắp bắt đầu';
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return hours ? `${hours}g ${rest}p nữa` : `${rest} phút nữa`;
}

function simpleStatus(cockpit: RuntimeCockpit | undefined, snapshot: DailyAppSnapshot, actionableCount: number) {
  const state = cockpit?.primary_state;
  if (state && RUNNING_STATES.has(state)) {
    return { tone: 'running', eyebrow: 'ĐANG CHẠY', title: 'Hệ thống đang làm việc', detail: cockpit?.current_activity?.story_label || 'Đang xử lý cơ hội mới', icon: Activity };
  }
  if (state === 'ACTION_REQUIRED' || state === 'DEGRADED' || actionableCount > 0) {
    return { tone: 'attention', eyebrow: 'CẦN XEM', title: 'Có việc cần chú ý', detail: 'Bấm vào đây để xem việc cần làm', icon: AlertTriangle };
  }
  if (state === 'STOPPED' || snapshot.runtime.kill_switch_active) {
    return { tone: 'stopped', eyebrow: 'ĐANG DỪNG', title: 'Hệ thống chưa chạy', detail: 'Không có hoạt động mới', icon: WifiOff };
  }
  return { tone: 'ready', eyebrow: 'SẴN SÀNG', title: 'Hệ thống đang chờ lịch', detail: 'Mọi thứ bình thường', icon: Leaf };
}

type FriendlyIncident = {
  key: string;
  title: string;
  detail: string;
  action: string;
  tone: 'attention' | 'resolved';
  count: number;
};

function isActionableIncident(item: Record<string, unknown>) {
  return String(item.severity || '').toUpperCase() !== 'RECOVERY_AUDIT';
}

function friendlyIncident(item: Record<string, unknown>): Omit<FriendlyIncident, 'count'> {
  const text = `${String(item.what_happened || '')} ${String(item.operator_action || '')}`.toLowerCase();
  const resolved = !isActionableIncident(item);
  if (resolved && text.includes('stale derivative expired')) return {
    key: 'resolved-expired', title: 'Nội dung cũ đã được đóng an toàn',
    detail: 'Không có bài đăng mới và lịch sử đối soát vẫn được giữ lại.',
    action: 'Không cần làm gì.', tone: 'resolved',
  };
  if (resolved && text.includes('transport-correction')) return {
    key: 'resolved-transport', title: 'Một lượt phân phối đã được đối soát',
    detail: 'Hệ thống đã giữ đúng danh tính của lượt gửi.',
    action: 'Không cần làm gì.', tone: 'resolved',
  };
  if (resolved && text.includes('absence-safe')) return {
    key: 'resolved-retry', title: 'Một lượt gửi lại đã được xác nhận',
    detail: 'Lượt xử lý bổ sung đã kết thúc an toàn.',
    action: 'Không cần làm gì.', tone: 'resolved',
  };
  if (/reauth|login|sign-in|auth_invalid/.test(text)) return {
    key: 'login', title: 'Một kênh cần đăng nhập lại',
    detail: 'Kênh này đang được giữ an toàn và chưa nhận nội dung mới.',
    action: 'Đăng nhập lại đúng tài khoản được nhắc đến.', tone: 'attention',
  };
  if (/identity|wrong account/.test(text)) return {
    key: 'identity', title: 'Cần kiểm tra đúng tài khoản',
    detail: 'Hệ thống đã dừng trước khi thực hiện hành động.',
    action: 'Xác nhận đúng tài khoản rồi làm mới dashboard.', tone: 'attention',
  };
  if (/heartbeat|supervisor|controller.*offline/.test(text)) return {
    key: 'runtime', title: 'Hệ thống theo dõi chưa phản hồi',
    detail: 'Dữ liệu vẫn được giữ nguyên và không có hành động công khai.',
    action: 'Chờ một phút rồi bấm Làm mới.', tone: 'attention',
  };
  if (/unknown_write|unknown write|pending.*reconcil|retry/.test(text)) return {
    key: 'pending-truth', title: 'Một kết quả vẫn đang được xác nhận',
    detail: 'Hệ thống đã dừng gửi lại để tránh thao tác trùng.',
    action: 'Không thử lại. Chờ hệ thống hoàn tất đối soát.', tone: 'attention',
  };
  if (/permission|scope/.test(text)) return {
    key: 'permission', title: 'Một kênh chưa đủ quyền',
    detail: 'Kênh này đã được tách khỏi lượt xử lý mới.',
    action: 'Kiểm tra quyền truy cập của kênh.', tone: 'attention',
  };
  return resolved ? {
    key: 'resolved-other', title: 'Một mục đã được xử lý an toàn',
    detail: 'Lịch sử được giữ lại để tiện kiểm tra sau này.',
    action: 'Không cần làm gì.', tone: 'resolved',
  } : {
    key: 'attention-other', title: 'Có một trạng thái cần kiểm tra',
    detail: 'Hệ thống đang giữ an toàn và chưa thực hiện hành động mới.',
    action: 'Bấm Làm mới sau một phút. Nếu vẫn còn, liên hệ người vận hành.', tone: 'attention',
  };
}

function groupIncidents(items: Array<Record<string, unknown>>) {
  const grouped = new Map<string, FriendlyIncident>();
  for (const item of items) {
    const friendly = friendlyIncident(item);
    const current = grouped.get(friendly.key);
    if (current) current.count += 1;
    else grouped.set(friendly.key, { ...friendly, count: 1 });
  }
  return Array.from(grouped.values());
}

function opportunityState(index: number, now: Date, running: boolean, nextWake: string | null | undefined) {
  const p = bangkokParts(now);
  let currentMinute = Number(p.hour) * 60 + Number(p.minute);
  if (currentMinute < 3 * 60) currentMinute += 24 * 60;
  const target = WINDOWS[index].minute;
  const nextHour = nextWake ? Number(bangkokParts(new Date(nextWake)).hour) : -1;
  const isNext = nextHour === Number(WINDOWS[index].time.slice(0, 2));
  if (running && isNext) return 'running';
  if (isNext) return 'next';
  if (currentMinute > target) return 'past';
  return 'future';
}

function lastResult(cockpit?: RuntimeCockpit) {
  const last = cockpit?.last_completed_editorial;
  if (!last) return { title: 'Chưa có run hoàn tất', detail: 'Kết quả đầu tiên sẽ xuất hiện ở đây', tone: 'neutral' };
  const rawResult = String(last.result || 'COMPLETE');
  const result = RESULT_LABELS[rawResult] ?? 'Đã kết thúc lượt chạy';
  return {
    title: last.story_label || 'Run gần nhất',
    detail: result,
    tone: /PASS|READY|QUALIFIED|COMPLETE/i.test(rawResult) ? 'good' : /BLOCK|FAIL|DEGRADED/i.test(rawResult) ? 'warn' : 'neutral',
  };
}

export function SimpleRunDashboard() {
  const [load, refresh] = useDailyAppSnapshot();
  const [now, setNow] = useState(() => new Date());
  const [incidentPanel, setIncidentPanel] = useState<'attention' | 'history' | null>(null);
  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), 1_000);
    return () => window.clearInterval(timer);
  }, []);
  useEffect(() => {
    const previous = document.title;
    document.title = 'ContentOps · Run Monitor';
    return () => { document.title = previous; };
  }, []);
  useEffect(() => {
    if (!incidentPanel) return;
    const close = (event: KeyboardEvent) => { if (event.key === 'Escape') setIncidentPanel(null); };
    window.addEventListener('keydown', close);
    return () => window.removeEventListener('keydown', close);
  }, [incidentPanel]);

  const snapshot = load.snapshot;
  const cockpit = snapshot?.runtime.operator_cockpit;
  const actionableIncidents = useMemo(
    () => (snapshot?.incidents.items ?? []).filter(isActionableIncident),
    [snapshot?.incidents.items],
  );
  const resolvedIncidents = useMemo(
    () => (snapshot?.incidents.items ?? []).filter(item => !isActionableIncident(item)),
    [snapshot?.incidents.items],
  );
  const status = snapshot ? simpleStatus(cockpit, snapshot, actionableIncidents.length) : null;
  const running = Boolean(cockpit?.primary_state && RUNNING_STATES.has(cockpit.primary_state));
  const result = snapshot ? lastResult(cockpit) : null;
  const qualified = snapshot?.today.qualified_articles_today ?? 0;
  const target = snapshot?.today.build_qualified_floor ?? 4;
  const progress = Math.min(100, Math.round((qualified / Math.max(1, target)) * 100));
  const nextWake = cockpit?.schedule.next_editorial_wake_utc ?? snapshot?.runtime.next_wake_utc;
  const visibleStages = useMemo(
    () => (cockpit?.timeline ?? []).filter(step => step.stage !== 'CANONICAL_DISPATCH' || step.state !== 'pending'),
    [cockpit?.timeline],
  );

  if (!snapshot) {
    return <main className="simple-run simple-run--offline">
      <section className="simple-offline-card">
        {load.kind === 'loading' ? <LoaderCircle className="simple-spin" /> : <WifiOff />}
        <h1>{load.kind === 'loading' ? 'Đang kết nối…' : 'Dashboard chưa sẵn sàng'}</h1>
        <p>{load.kind === 'loading' ? 'Chỉ mất vài giây' : 'Hãy mở lại shortcut sau một phút'}</p>
        {load.kind === 'offline' && <button type="button" onClick={() => void refresh()}><RefreshCw /> Thử lại</button>}
      </section>
    </main>;
  }

  const StatusIcon = status!.icon;
  const publicSafe = cockpit?.safety.active_public_write !== true && (
    cockpit?.safety.new_public_writes_blocked === true || snapshot.runtime.operating_mode !== 'AUTONOMOUS_DEFAULT'
  );
  const noUnknown = (cockpit?.safety.unknown_write_count ?? snapshot.published.unknown_write_count) === 0;
  const noDuplicateSignal = snapshot.incidents.items.every(item => !/duplicate|race/i.test(String(item.what_happened)));

  return <main className="simple-run" aria-live="polite">
    <div className="simple-run__glow simple-run__glow--one" />
    <div className="simple-run__glow simple-run__glow--two" />
    <header className="simple-header">
      <div className="simple-brand"><span>CC</span><div><strong>Run Monitor</strong><small>ContentOps V1</small></div></div>
      <div className="simple-clock"><strong>{bangkokClock(now)}</strong><small>{bangkokDate(now)} · Bangkok</small></div>
      <button type="button" className="simple-refresh" onClick={() => void refresh()} aria-label="Làm mới"><RefreshCw /></button>
    </header>

    {load.kind === 'offline' && <div className="simple-stale"><WifiOff /> Mất kết nối · đang hiển thị dữ liệu gần nhất</div>}

    <button type="button" className={`simple-hero is-${status!.tone} ${actionableIncidents.length ? 'is-clickable' : ''}`} disabled={!actionableIncidents.length} onClick={() => setIncidentPanel('attention')}>
      <div className="simple-hero__icon"><StatusIcon /></div>
      <div className="simple-hero__copy"><span>{status!.eyebrow}</span><h1>{status!.title}</h1><p>{status!.detail}</p>{actionableIncidents.length > 0 && <em>Xem chi tiết <ChevronRight /></em>}</div>
      <div className="simple-next"><small>Lần chạy tiếp theo</small><strong>{timeUntil(nextWake, now)}</strong><span>{nextWake ? new Intl.DateTimeFormat('vi-VN', { timeZone: BANGKOK_ZONE, hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).format(new Date(nextWake)) : '—'}</span></div>
    </button>

    <section className="simple-schedule" aria-label="Lịch chạy hôm nay">
      <div className="simple-section-title"><Clock3 /><span>Lịch hôm nay</span></div>
      <div className="simple-schedule__line">
        {WINDOWS.map((window, index) => {
          const state = opportunityState(index, now, running, nextWake);
          return <article key={window.time} className={`simple-slot is-${state}`}>
            <div className="simple-slot__dot">{state === 'running' ? <LoaderCircle className="simple-spin" /> : null}</div>
            <strong>{window.time}</strong><small>{window.label}</small>
            <em>{state === 'running' ? 'Đang chạy' : state === 'next' ? 'Tiếp theo' : state === 'past' ? 'Đã qua' : 'Sắp tới'}</em>
          </article>;
        })}
      </div>
    </section>

    <section className="simple-grid">
      <article className="simple-card simple-progress-card">
        <div className="simple-section-title"><Sparkles /><span>Hôm nay</span></div>
        <div className="simple-progress-row">
          <div className="simple-ring" style={{ '--progress': `${progress * 3.6}deg` } as CSSProperties}>
            <div><strong>{qualified}</strong><small>/ {target}</small></div>
          </div>
          <div className="simple-progress-copy"><strong>{snapshot.runtime.rolling_24h_unique_headlines ?? 0}</strong><span>tin đang theo dõi</span><small>{DAY_LABELS[snapshot.today.production_day_state ?? ''] || 'đang cập nhật'}</small></div>
        </div>
      </article>

      <article className={`simple-card simple-result-card is-${result!.tone}`}>
        <div className="simple-section-title"><FileCheck2 /><span>Kết quả gần nhất</span></div>
        <div className="simple-result-icon"><CheckCircle2 /></div>
        <h2>{result!.title}</h2><p>{result!.detail}</p>
      </article>

      <article className="simple-card simple-safety-card">
        <div className="simple-section-title"><ShieldCheck /><span>An toàn</span></div>
        <div className="simple-safety-list">
          <div className={publicSafe ? 'is-good' : 'is-warn'}><span>{publicSafe ? <Check /> : <AlertTriangle />}</span><strong>Không đăng công khai</strong></div>
          <div className={noDuplicateSignal ? 'is-good' : 'is-warn'}><span>{noDuplicateSignal ? <Check /> : <AlertTriangle />}</span><strong>Không chạy lặp</strong></div>
          <div className={noUnknown ? 'is-good' : 'is-warn'}><span>{noUnknown ? <Check /> : <AlertTriangle />}</span><strong>Mọi trạng thái rõ ràng</strong></div>
        </div>
      </article>
    </section>

    {running && visibleStages.length > 0 && <section className="simple-live-flow">
      <div className="simple-section-title"><Activity /><span>Tiến độ hiện tại</span></div>
      <div className="simple-stage-row">{visibleStages.map(step => <div key={step.stage} className={`simple-stage is-${step.state}`}><span>{step.state === 'completed' ? <Check /> : step.state === 'current' ? <LoaderCircle className="simple-spin" /> : null}</span><small>{STAGE_LABELS[step.stage] ?? step.label}</small></div>)}</div>
    </section>}

    {actionableIncidents.length > 0 && <button type="button" className="simple-alert" onClick={() => setIncidentPanel('attention')}><AlertTriangle /><div><strong>Cần chú ý</strong><span>{actionableIncidents.length} việc cần xem</span></div><ChevronRight /></button>}
    {actionableIncidents.length === 0 && resolvedIncidents.length > 0 && <button type="button" className="simple-alert simple-alert--history" onClick={() => setIncidentPanel('history')}><History /><div><strong>Đã xử lý an toàn</strong><span>{resolvedIncidents.length} mục trong lịch sử</span></div><ChevronRight /></button>}

    <footer><span><i /> Tự làm mới mỗi 3 giây</span><small>Chỉ theo dõi · không đăng</small></footer>

    {incidentPanel && <div className="simple-dialog-backdrop" onMouseDown={() => setIncidentPanel(null)}>
      <section className="simple-dialog" role="dialog" aria-modal="true" aria-labelledby="simple-dialog-title" onMouseDown={event => event.stopPropagation()}>
        <header><div><span>{incidentPanel === 'attention' ? 'VIỆC CẦN LÀM' : 'LỊCH SỬ'}</span><h2 id="simple-dialog-title">{incidentPanel === 'attention' ? 'Cần chú ý' : 'Đã xử lý an toàn'}</h2><p>{incidentPanel === 'attention' ? 'Làm theo từng bước bên dưới.' : 'Các mục này chỉ để tham khảo. Bạn không cần làm gì.'}</p></div><button type="button" onClick={() => setIncidentPanel(null)} aria-label="Đóng"><X /></button></header>
        <div className="simple-dialog__list">{groupIncidents(incidentPanel === 'attention' ? actionableIncidents : resolvedIncidents).map(item => <article key={item.key} className={`is-${item.tone}`}>
          <div className="simple-dialog__status">{item.tone === 'resolved' ? <CheckCircle2 /> : <AlertTriangle />}</div>
          <div><h3>{item.title}{item.count > 1 && <small>× {item.count}</small>}</h3><p>{item.detail}</p><strong>{item.action}</strong></div>
        </article>)}</div>
        <button type="button" className="simple-dialog__done" onClick={() => setIncidentPanel(null)}>Đã hiểu</button>
      </section>
    </div>}
  </main>;
}
