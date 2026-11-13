import { useState, type FormEvent } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";
import { ErrorFeedback, Feedback, Loading } from "../components/ui/Feedback";
import { isAbort } from "../api/client";
import { BookOpenCheck, Eye, EyeOff } from "lucide-react";
export default function LoginPage() {
  const auth = useAuth();
  const [busy, setBusy] = useState(false),
    [error, setError] = useState<unknown>(null);
  const [username, setUsername] = useState(""),
    [password, setPassword] = useState(""),
    [reveal, setReveal] = useState(false);
  if (auth.user) return <Navigate to="/chat" replace />;
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (busy || !username.trim() || !password) return;
    setBusy(true);
    setError(null);
    try {
      await auth.login(username, password);
      setPassword("");
    } catch (e) {
      if (!isAbort(e)) setError(e);
    } finally {
      setBusy(false);
    }
  };
  return (
    <main className="login-page">
      <section className="login-box">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">
            <BookOpenCheck size={18} />
          </span>
          Knowledge Copilot
        </div>
        <h1>Đăng nhập</h1>
        <p className="muted">Hỏi đáp tài liệu nội bộ, có nguồn để kiểm tra.</p>
        {auth.expired && (
          <Feedback title="Phiên đăng nhập đã hết hạn">
            Vui lòng đăng nhập lại để tiếp tục.
          </Feedback>
        )}
        {auth.error && (
          <Feedback
            title="Chưa xác minh được phiên đăng nhập"
            kind="error"
            action={
              <button className="button" onClick={auth.revalidate}>
                Kiểm tra lại phiên
              </button>
            }
          >
            {auth.error}
          </Feedback>
        )}
        {error !== null && <ErrorFeedback error={error} />}
        <form onSubmit={submit} aria-busy={busy}>
          <label className="field">
            Tên đăng nhập
            <input
              name="username"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              maxLength={64}
              autoCapitalize="none"
              spellCheck={false}
              disabled={busy}
            />
          </label>
          <div className="field">
            <label htmlFor="password">Mật khẩu</label>
            <span className="password-input">
              <input
                id="password"
                type={reveal ? "text" : "password"}
                name="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                maxLength={128}
                disabled={busy}
              />
              <button
                type="button"
                className="icon-button small"
                aria-label={reveal ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
                aria-pressed={reveal}
                onClick={() => setReveal((v) => !v)}
              >
                {reveal ? (
                  <EyeOff size={16} aria-hidden="true" />
                ) : (
                  <Eye size={16} aria-hidden="true" />
                )}
              </button>
            </span>
          </div>
          <button className="button button-primary full-width" disabled={busy || auth.loading}>
            {busy ? "Đang đăng nhập…" : "Đăng nhập"}
          </button>
        </form>
        {auth.loading && <Loading label="Đang kiểm tra phiên…" />}
        <p className="hint">
          Tài khoản do quản trị viên cấp. Quên mật khẩu, hãy liên hệ quản trị viên.
        </p>
      </section>
    </main>
  );
}
