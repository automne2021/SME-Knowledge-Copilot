import { useEffect, useRef, useState, type FormEvent } from "react";
import { api } from "../../api";
import { isAbort } from "../../api/client";
import type { Folder, KnowledgeDocument } from "../../api/types";
import { documentChanged } from "../../auth/session";
import { Dialog } from "../../components/ui/Dialog";
import { ErrorFeedback } from "../../components/ui/Feedback";
import { foldersChanged } from "./useFolders";

export type FolderAction = { kind: "create" } | { kind: "rename" | "delete"; folder: Folder };
export function FolderDialog({
  action,
  onClose,
  onDone,
}: {
  action: FolderAction;
  onClose: () => void;
  onDone: () => void;
}) {
  const [name, setName] = useState(action.kind === "create" ? "" : action.folder.name);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const controller = useRef<AbortController | null>(null);
  useEffect(() => () => controller.current?.abort(), []);
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (
      busy ||
      (action.kind !== "delete" && (!name.trim() || Array.from(name.trim()).length > 100))
    )
      return;
    setBusy(true);
    setError(null);
    const next = new AbortController();
    controller.current = next;
    try {
      if (action.kind === "create") await api.createFolder(name.trim(), next.signal);
      else if (action.kind === "rename")
        await api.renameFolder(action.folder.id, name.trim(), next.signal);
      else await api.deleteFolder(action.folder.id, next.signal);
      if (!next.signal.aborted) {
        foldersChanged();
        onDone();
      }
    } catch (e) {
      if (!isAbort(e)) setError(e);
    } finally {
      if (!next.signal.aborted) setBusy(false);
    }
  };
  const title =
    action.kind === "create"
      ? "Tạo thư mục"
      : action.kind === "rename"
        ? "Đổi tên thư mục"
        : "Xóa thư mục?";
  return (
    <Dialog title={title} onClose={onClose} busy={busy}>
      <form onSubmit={submit}>
        {action.kind === "delete" ? (
          <>
            <p>Bạn có muốn xóa thư mục “{action.folder.name}”?</p>
            <p className="muted">
              Chỉ xóa được thư mục không còn tài liệu tham chiếu. Số tài liệu sẵn sàng không quyết
              định thư mục có rỗng hay không.
            </p>
          </>
        ) : (
          <>
            {action.kind === "rename" && (
              <p>Đổi tên thư mục “{action.folder.name}”. Xác nhận bằng nút bên dưới.</p>
            )}
            <label className="field">
              Tên thư mục
              <input
                value={name}
                required
                disabled={busy}
                onChange={(e) => setName(e.target.value)}
                autoComplete="off"
              />
            </label>
            <p className="hint">Từ 1 đến 100 ký tự, không trùng tên thư mục khác.</p>
          </>
        )}
        {error !== null && <ErrorFeedback error={error} />}
        <div className="dialog-actions">
          <button type="button" className="button" onClick={onClose} disabled={busy}>
            Hủy
          </button>
          <button
            className={`button ${action.kind === "delete" ? "button-destructive" : "button-primary"}`}
            disabled={
              busy ||
              (action.kind !== "delete" && (!name.trim() || Array.from(name.trim()).length > 100))
            }
          >
            {busy
              ? "Đang lưu…"
              : action.kind === "create"
                ? "Tạo thư mục"
                : action.kind === "rename"
                  ? "Xác nhận đổi tên"
                  : "Xóa thư mục"}
          </button>
        </div>
      </form>
    </Dialog>
  );
}

export function MoveDocumentDialog({
  document: doc,
  folders,
  onClose,
  onDone,
}: {
  document: KnowledgeDocument;
  folders: Folder[];
  onClose: () => void;
  onDone: () => void;
}) {
  const [folderId, setFolderId] = useState(doc.folder_id ?? "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const controller = useRef<AbortController | null>(null);
  useEffect(() => () => controller.current?.abort(), []);
  const missing = Boolean(folderId && !folders.some((f) => f.id === folderId));
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (busy || missing) return;
    const next = new AbortController();
    controller.current = next;
    setBusy(true);
    setError(null);
    try {
      await api.moveDocument(doc.id, folderId || null, next.signal);
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
    <Dialog title="Chuyển thư mục tài liệu" onClose={onClose} busy={busy}>
      <p className="selected-file">{doc.filename}</p>
      <form onSubmit={submit}>
        <label className="field">
          Thư mục đích
          <select value={folderId} onChange={(e) => setFolderId(e.target.value)} disabled={busy}>
            <option value="">Chưa phân loại</option>
            {missing && <option value={folderId}>Thư mục không còn trong danh sách</option>}
            {folders.map((f) => (
              <option value={f.id} key={f.id}>
                {f.name}
              </option>
            ))}
          </select>
        </label>
        {error !== null && <ErrorFeedback error={error} />}
        <div className="dialog-actions">
          <button type="button" className="button" onClick={onClose} disabled={busy}>
            Hủy
          </button>
          <button className="button button-primary" disabled={busy || missing}>
            {busy ? "Đang lưu…" : "Lưu thư mục"}
          </button>
        </div>
      </form>
    </Dialog>
  );
}
