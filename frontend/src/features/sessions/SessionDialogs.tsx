import { useEffect, useRef, useState, type FormEvent } from "react";
import { api } from "../../api";
import { isAbort } from "../../api/client";
import type { ChatSession } from "../../api/types";
import { useAuth } from "../../auth/AuthProvider";
import { Dialog } from "../../components/ui/Dialog";
import { ErrorFeedback } from "../../components/ui/Feedback";
import { savePending } from "../chat/pending";

function useAction() {
  const [busy, setBusy] = useState(false),
    [error, setError] = useState<unknown>(null);
  const controller = useRef<AbortController | null>(null);
  useEffect(() => () => controller.current?.abort(), []);
  const run = async (action: (signal: AbortSignal) => Promise<void>) => {
    if (busy) return;
    const next = new AbortController();
    controller.current = next;
    setBusy(true);
    setError(null);
    try {
      await action(next.signal);
    } catch (e) {
      if (!isAbort(e) && !next.signal.aborted) setError(e);
    } finally {
      if (!next.signal.aborted) setBusy(false);
    }
  };
  return { busy, error, run };
}

export function RenameSessionDialog({
  session,
  onClose,
  onDone,
}: {
  session: ChatSession;
  onClose: () => void;
  onDone: (session: ChatSession) => void;
}) {
  const [title, setTitle] = useState(session.title);
  const { busy, error, run } = useAction();
  const value = title.trim();
  const valid = value.length > 0 && value.length <= 200 && value !== session.title;
  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (!valid) return;
    void run(async (signal) => {
      const saved = await api.renameSession(session.id, value, signal);
      if (!signal.aborted) onDone(saved);
    });
  };
  return (
    <Dialog title="Đổi tên cuộc trò chuyện" onClose={onClose} busy={busy}>
      <form onSubmit={submit}>
        <label className="field">
          Tên mới
          <input
            value={title}
            maxLength={200}
            autoFocus
            disabled={busy}
            onChange={(e) => setTitle(e.target.value)}
          />
        </label>
        {error !== null && <ErrorFeedback error={error} />}
        <div className="dialog-actions">
          <button type="button" className="button" onClick={onClose} disabled={busy}>
            Hủy
          </button>
          <button className="button button-primary" disabled={busy || !valid}>
            {busy ? "Đang lưu…" : "Lưu"}
          </button>
        </div>
      </form>
    </Dialog>
  );
}

export function DeleteSessionDialog({
  session,
  onClose,
  onDone,
}: {
  session: ChatSession;
  onClose: () => void;
  onDone: (session: ChatSession) => void;
}) {
  const { user } = useAuth();
  const { busy, error, run } = useAction();
  const cancelRef = useRef<HTMLButtonElement>(null);
  const remove = () =>
    void run(async (signal) => {
      await api.deleteSession(session.id, signal);
      if (signal.aborted) return;
      if (user) savePending(user.id, session.id, null);
      onDone(session);
    });
  return (
    <Dialog title="Xóa cuộc trò chuyện?" onClose={onClose} busy={busy} initialFocus={cancelRef}>
      <p className="selected-file">{session.title}</p>
      <ul className="consequences">
        <li>Toàn bộ câu hỏi, câu trả lời và trích dẫn trong cuộc trò chuyện sẽ bị xóa.</li>
        <li>Không thể hoàn tác. Tài liệu nguồn không bị ảnh hưởng.</li>
      </ul>
      {error !== null && <ErrorFeedback error={error} />}
      <div className="dialog-actions">
        <button ref={cancelRef} type="button" className="button" onClick={onClose} disabled={busy}>
          Hủy
        </button>
        <button
          type="button"
          className="button button-destructive"
          onClick={remove}
          disabled={busy}
        >
          {busy ? "Đang xóa…" : "Xóa cuộc trò chuyện"}
        </button>
      </div>
    </Dialog>
  );
}
