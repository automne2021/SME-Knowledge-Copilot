import { useEffect, useRef, useState, type FormEvent } from "react";
import { Upload } from "lucide-react";
import { api } from "../../api";
import { ApiError, isAbort } from "../../api/client";
import type { Folder, KnowledgeDocument } from "../../api/types";
import { documentChanged } from "../../auth/session";
import { Dialog } from "../../components/ui/Dialog";
import { ErrorFeedback, Feedback } from "../../components/ui/Feedback";
import { fileSize } from "../../lib/format";
export function UploadDialog({
  onClose,
  onDone,
  folders = [],
  initialFolderId = "",
}: {
  onClose: () => void;
  onDone: (notice: string) => void;
  folders?: Folder[];
  initialFolderId?: string;
}) {
  const [folderId, setFolderId] = useState(initialFolderId);
  const missingFolder = Boolean(folderId && !folders.some((f) => f.id === folderId));
  const [file, setFile] = useState<File | null>(null),
    [error, setError] = useState<unknown>(null),
    [validation, setValidation] = useState("");
  const [busy, setBusy] = useState(false);
  const controller = useRef<AbortController | null>(null);
  useEffect(() => () => controller.current?.abort(), []);
  const select = (candidate?: File) => {
    setError(null);
    setValidation("");
    setFile(null);
    if (!candidate) return;
    if (!/\.(pdf|docx|txt|md)$/i.test(candidate.name)) {
      setValidation("Chọn file PDF, DOCX, TXT hoặc MD.");
      return;
    }
    if (candidate.size > 20 * 1024 ** 2) {
      setValidation("File vượt giới hạn 20 MB.");
      return;
    }
    setFile(candidate);
  };
  const upload = async (e: FormEvent) => {
    e.preventDefault();
    if (!file || busy || missingFolder) return;
    setBusy(true);
    setError(null);
    const next = new AbortController();
    controller.current = next;
    try {
      const result = await api.upload(file, next.signal, folderId);
      if (!next.signal.aborted) {
        documentChanged(result.document_id);
        onDone("Đã nhận tài liệu. Nội dung sẽ được dùng khi xử lý hoàn tất.");
      }
    } catch (e) {
      if (!isAbort(e)) setError(e);
    } finally {
      if (!next.signal.aborted) setBusy(false);
    }
  };
  const duplicate =
    error instanceof ApiError &&
    error.code === "duplicate_document" &&
    typeof error.details?.document_id === "string"
      ? error.details.document_id
      : null;
  return (
    <Dialog title="Tải tài liệu" onClose={onClose} busy={busy}>
      <form onSubmit={upload}>
        <label className="field">
          Thư mục (tùy chọn)
          <select value={folderId} disabled={busy} onChange={(e) => setFolderId(e.target.value)}>
            <option value="">Chưa phân loại</option>
            {missingFolder && <option value={folderId}>Thư mục không còn trong danh sách</option>}
            {folders.map((f) => (
              <option value={f.id} key={f.id}>
                {f.name}
              </option>
            ))}
          </select>
        </label>
        <div
          className={`drop-zone ${busy ? "disabled" : ""}`}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            if (!busy) select(e.dataTransfer.files[0]);
          }}
        >
          <Upload className="drop-icon" size={26} aria-hidden="true" />
          <label className="drop-label">
            Chọn hoặc thả một tài liệu
            <input
              className="sr-only"
              type="file"
              accept=".pdf,.docx,.txt,.md"
              disabled={busy}
              onChange={(e) => select(e.target.files?.[0])}
            />
          </label>
          <p className="hint">PDF có text, DOCX, TXT, MD · Tối đa 20 MB mỗi file</p>
        </div>
        {file && (
          <p className="selected-file">
            {file.name} <span className="muted">· {fileSize(file.size)}</span>
          </p>
        )}
        {validation && (
          <Feedback title="Chưa thể chọn file" kind="error">
            {validation}
          </Feedback>
        )}
        {error !== null && <ErrorFeedback error={error} />}
        {duplicate && (
          <a
            className="text-link"
            href={`#document-${encodeURIComponent(duplicate)}`}
            onClick={() => onDone("Tài liệu này đã tồn tại. Danh sách đã được cập nhật.")}
          >
            Xem tài liệu đã có trong danh sách
          </a>
        )}
        <div className="dialog-actions">
          <button className="button" type="button" onClick={onClose} disabled={busy}>
            Hủy
          </button>
          <button className="button button-primary" disabled={!file || busy || missingFolder}>
            {busy ? "Đang tải tài liệu…" : "Tải tài liệu"}
          </button>
        </div>
      </form>
    </Dialog>
  );
}
export function DeleteDialog({
  document: doc,
  onClose,
  onDone,
}: {
  document: KnowledgeDocument;
  onClose: () => void;
  onDone: () => void;
}) {
  const [name, setName] = useState(""),
    [busy, setBusy] = useState(false),
    [error, setError] = useState<unknown>(null);
  const controller = useRef<AbortController | null>(null);
  const cancelRef = useRef<HTMLButtonElement>(null);
  useEffect(() => () => controller.current?.abort(), []);
  const remove = async (e: FormEvent) => {
    e.preventDefault();
    if (busy || name !== doc.filename) return;
    setBusy(true);
    setError(null);
    const next = new AbortController();
    controller.current = next;
    try {
      await api.remove(doc.id, next.signal);
      if (!next.signal.aborted) {
        documentChanged(doc.id);
        onDone();
      }
    } catch (e) {
      if (!isAbort(e)) setError(e);
    } finally {
      if (!next.signal.aborted) setBusy(false);
    }
  };
  return (
    <Dialog title="Xóa tài liệu?" onClose={onClose} busy={busy} initialFocus={cancelRef}>
      <p className="muted">
        Tài liệu sẽ ngừng được dùng để trả lời. Nội dung liên quan trong lịch sử sẽ không còn khả
        dụng.
      </p>
      <p className="selected-file">{doc.filename}</p>
      <form onSubmit={remove}>
        <label className="field">
          Nhập đúng tên tài liệu để xác nhận
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            autoComplete="off"
            disabled={busy}
          />
        </label>
        {error !== null && <ErrorFeedback error={error} />}
        <div className="dialog-actions">
          <button
            ref={cancelRef}
            type="button"
            className="button"
            onClick={onClose}
            disabled={busy}
          >
            Hủy
          </button>
          <button className="button button-destructive" disabled={busy || name !== doc.filename}>
            {busy ? "Đang xóa…" : "Xóa tài liệu"}
          </button>
        </div>
      </form>
    </Dialog>
  );
}
