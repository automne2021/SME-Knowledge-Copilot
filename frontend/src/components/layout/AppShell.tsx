import { useEffect, useState, type ReactNode } from "react";
import { NavLink, Link, useLocation } from "react-router-dom";
import { BookOpenCheck, FileText, LogOut, Menu, MessageSquare, Plus } from "lucide-react";
import { useAuth } from "../../auth/AuthProvider";
import { useWorkspace } from "../../workspace/WorkspaceProvider";
import { Dialog } from "../ui/Dialog";
import { SourcePanel } from "../../features/sources/SourcePanel";
export function AppShell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const workspace = useWorkspace();
  const location = useLocation();
  const closeSource = workspace.closeSource;
  useEffect(() => {
    closeSource();
  }, [location.pathname, closeSource]);
  const [menu, setMenu] = useState(false);
  const chat = location.pathname.startsWith("/chat");
  const navigation = (
    <>
      <nav className="primary-nav" aria-label="Điều hướng chính">
        <NavLink
          to="/chat"
          onClick={() => {
            setMenu(false);
            workspace.closeSource();
          }}
          className={chat ? "active" : ""}
        >
          <MessageSquare size={18} aria-hidden="true" />
          Hỏi đáp
        </NavLink>
        <NavLink
          to="/documents"
          onClick={() => {
            setMenu(false);
            workspace.closeSource();
          }}
        >
          <FileText size={18} aria-hidden="true" />
          Tài liệu
        </NavLink>
      </nav>
      {chat && (
        <>
          <Link
            className="button button-primary new-chat"
            to="/chat"
            onClick={() => {
              setMenu(false);
              workspace.closeSource();
            }}
          >
            <Plus size={16} aria-hidden="true" />
            Cuộc trò chuyện mới
          </Link>
          <div className="session-list">
            <h2>Phiên gần đây</h2>
            {workspace.sessionsLoading && (
              <p className="hint" role="status">
                Đang tải phiên…
              </p>
            )}
            {workspace.sessionError !== null && (
              <div>
                <p className="hint">Chưa tải được danh sách phiên.</p>
                <button className="text-button" onClick={workspace.refreshSessions}>
                  Thử lại
                </button>
              </div>
            )}
            {workspace.sessions.map((session) => (
              <NavLink
                key={session.id}
                to={`/chat/${encodeURIComponent(session.id)}`}
                onClick={() => {
                  setMenu(false);
                  workspace.closeSource();
                }}
                title={session.title}
              >
                <span>{session.title}</span>
              </NavLink>
            ))}
            {!workspace.sessionsLoading &&
              workspace.sessions.length === 0 &&
              workspace.sessionError === null && <p className="hint">Chưa có cuộc trò chuyện.</p>}
            {workspace.sessions.length === 100 && (
              <p className="hint">Hiển thị 100 phiên gần nhất.</p>
            )}
          </div>
        </>
      )}
    </>
  );
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        Đến nội dung chính
      </a>
      <header className="app-header">
        <Link to="/chat" className="brand">
          <span className="brand-mark" aria-hidden="true">
            <BookOpenCheck size={18} />
          </span>
          Knowledge Copilot
        </Link>
        <span className="workspace-label">Không gian làm việc</span>
        <button className="button mobile-nav" onClick={() => setMenu(true)}>
          <Menu size={16} aria-hidden="true" />
          Điều hướng
        </button>
        <div className="account">
          <span className="avatar" aria-hidden="true">
            {(user?.display_name ?? "?").trim().charAt(0).toUpperCase()}
          </span>
          <span className="account-name">
            {user?.display_name}
            <small>{user?.role === "knowledge_admin" ? "Quản trị tri thức" : "Thành viên"}</small>
          </span>
          <button className="button button-ghost" onClick={logout}>
            <LogOut size={16} aria-hidden="true" />
            Đăng xuất
          </button>
        </div>
      </header>
      <div className={`app-body ${workspace.source ? "has-source" : ""}`}>
        <aside className="sidebar">{navigation}</aside>
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
        <Dialog title="Điều hướng" onClose={() => setMenu(false)}>
          {navigation}
          <button className="text-button mobile-signout" onClick={logout}>
            Đăng xuất
          </button>
        </Dialog>
      )}
    </div>
  );
}
