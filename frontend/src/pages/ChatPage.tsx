import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import { isAbort } from "../api/client";
import type { Citation, KnowledgeDocument } from "../api/types";
import { useAuth } from "../auth/AuthProvider";
import { DOCUMENT_CHANGED } from "../auth/session";
import { useWorkspace } from "../workspace/WorkspaceProvider";
import { ErrorFeedback, Feedback, Loading } from "../components/ui/Feedback";
import { AnswerView } from "../features/chat/AnswerView";
import { useChat } from "../features/chat/useChat";
import { savePending } from "../features/chat/pending";
import { SOURCE_UNAVAILABLE } from "../features/sources/SourcePanel";
import { SUGGESTED_QUESTIONS } from "../features/chat/suggestions";
import { ArrowUp, BookOpenCheck, Clock, Files, Funnel, LoaderCircle, X } from "lucide-react";
import { clock, useElapsed } from "../hooks/useElapsed";
export default function ChatPage() {
  const { sessionId } = useParams();
  return <Conversation key={sessionId ?? "new"} sessionId={sessionId} />;
}
function Conversation({ sessionId }: { sessionId?: string }) {
  const { user } = useAuth(),
    workspace = useWorkspace(),
    navigate = useNavigate(),
    location = useLocation();
  const chat = useChat(user!.id, sessionId);
  const [draft, setDraft] = useState(""),
    [selected, setSelected] = useState<string[]>([]);
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]),
    [docError, setDocError] = useState<unknown>(null);
  const [creating, setCreating] = useState(false),
    [createError, setCreateError] = useState<unknown>(null);
  const controller = useRef<AbortController | null>(null),
    documentController = useRef<AbortController | null>(null);
  const submitLock = useRef(false);
  const autoSend = Boolean((location.state as { send?: boolean } | null)?.send);
  const refreshDocuments = useCallback(() => {
    documentController.current?.abort();
    const next = new AbortController();
    documentController.current = next;
    api
      .documents(next.signal)
      .then((result) => {
        if (!next.signal.aborted) {
          setDocuments(result.items);
          setDocError(null);
        }
      })
      .catch((e) => {
        if (!isAbort(e)) setDocError(e);
      });
  }, []);
  useEffect(() => {
    refreshDocuments();
    window.addEventListener("focus", refreshDocuments);
    window.addEventListener(DOCUMENT_CHANGED, refreshDocuments);
    window.addEventListener(SOURCE_UNAVAILABLE, refreshDocuments);
    return () => {
      controller.current?.abort();
      documentController.current?.abort();
      window.removeEventListener("focus", refreshDocuments);
      window.removeEventListener(DOCUMENT_CHANGED, refreshDocuments);
      window.removeEventListener(SOURCE_UNAVAILABLE, refreshDocuments);
    };
  }, [refreshDocuments]);
  const runPending = chat.run;
  useEffect(() => {
    if (autoSend) void runPending();
  }, [autoSend, runPending]);
  useEffect(() => {
    if (chat.failedQuestion && !chat.pending && !chat.busy) setDraft(chat.failedQuestion);
  }, [chat.failedQuestion, chat.pending, chat.busy]);
  const ready = documents.filter((d) => d.status === "ready");
  const unavailable = selected.some((id) => !ready.some((d) => d.id === id));
  const capped = chat.messages.length >= 98;
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const question = draft.trim();
    if (
      submitLock.current ||
      !question ||
      question.length > 4000 ||
      creating ||
      chat.busy ||
      chat.pending ||
      unavailable ||
      capped ||
      chat.loading ||
      chat.historyError ||
      chat.orphanRun?.status === "running"
    )
      return;
    submitLock.current = true;
    setCreateError(null);
    if (!sessionId) {
      setCreating(true);
      const next = new AbortController();
      controller.current = next;
      try {
        const session = await api.createSession(question.slice(0, 80), next.signal);
        if (next.signal.aborted) return;
        const payload = {
          session_id: session.id,
          client_request_id: crypto.randomUUID(),
          question,
          retrieval_mode: "dense" as const,
          filters: { document_ids: [...selected] },
        };
        savePending(user!.id, session.id, { payload, startedAt: Date.now() });
        workspace.refreshSessions();
        navigate(`/chat/${encodeURIComponent(session.id)}`, { state: { send: true } });
      } catch (e) {
        if (!isAbort(e)) setCreateError(e);
      } finally {
        submitLock.current = false;
        if (!next.signal.aborted) setCreating(false);
      }
    } else {
      try {
        setDraft("");
        await chat.run({
          session_id: sessionId,
          client_request_id: crypto.randomUUID(),
          question,
          retrieval_mode: "dense",
          filters: { document_ids: [...selected] },
        });
      } finally {
        submitLock.current = false;
      }
    }
  };
  const openCitation = (citation: Citation) =>
    workspace.openSource({
      documentId: citation.document_id,
      chunkId: citation.chunk_id,
      filename: citation.file_name,
      location: citation.location,
    });
  const busy = chat.busy || creating;
  const elapsed = useElapsed(busy ? (chat.pending?.startedAt ?? null) : null);
  const chosen = selected.map((id) => documents.find((d) => d.id === id));
  return (
    <section className="chat-page">
      <div className="chat-heading">
        <h1>Hỏi đáp tài liệu</h1>
        <span className="chip">
          <Files size={14} aria-hidden="true" />
          {ready.length} tài liệu sẵn sàng
        </span>
      </div>
      <div className="chat-thread">
        {chat.loading ? (
          <Loading label="Đang kiểm tra lịch sử…" />
        ) : chat.historyError ? (
          <ErrorFeedback error={chat.historyError} retry={() => void chat.refresh(true)} />
        ) : chat.messages.length === 0 && !chat.pending ? (
          <div className="empty-state chat-empty">
            <span className="empty-icon" aria-hidden="true">
              <BookOpenCheck size={28} />
            </span>
            <h2>Bạn cần tìm thông tin gì?</h2>
            <p>
              Hỏi về quy định, quy trình trong tài liệu nội bộ. Mỗi câu trả lời đều kèm nguồn để bạn
              mở ra kiểm tra.
            </p>
            {ready.length === 0 ? (
              <Link className="button" to="/documents">
                Xem tài liệu
              </Link>
            ) : (
              <div className="suggestions" aria-label="Câu hỏi gợi ý">
                {SUGGESTED_QUESTIONS.map((q) => (
                  <button
                    key={q}
                    type="button"
                    className="suggestion"
                    disabled={busy || Boolean(chat.pending)}
                    onClick={() => {
                      setDraft(q);
                      document.getElementById("question")?.focus();
                    }}
                  >
                    {q}
                  </button>
                ))}
              </div>
            )}
          </div>
        ) : (
          chat.messages.map((message) => (
            <div key={message.id} className={`message message-${message.role}`}>
              {message.role === "user" ? (
                <div className="bubble">
                  <p className="sr-only">Bạn</p>
                  <p className="plain-text">{message.content}</p>
                </div>
              ) : message.source_unavailable || !message.answer ? (
                <Feedback title="Nguồn không còn khả dụng">
                  Nội dung trả lời liên quan đã được ẩn hoặc chưa đủ thông tin để hiển thị.
                </Feedback>
              ) : (
                <AnswerView answer={message.answer} onSource={openCitation} />
              )}
            </div>
          ))
        )}
        {chat.pending &&
          (!chat.pending.runId ||
            !chat.messages.some((m) => m.query_run_id === chat.pending!.runId)) && (
            <div className="message message-user">
              <div className="bubble">
                <p className="sr-only">Bạn</p>
                <p className="plain-text">{chat.pending.payload.question}</p>
              </div>
            </div>
          )}
        {busy && (
          <div className="thinking" role="status">
            <LoaderCircle className="spin thinking-icon" size={18} aria-hidden="true" />
            <div className="thinking-body">
              <p className="thinking-title">
                {creating ? "Đang tạo cuộc trò chuyện…" : "Đang tìm tài liệu và soạn câu trả lời…"}
                {!creating && chat.pending && (
                  <span className="elapsed" aria-label={`Đã chờ ${elapsed} giây`}>
                    <Clock size={14} aria-hidden="true" />
                    {clock(elapsed)}
                  </span>
                )}
              </p>
              <p className="hint">
                Thường mất 30–45 giây. Câu trả lời chỉ hiển thị sau khi đã kiểm tra trích dẫn.
              </p>
            </div>
          </div>
        )}
        {chat.pending && !chat.busy && (
          <Feedback
            title="Cần kiểm tra kết quả truy vấn trước"
            action={
              <button className="button" onClick={() => void chat.run()}>
                Kiểm tra lại truy vấn
              </button>
            }
          >
            Kết nối có thể đã gián đoạn trong lúc server xử lý. Kiểm tra cùng truy vấn để tránh gửi
            trùng.
          </Feedback>
        )}
        {chat.orphanRun && (
          <Feedback
            title={
              chat.orphanRun.status === "running"
                ? "Truy vấn trước vẫn đang xử lý"
                : "Truy vấn trước chưa hoàn tất thành công"
            }
            kind={chat.orphanRun.status === "failed" ? "warning" : "info"}
            action={
              <button className="button" disabled={busy} onClick={() => void chat.checkOrphan()}>
                Kiểm tra trạng thái
              </button>
            }
          >
            Bạn có thể kiểm tra trạng thái trước khi gửi câu hỏi mới.
          </Feedback>
        )}
        {chat.error !== null && <ErrorFeedback error={chat.error} />}
        {createError !== null && <ErrorFeedback error={createError} />}
        {chat.error !== null && !chat.pending && (
          <button
            className="text-button"
            onClick={() => {
              const previous = [...chat.messages].reverse().find((m) => m.role === "user");
              if (previous) setDraft(previous.content);
            }}
          >
            Đưa câu hỏi trước vào ô nhập
          </button>
        )}
      </div>
      <div className="chat-composer">
        {docError !== null && (
          <Feedback
            title="Chưa tải được danh sách tài liệu"
            kind="warning"
            action={
              <button className="text-button" onClick={refreshDocuments}>
                Thử lại
              </button>
            }
          >
            Danh sách nguồn có thể chưa cập nhật.
          </Feedback>
        )}
        {unavailable && (
          <Feedback title="Một số tài liệu đã chọn không còn sẵn sàng" kind="warning">
            Hãy chọn lại phạm vi tài liệu trước khi gửi câu hỏi.
          </Feedback>
        )}
        {capped && (
          <Feedback
            title="Phiên gần giới hạn hiển thị lịch sử"
            kind="warning"
            action={
              <Link className="button" to="/chat">
                Tạo cuộc trò chuyện mới
              </Link>
            }
          >
            Ứng dụng hiện hiển thị tối đa 100 tin nhắn trong một phiên. Tạo phiên mới để không mất
            phần kết quả mới khi tải lại.
          </Feedback>
        )}
        <form onSubmit={submit} aria-busy={busy}>
          <details className="document-picker">
            <summary>
              <Funnel size={14} aria-hidden="true" />
              Phạm vi:{" "}
              {selected.length ? `${selected.length} tài liệu đã chọn` : "Tất cả tài liệu sẵn sàng"}
            </summary>
            <div className="document-options">
              <label>
                <input
                  type="checkbox"
                  checked={selected.length === 0}
                  onChange={() => setSelected([])}
                  disabled={busy || Boolean(chat.pending)}
                />
                Tất cả tài liệu sẵn sàng
              </label>
              {ready.map((doc) => (
                <label key={doc.id}>
                  <input
                    type="checkbox"
                    checked={selected.includes(doc.id)}
                    disabled={busy || Boolean(chat.pending)}
                    onChange={(e) =>
                      setSelected((current) =>
                        e.target.checked
                          ? [...current, doc.id]
                          : current.filter((id) => id !== doc.id),
                      )
                    }
                  />
                  <span>{doc.filename}</span>
                </label>
              ))}
              {ready.length === 0 && <p className="hint">Chưa có tài liệu sẵn sàng.</p>}
              {documents.length === 100 && (
                <p className="hint">
                  Bộ chọn hiện hiển thị trong 100 tài liệu đã tải. “Tất cả” vẫn tìm trên toàn bộ tài
                  liệu sẵn sàng của workspace.
                </p>
              )}
            </div>
          </details>
          {selected.length > 0 && (
            <ul className="scope-chips" aria-label="Tài liệu đang hỏi">
              {chosen.map((doc, i) => (
                <li key={selected[i]}>
                  <span>{doc?.filename ?? "Tài liệu không còn trong danh sách"}</span>
                  <button
                    type="button"
                    aria-label={`Bỏ ${doc?.filename ?? "tài liệu"} khỏi phạm vi`}
                    disabled={busy || Boolean(chat.pending)}
                    onClick={() =>
                      setSelected((current) => current.filter((id) => id !== selected[i]))
                    }
                  >
                    <X size={14} aria-hidden="true" />
                  </button>
                </li>
              ))}
            </ul>
          )}
          <div className="composer-box">
            <label htmlFor="question" className="sr-only">
              Câu hỏi của bạn
            </label>
            <textarea
              id="question"
              name="question"
              placeholder="Hỏi về tài liệu, ví dụ: quy trình xin nghỉ phép gồm những bước nào?"
              rows={2}
              value={draft}
              maxLength={4000}
              disabled={busy || Boolean(chat.pending) || capped}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
                  e.preventDefault();
                  e.currentTarget.form?.requestSubmit();
                }
              }}
            />
            <div className="composer-actions">
              <span className="hint">Enter gửi · Shift+Enter xuống dòng</span>
              <button
                className="send-button"
                disabled={
                  busy ||
                  Boolean(chat.pending) ||
                  unavailable ||
                  capped ||
                  chat.loading ||
                  Boolean(chat.historyError) ||
                  chat.orphanRun?.status === "running" ||
                  !draft.trim()
                }
              >
                <ArrowUp size={18} aria-hidden="true" />
                <span className="sr-only">{busy ? "Đang xử lý…" : "Gửi câu hỏi"}</span>
              </button>
            </div>
          </div>
        </form>
        <p className="hint composer-note">
          Mỗi câu hỏi được trả lời độc lập, hãy ghi đủ ngữ cảnh. AI có thể sai, hãy mở nguồn để kiểm
          tra trước khi sử dụng.
        </p>
      </div>
    </section>
  );
}
