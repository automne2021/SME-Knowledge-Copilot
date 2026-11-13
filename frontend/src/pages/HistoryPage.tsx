import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { MessageSquare, Search } from "lucide-react";
import type { ChatSession } from "../api/types";
import { useWorkspace } from "../workspace/WorkspaceProvider";
import { ErrorFeedback, Feedback, Loading } from "../components/ui/Feedback";
import { useSessionActions } from "../features/sessions/SessionActions";
import { formatDate } from "../lib/format";

const DAY = 24 * 60 * 60 * 1000;

/** Group by calendar day in Asia/Ho_Chi_Minh, matching how dates are shown elsewhere. */
export function groupSessions(sessions: ChatSession[], now = Date.now()) {
  const day = (value: number) =>
    new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Ho_Chi_Minh" }).format(new Date(value));
  const today = day(now),
    weekAgo = now - 7 * DAY;
  const groups: { label: string; items: ChatSession[] }[] = [
    { label: "Hôm nay", items: [] },
    { label: "7 ngày qua", items: [] },
    { label: "Cũ hơn", items: [] },
  ];
  for (const session of sessions) {
    const created = new Date(session.created_at).getTime();
    groups[day(created) === today ? 0 : created >= weekAgo ? 1 : 2].items.push(session);
  }
  return groups.filter((group) => group.items.length > 0);
}

export default function HistoryPage() {
  const workspace = useWorkspace();
  const [query, setQuery] = useState(""),
    [notice, setNotice] = useState("");
  const actions = useSessionActions(setNotice);
  const groups = useMemo(() => {
    const needle = query.trim().toLocaleLowerCase("vi");
    return groupSessions(
      needle
        ? workspace.sessions.filter((s) => s.title.toLocaleLowerCase("vi").includes(needle))
        : workspace.sessions,
    );
  }, [workspace.sessions, query]);
  return (
    <section className="page history-page">
      <div className="page-heading">
        <div>
          <h1>Lịch sử hội thoại</h1>
          <p className="muted">Chỉ bạn xem được các cuộc trò chuyện của mình.</p>
        </div>
        <label className="search-field">
          <Search size={16} aria-hidden="true" />
          <span className="sr-only">Tìm cuộc trò chuyện</span>
          <input
            type="search"
            placeholder="Tìm theo tên cuộc trò chuyện"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </label>
      </div>
      {notice && <Feedback title={notice} />}
      {workspace.sessionsLoading && workspace.sessions.length === 0 ? (
        <Loading label="Đang tải lịch sử…" />
      ) : workspace.sessionError !== null ? (
        <ErrorFeedback error={workspace.sessionError} retry={workspace.refreshSessions} />
      ) : workspace.sessions.length === 0 ? (
        <div className="empty-state">
          <h2>Chưa có cuộc trò chuyện</h2>
          <p>Các câu hỏi bạn đặt sẽ được lưu ở đây.</p>
          <Link className="button" to="/chat">
            Bắt đầu hỏi đáp
          </Link>
        </div>
      ) : groups.length === 0 ? (
        <p className="hint">Không có cuộc trò chuyện nào khớp “{query.trim()}”.</p>
      ) : (
        groups.map((group) => (
          <section className="history-group" key={group.label} aria-label={group.label}>
            <h2>{group.label}</h2>
            <ul className="history-list">
              {group.items.map((session) => (
                <li key={session.id}>
                  <MessageSquare size={16} aria-hidden="true" className="history-icon" />
                  <Link to={`/chat/${encodeURIComponent(session.id)}`} className="history-title">
                    {session.title}
                  </Link>
                  <time dateTime={session.created_at}>{formatDate(session.created_at)}</time>
                  {actions.buttons(session)}
                </li>
              ))}
            </ul>
          </section>
        ))
      )}
      {workspace.sessions.length === 100 && (
        <p className="hint">Đang hiển thị 100 cuộc trò chuyện gần nhất.</p>
      )}
      {actions.dialogs}
    </section>
  );
}
