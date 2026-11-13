import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../../api";
import { ApiError, isAbort } from "../../api/client";
import type { Answer, ChatMessage, ChatQuery } from "../../api/types";
import { DOCUMENT_CHANGED } from "../../auth/session";
import { SOURCE_UNAVAILABLE } from "../sources/SourcePanel";
import { readPending, savePending, type PendingQuery } from "./pending";
function pause(signal: AbortSignal) {
  return new Promise<void>((resolve, reject) => {
    const abort = () => {
      clearTimeout(timer);
      reject(new DOMException("Aborted", "AbortError"));
    };
    const timer = setTimeout(() => {
      signal.removeEventListener("abort", abort);
      resolve();
    }, 3000);
    if (signal.aborted) abort();
    else signal.addEventListener("abort", abort, { once: true });
  });
}
export const REVALIDATE_DELAY_MS = 150;
export function useChat(userId: string, sessionId: string | undefined) {
  const [messages, setMessages] = useState<ChatMessage[]>([]),
    [loading, setLoading] = useState(Boolean(sessionId));
  const [error, setError] = useState<unknown>(null),
    [historyError, setHistoryError] = useState<unknown>(null),
    [busy, setBusy] = useState(false);
  const [pending, setPending] = useState<PendingQuery | null>(() =>
    sessionId ? readPending(userId, sessionId) : null,
  );
  const [orphanRun, setOrphanRun] = useState<Answer | null>(null);
  const [failedQuestion, setFailedQuestion] = useState("");
  const pendingRef = useRef(pending),
    request = useRef<AbortController | null>(null),
    history = useRef<AbortController | null>(null);
  const updatePending = useCallback(
    (next: PendingQuery | null) => {
      pendingRef.current = next;
      setPending(next);
      if (sessionId) savePending(userId, sessionId, next);
    },
    [userId, sessionId],
  );
  const refresh = useCallback(
    async (hide = false) => {
      if (!sessionId) return;
      history.current?.abort();
      const next = new AbortController();
      history.current = next;
      if (hide) {
        setMessages([]);
        setLoading(true);
        setOrphanRun(null);
      }
      setHistoryError(null);
      try {
        const result = await api.messages(sessionId, next.signal);
        if (next.signal.aborted) return;
        setMessages(result.items);
        const last = result.items[result.items.length - 1];
        if (last?.role === "user" && last.query_run_id && !pendingRef.current) {
          const run = await api.run(last.query_run_id, next.signal);
          if (!next.signal.aborted) setOrphanRun(run.status === "completed" ? null : run);
        } else setOrphanRun(null);
      } catch (e) {
        if (!isAbort(e)) setHistoryError(e);
      } finally {
        if (!next.signal.aborted) setLoading(false);
      }
    },
    [sessionId],
  );
  useEffect(() => {
    void refresh(true);
    // Returning to the tab fires both "visibilitychange" and "focus". Coalesce them into one
    // background revalidation that keeps the thread on screen; the server response replaces it
    // (including redactions). Clearing first caused a spinner, layout jumps and double loads.
    let timer: ReturnType<typeof setTimeout> | undefined;
    const revalidate = () => {
      if (document.hidden) return;
      clearTimeout(timer);
      timer = setTimeout(() => void refresh(), REVALIDATE_DELAY_MS);
    };
    // In-app deletes still clear immediately: we know the content is no longer valid.
    const invalidate = () => {
      clearTimeout(timer);
      setMessages([]);
      setOrphanRun(null);
      void refresh(true);
    };
    window.addEventListener("focus", revalidate);
    document.addEventListener("visibilitychange", revalidate);
    window.addEventListener(DOCUMENT_CHANGED, invalidate);
    window.addEventListener(SOURCE_UNAVAILABLE, invalidate);
    return () => {
      clearTimeout(timer);
      history.current?.abort();
      request.current?.abort();
      window.removeEventListener("focus", revalidate);
      document.removeEventListener("visibilitychange", revalidate);
      window.removeEventListener(DOCUMENT_CHANGED, invalidate);
      window.removeEventListener(SOURCE_UNAVAILABLE, invalidate);
    };
  }, [refresh]);
  const run = useCallback(
    async (payload?: ChatQuery) => {
      if (!sessionId) return;
      request.current?.abort();
      const next = new AbortController();
      request.current = next;
      const current = payload ? { payload, startedAt: Date.now() } : pendingRef.current;
      if (!current) return;
      updatePending(current);
      setBusy(true);
      setError(null);
      setOrphanRun(null);
      setFailedQuestion("");
      const started = Date.now();
      try {
        let result: Answer;
        try {
          result = current.runId
            ? await api.run(current.runId, next.signal)
            : await api.query(current.payload, next.signal);
        } catch (e) {
          if (
            e instanceof ApiError &&
            e.code === "query_in_progress" &&
            typeof e.details?.run_id === "string"
          ) {
            current.runId = e.details.run_id;
            updatePending({ ...current });
            result = await api.run(current.runId, next.signal);
          } else throw e;
        }
        while (result.status === "running") {
          current.runId = result.run_id ?? result.id;
          updatePending({ ...current });
          if (!current.runId || Date.now() - started > 180000)
            throw new ApiError(
              0,
              "request_timeout",
              "Chưa xác định được kết quả. Hãy kiểm tra lại truy vấn đang xử lý.",
            );
          await pause(next.signal);
          result = await api.run(current.runId, next.signal);
        }
        if (next.signal.aborted) return;
        updatePending(null);
        if (result.status === "failed")
          throw new ApiError(
            503,
            result.error_code ?? "query_failed",
            "Truy vấn đã kết thúc nhưng chưa tạo được câu trả lời. Bạn có thể gửi câu hỏi mới.",
          );
        await refresh();
      } catch (e) {
        if (!isAbort(e) && !next.signal.aborted) {
          if (
            e instanceof ApiError &&
            e.status !== 0 &&
            !["database_unavailable", "internal_error"].includes(e.code)
          )
            updatePending(null);
          if (e instanceof ApiError && ["source_changed", "source_unavailable"].includes(e.code))
            window.dispatchEvent(new CustomEvent(SOURCE_UNAVAILABLE, { detail: null }));
          setFailedQuestion(current.payload.question);
          setError(e);
          await refresh();
        }
      } finally {
        if (!next.signal.aborted) setBusy(false);
      }
    },
    [sessionId, updatePending, refresh],
  );
  const checkOrphan = async () => {
    if (!orphanRun) return;
    request.current?.abort();
    const next = new AbortController();
    request.current = next;
    setBusy(true);
    try {
      const value = await api.run(orphanRun.run_id ?? orphanRun.id!, next.signal);
      if (!next.signal.aborted) {
        setOrphanRun(value.status === "completed" ? null : value);
        await refresh();
      }
    } catch (e) {
      if (!isAbort(e)) setError(e);
    } finally {
      if (!next.signal.aborted) setBusy(false);
    }
  };
  return {
    messages,
    loading,
    error,
    historyError,
    busy,
    pending,
    orphanRun,
    failedQuestion,
    run,
    checkOrphan,
    refresh,
  };
}
