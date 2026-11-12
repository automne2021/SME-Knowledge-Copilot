import { useCallback, useEffect, useRef, useState } from "react";
import { Download, ExternalLink, FileText, Quote, X } from "lucide-react";
import { api } from "../../api";
import { ApiError, isAbort } from "../../api/client";
import type { SourceChunk, SourceTarget } from "../../api/types";
import { DOCUMENT_CHANGED } from "../../auth/session";
import { Dialog } from "../../components/ui/Dialog";
import { ErrorFeedback, Feedback, Loading } from "../../components/ui/Feedback";
import { useMedia } from "../../hooks/useMedia";
import { sourceLocation } from "../../lib/format";
export const SOURCE_UNAVAILABLE = "sme:source-unavailable";
export function SourcePanel({ target, onClose }: { target: SourceTarget; onClose: () => void }) {
  const modal = useMedia("(max-width:1199px)");
  const [chunk, setChunk] = useState<SourceChunk | null>(null),
    [filename, setFilename] = useState("");
  const [full, setFull] = useState<{ url?: string; text?: string } | null>(null);
  const [loading, setLoading] = useState(true),
    [fullLoading, setFullLoading] = useState(false),
    [error, setError] = useState<unknown>(null);
  const controller = useRef<AbortController | null>(null),
    contentController = useRef<AbortController | null>(null);
  const url = useRef<string | null>(null);
  const clear = useCallback(() => {
    setChunk(null);
    setFull(null);
    setFilename("");
    setFullLoading(false);
    if (url.current) URL.revokeObjectURL(url.current);
    url.current = null;
    contentController.current?.abort();
  }, []);
  const loadContent = useCallback(
    async (signal: AbortSignal) => {
      const blob = await api.content(target.documentId, signal);
      if (signal.aborted) return;
      if (blob.type.split(";")[0] === "application/pdf") {
        const value = URL.createObjectURL(blob);
        if (signal.aborted) {
          URL.revokeObjectURL(value);
          return;
        }
        if (url.current) URL.revokeObjectURL(url.current);
        url.current = value;
        setFull({ url: value });
      } else {
        const text = await blob.text();
        if (!signal.aborted) setFull({ text });
      }
    },
    [target.documentId],
  );
  const failed = useCallback(
    (e: unknown) => {
      if (isAbort(e)) return;
      clear();
      setError(e);
      if (e instanceof ApiError && [404, 409, 410].includes(e.status))
        window.dispatchEvent(new CustomEvent(SOURCE_UNAVAILABLE, { detail: target.documentId }));
    },
    [clear, target.documentId],
  );
  const refresh = useCallback(() => {
    controller.current?.abort();
    clear();
    setLoading(true);
    setError(null);
    const next = new AbortController();
    controller.current = next;
    (async () => {
      const doc = await api.document(target.documentId, next.signal);
      if (doc.status !== "ready")
        throw new ApiError(410, "source_unavailable", "Nguồn không còn sẵn sàng để xem.");
      const value = target.chunkId
        ? await api.chunk(target.documentId, target.chunkId, next.signal)
        : null;
      if (next.signal.aborted) return;
      setFilename(doc.filename);
      setChunk(value);
      if (!target.chunkId) await loadContent(next.signal);
    })()
      .catch(failed)
      .finally(() => {
        if (!next.signal.aborted) setLoading(false);
      });
  }, [clear, failed, loadContent, target.documentId, target.chunkId]);
  useEffect(() => {
    refresh();
    const visibility = () => {
      if (document.hidden) {
        controller.current?.abort();
        clear();
        setLoading(true);
      } else refresh();
    };
    const changed = (e: Event) => {
      if ((e as CustomEvent).detail === target.documentId) refresh();
    };
    const unknownSourceChanged = (e: Event) => {
      if ((e as CustomEvent).detail === null) refresh();
    };
    window.addEventListener("focus", refresh);
    document.addEventListener("visibilitychange", visibility);
    window.addEventListener(DOCUMENT_CHANGED, changed);
    window.addEventListener(SOURCE_UNAVAILABLE, unknownSourceChanged);
    return () => {
      controller.current?.abort();
      contentController.current?.abort();
      if (url.current) URL.revokeObjectURL(url.current);
      window.removeEventListener("focus", refresh);
      document.removeEventListener("visibilitychange", visibility);
      window.removeEventListener(DOCUMENT_CHANGED, changed);
      window.removeEventListener(SOURCE_UNAVAILABLE, unknownSourceChanged);
    };
  }, [refresh, clear, target.documentId]);
  useEffect(() => {
    if (modal) return;
    const key = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", key);
    return () => window.removeEventListener("keydown", key);
  }, [modal, onClose]);
  const openFull = async () => {
    const next = new AbortController();
    contentController.current?.abort();
    contentController.current = next;
    setFullLoading(true);
    setError(null);
    try {
      await loadContent(next.signal);
    } catch (e) {
      failed(e);
    } finally {
      if (!next.signal.aborted) setFullLoading(false);
    }
  };
  const unavailable = error instanceof ApiError && [404, 409, 410].includes(error.status);
  const body = (
    <>
      {loading ? (
        <Loading label="Đang kiểm tra nguồn…" />
      ) : error ? (
        unavailable ? (
          <Feedback title="Nguồn không còn khả dụng" kind="warning">
            Tài liệu đã bị xóa, thay đổi hoặc bạn không còn quyền truy cập. Nội dung cũ đã được ẩn.
          </Feedback>
        ) : (
          <ErrorFeedback error={error} retry={refresh} />
        )
      ) : (
        <>
          <div className="source-file">
            <span className="source-file-icon" aria-hidden="true">
              <FileText size={18} />
            </span>
            <div>
              <p className="source-filename">{filename}</p>
              {chunk && <span className="chip">{sourceLocation(chunk.location)}</span>}
            </div>
          </div>
          {chunk && (
            <figure className="source-excerpt">
              <figcaption>
                <Quote size={14} aria-hidden="true" />
                Đoạn được trích dẫn
              </figcaption>
              <blockquote>{chunk.text}</blockquote>
            </figure>
          )}
          {!full && (
            <button className="button" onClick={openFull} disabled={fullLoading}>
              <ExternalLink size={16} aria-hidden="true" />
              {fullLoading ? "Đang tải tài liệu…" : "Mở tài liệu"}
            </button>
          )}
          {full?.text !== undefined && <pre className="source-text">{full.text}</pre>}
          {full?.url && (
            <>
              <iframe
                className="source-pdf"
                title={`Nội dung ${filename}`}
                src={`${full.url}#page=${chunk?.location.page_start ?? target.location?.page_start ?? 1}`}
              />
              <a className="button" href={full.url} download={filename}>
                <Download size={16} aria-hidden="true" />
                Tải bản PDF
              </a>
              <p className="hint">
                Nếu trình duyệt không xem được PDF, hãy tải bản đã kiểm tra quyền truy cập.
              </p>
            </>
          )}
          <p className="hint">Đối chiếu nội dung và điều kiện áp dụng trước khi sử dụng.</p>
        </>
      )}
    </>
  );
  return modal ? (
    <Dialog title="Nguồn tham chiếu" className="source-dialog" onClose={onClose}>
      {body}
    </Dialog>
  ) : (
    <aside className="source-panel" aria-label="Nguồn tham chiếu">
      <div className="source-header">
        <h2>Nguồn tham chiếu</h2>
        <button className="icon-button" aria-label="Đóng" onClick={onClose}>
          <X size={18} aria-hidden="true" />
        </button>
      </div>
      {body}
    </aside>
  );
}
