import { useEffect, useState, type ReactNode } from "react";
import { NavLink, Link, useLocation } from "react-router-dom";
import { BookOpenCheck, FileText, History, LogOut, Menu, MessageSquare, Plus } from "lucide-react";
import { useAuth } from "../../auth/AuthProvider";
import { useWorkspace } from "../../workspace/WorkspaceProvider";
import { Dialog } from "../ui/Dialog";
import { SourcePanel } from "../../features/sources/SourcePanel";
import { useSessionActions } from "../../features/sessions/SessionActions";

const RECENT_LIMIT = 15;

export function AppShell({ children }: { children: ReactNode }) {
  const { user, signOut } = useAuth();
  const workspace = useWorkspace();
  const location = useLocation();
  const closeSource = workspace.closeSource;
  useEffect(() => {
    closeSource();
  }, [location.pathname, closeSource]);
  const [menu, setMenu] = useState(false),
    [signingOut, setSigningOut] = useState(false);
  const sessionActions = useSessionActions();
  const chat = location.pathname.startsWith("/chat");
  const leave = () => {
    setMenu(false);
    workspace.closeSource();
  };
  const exit = async () => {
    if (signingOut) return;
    setSigningOut(true);
    await signOut();
  };
  const role = user?.role === "knowledge_admin" ? "Quản trị viên" : "Thành viên";
  const navigation = (
    <>
      <nav className="primary-nav" aria-label="Điều hướng chính">
        <NavLink to="/chat" onClick={leave} className={chat ? "active" : ""}>
          <MessageSquare size={18} aria-hidden="true" />
          Hỏi đáp
        </NavLink>
        <NavLink to="/documents" onClick={leave}>
          <FileText size={18} aria-hidden="true" />
          Tài liệu
        </NavLink>
        <NavLink to="/history" onClick={leave}>
          <History size={18} aria-hidden="true" />
          Lịch sử
        </NavLink>
      </nav>
      {chat && (
        <>
          <Link className="button new-chat" to="/chat" onClick={leave}>
            <Plus size={16} aria-hidden="true" />
            Cuộc trò chuyện mới
          </Link>
          <div className="session-list">
            <h2>Gần đây</h2>
            {workspace.sessionsLoading && workspace.sessions.length === 0 && (
              <p className="hint" role="status">
                Đang tải…
              </p>
            )}
            {workspace.sessionError !== null && (
              <div>
                <p className="hint">Chưa tải được danh sách.</p>
                <button className="text-button" onClick={workspace.refreshSessions}>
                  Thử lại
                </button>
              </div>
            )}
            {workspace.sessions.slice(0, RECENT_LIMIT).map((session) => (
              <div className="session-row" key={session.id}>
                <NavLink
                  to={`/chat/${encodeURIComponent(session.id)}`}
                  onClick={leave}
                  title={session.title}
                >
                  {session.title}
                </NavLink>
                {sessionActions.buttons(session)}
              </div>
            ))}
            {!workspace.sessionsLoading &&
              workspace.sessions.length === 0 &&
              workspace.sessionError === null && <p className="hint">Chưa có cuộc trò chuyện.</p>}
            {workspace.sessions.length > RECENT_LIMIT && (
              <Link className="text-button see-all" to="/history" onClick={leave}>
                Xem tất cả trong Lịch sử
              </Link>
            )}
          </div>
        </>
      )}
    </>
  );
  const brand = (
    <Link to="/chat" className="brand" onClick={leave}>
      <span className="brand-mark" aria-hidden="true">
        <BookOpenCheck size={18} />
      </span>
      <span className="brand-text">
        Knowledge Copilot
        <small>Không gian làm việc</small>
      </span>
    </Link>
  );
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        Đến nội dung chính
      </a>
      <header className="mobile-header">
        {brand}
        <button className="button mobile-nav" onClick={() => setMenu(true)}>
          <Menu size={16} aria-hidden="true" />
          Menu
        </button>
      </header>
      <div className={`app-body ${workspace.source ? "has-source" : ""}`}>
        <aside className="sidebar">
          {brand}
          <div className="sidebar-scroll">{navigation}</div>
          <div className="account">
            <span className="avatar" aria-hidden="true">
              {(user?.display_name ?? "?").trim().charAt(0).toUpperCase()}
            </span>
            <span className="account-name">
              {user?.display_name}
              <small>{role}</small>
            </span>
            <button
              className="icon-button"
              aria-label="Đăng xuất"
              title="Đăng xuất"
              onClick={() => void exit()}
              disabled={signingOut}
            >
              <LogOut size={18} aria-hidden="true" />
            </button>
          </div>
        </aside>
        <main id="main-content" className="main-content">
          {children}
        </main>
        {workspace.source && (
          <SourcePanel
            key={`${workspace.source.documentId}:${workspace.source.chunkId ?? "file"}`}
            target={workspace.source}
            onClose={workspace.closeSource}
          />
        )}
      </div>
      {menu && (
        <Dialog title="Menu" onClose={() => setMenu(false)}>
          {navigation}
          <p className="mobile-account">
            {user?.display_name} · {role}
          </p>
          <button
            className="button mobile-signout"
            onClick={() => void exit()}
            disabled={signingOut}
          >
            <LogOut size={16} aria-hidden="true" />
            Đăng xuất
          </button>
        </Dialog>
      )}
      {sessionActions.dialogs}
    </div>
  );
}
