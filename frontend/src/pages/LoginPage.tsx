import { useState, type FormEvent } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";
import { ErrorFeedback, Feedback, Loading } from "../components/ui/Feedback";
import { isAbort } from "../api/client";
import { BookOpenCheck, Quote, SearchX, ShieldCheck } from "lucide-react";
export default function LoginPage() {
  const auth = useAuth();
  const [busy, setBusy] = useState(false),
    [error, setError] = useState<unknown>(null);
  const [username, setUsername] = useState(""),
    [password, setPassword] = useState("");
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
      <section className="login-intro" aria-label="Giới thiệu">
        <div className="brand brand-inverse">
          <span className="brand-mark" aria-hidden="true">
            <BookOpenCheck size={18} />
          </span>
          Knowledge Copilot
        </div>
        <h2>Hỏi đáp tài liệu nội bộ, có nguồn để kiểm tra.</h2>
        <ul>
          <li>
            <Quote size={18} aria-hidden="true" />
            <span>
              <strong>Trích dẫn từ tài liệu gốc</strong>
              Mỗi ý trong câu trả lời gắn với đoạn nguồn, mở ra là thấy đúng trang, đoạn hoặc dòng.
            </span>
          </li>
          <li>
            <SearchX size={18} aria-hidden="true" />
            <span>
              <strong>Biết nói “chưa đủ bằng chứng”</strong>
              Không có thông tin trong tài liệu thì không tự bịa câu trả lời.
            </span>
          </li>
          <li>
            <ShieldCheck size={18} aria-hidden="true" />
            <span>
              <strong>Đúng quyền, đúng phiên bản</strong>
              Chỉ dùng tài liệu đã xử lý xong trong không gian của bạn; tài liệu bị xóa ngừng được
              dùng ngay.
            </span>
          </li>
        </ul>
      </section>
      <section className="login-box">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">
            <BookOpenCheck size={18} />
          </span>
          Knowledge Copilot
        </div>
        <h1>Đăng nhập</h1>
        <p className="muted">Truy cập kiến thức trong không gian làm việc của bạn.</p>
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
          <label className="field">
            Mật khẩu
            <input
              type="password"
              name="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              maxLength={128}
              disabled={busy}
            />
          </label>
          <button className="button button-primary full-width" disabled={busy || auth.loading}>
            {busy ? "Đang đăng nhập…" : "Đăng nhập"}
          </button>
        </form>
        {auth.loading && <Loading label="Đang kiểm tra phiên…" />}
        <p className="hint">Sử dụng tài khoản được quản trị viên cung cấp.</p>
      </section>
    </main>
  );
}
