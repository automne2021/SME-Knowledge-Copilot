import { Navigate, Outlet, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth/AuthProvider";
import { WorkspaceProvider } from "./workspace/WorkspaceProvider";
import { AppShell } from "./components/layout/AppShell";
import { Loading } from "./components/ui/Feedback";
import LoginPage from "./pages/LoginPage";
import DocumentsPage from "./pages/DocumentsPage";
import ChatPage from "./pages/ChatPage";
function Protected() {
  const { user, loading } = useAuth();
  if (loading)
    return (
      <main className="session-check">
        <Loading label="Đang kiểm tra phiên đăng nhập…" />
      </main>
    );
  if (!user) return <Navigate to="/login" replace />;
  return (
    <WorkspaceProvider key={`${user.id}:${user.workspace_id}:${user.role}`}>
      <AppShell>
        <Outlet />
      </AppShell>
    </WorkspaceProvider>
  );
}
export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<Protected />}>
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/chat/:sessionId" element={<ChatPage />} />
          <Route path="/documents" element={<DocumentsPage />} />
          <Route path="*" element={<Navigate to="/chat" replace />} />
        </Route>
      </Routes>
    </AuthProvider>
  );
}
