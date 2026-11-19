import { useEffect, useMemo, useRef, useState } from "react";
import { Eye, RotateCw, Search, Trash2, Upload } from "lucide-react";
import { api } from "../api";
import { isAbort } from "../api/client";
import type { DocumentStatus, KnowledgeDocument, Job } from "../api/types";
import { useAuth } from "../auth/AuthProvider";
import { useWorkspace } from "../workspace/WorkspaceProvider";
import { ErrorFeedback, Feedback, Loading } from "../components/ui/Feedback";
import { DeleteDialog, UploadDialog } from "../features/documents/DocumentDialogs";
import { useDocuments } from "../features/documents/useDocuments";
import { useFolders } from "../features/folders/useFolders";
import {
  FolderDialog,
  MoveDocumentDialog,
  type FolderAction,
} from "../features/folders/FolderDialogs";
import { clock, useNow } from "../hooks/useElapsed";
import {
  fileKind,
  fileSize,
  formatDate,
  INGEST_STAGES,
  stageLabel,
  warningsFor,
} from "../lib/format";
const statusLabels = {
  queued: "Đang chờ",
  processing: "Đang xử lý",
  ready: "Sẵn sàng",
  failed: "Xử lý thất bại",
  needs_ocr: "Cần bản có text",
  deleting: "Đang xóa",
  deleted: "Đã xóa",
};
type StatusFilter = "all" | "ready" | "active" | "attention";
const FILTERS: { key: StatusFilter; label: string; match: (status: DocumentStatus) => boolean }[] =
  [
    { key: "all", label: "Tất cả", match: () => true },
    { key: "ready", label: "Sẵn sàng", match: (s) => s === "ready" },
    {
      key: "active",
      label: "Đang xử lý",
      match: (s) => s === "queued" || s === "processing" || s === "deleting",
    },
    { key: "attention", label: "Cần chú ý", match: (s) => s === "failed" || s === "needs_ocr" },
  ];
/** "Bước 4/6 · Lập chỉ mục · 8/14 đoạn" from the worker's real stage and chunk counters. */
export function progressText(job: Job) {
  const step = INGEST_STAGES.indexOf(job.stage);
  const parts = [];
  if (step >= 0) parts.push(`Bước ${step + 1}/${INGEST_STAGES.length}`);
  parts.push(stageLabel[job.stage] ?? "Đang xử lý tài liệu");
  const done = job.progress?.completed_units,
    total = job.progress?.total_units;
  if (typeof done === "number" && typeof total === "number" && total > 0)
    parts.push(`${done}/${total} đoạn`);
  return parts.join(" · ");
}
export default function DocumentsPage() {
  const { user } = useAuth();
  const { openSource } = useWorkspace();
  const [folderId, setFolderId] = useState("");
  const documents = useDocuments(folderId || undefined);
  const folders = useFolders();
  const [folderAction, setFolderAction] = useState<FolderAction | null>(null);
  const [move, setMove] = useState<KnowledgeDocument | null>(null);
  const admin = user?.role === "knowledge_admin";
  const [upload, setUpload] = useState(false),
    [remove, setRemove] = useState<KnowledgeDocument | null>(null);
  const [notice, setNotice] = useState(""),
    [actionError, setActionError] = useState<unknown>(null),
    [busy, setBusy] = useState<string | null>(null);
  const [query, setQuery] = useState(""),
    [filter, setFilter] = useState<StatusFilter>("all");
  const controller = useRef<AbortController | null>(null);
  useEffect(() => () => controller.current?.abort(), []);
  const visible = useMemo(() => {
    const needle = query.trim().toLocaleLowerCase("vi");
    const match = FILTERS.find((f) => f.key === filter)!.match;
    return documents.items.filter(
      (d) => match(d.status) && (!needle || d.filename.toLocaleLowerCase("vi").includes(needle)),
    );
  }, [documents.items, query, filter]);
  const now = useNow(
    documents.items.some((d) => d.status === "queued" || d.status === "processing"),
  );
  const retry = async (job: Job) => {
    if (busy) return;
    const next = new AbortController();
    controller.current = next;
    setBusy(job.id);
    setActionError(null);
    try {
      await api.retry(job.id, next.signal);
      if (!next.signal.aborted) {
        setNotice(
          job.kind === "cleanup"
            ? "Đã yêu cầu thử lại dọn dẹp. Tài liệu tiếp tục bị loại khỏi nguồn hỏi đáp."
            : "Đã yêu cầu xử lý lại tài liệu.",
        );
        documents.refresh();
      }
    } catch (e) {
      if (!isAbort(e)) setActionError(e);
    } finally {
      if (!next.signal.aborted) setBusy(null);
    }
  };
  return (
    <section className="page documents-page">
      <div className="page-heading">
        <div>
          <h1>Tài liệu</h1>
          <p className="muted">Quản lý nguồn kiến thức của không gian làm việc.</p>
        </div>
        {admin && (
          <button className="button button-primary" onClick={() => setUpload(true)}>
            <Upload size={16} aria-hidden="true" />
            Tải tài liệu
          </button>
        )}
      </div>
      {notice && <Feedback title={notice} />}
      {actionError !== null && <ErrorFeedback error={actionError} />}
      <section className="folder-section" aria-label="Thư mục tài liệu">
        <div className="folder-heading">
          <h2>Thư mục</h2>
          {admin && (
            <button className="button" onClick={() => setFolderAction({ kind: "create" })}>
              Tạo thư mục
            </button>
          )}
        </div>
        {folders.loading ? (
          <Loading label="Đang tải thư mục…" />
        ) : folders.error ? (
          <ErrorFeedback error={folders.error} retry={folders.refresh} />
        ) : (
          <>
            <label className="field folder-filter">
              Lọc theo thư mục
              <select value={folderId} onChange={(e) => setFolderId(e.target.value)}>
                <option value="">Tất cả thư mục</option>
                {folderId && !folders.items.some((f) => f.id === folderId) && (
                  <option value={folderId}>Thư mục không còn trong danh sách</option>
                )}
                {folders.items.map((f) => (
                  <option key={f.id} value={f.id}>
                    {f.name}
                  </option>
                ))}
              </select>
            </label>
            {folders.items.length === 0 && (
              <p className="hint">Chưa có thư mục. Tài liệu vẫn có thể để chưa phân loại.</p>
            )}
            <ul className="folder-list">
              {folders.items.map((f) => (
                <li key={f.id}>
                  <div>
                    <strong>{f.name}</strong>
                    <small>{f.ready_document_count} tài liệu sẵn sàng</small>
                  </div>
                  {admin && (
                    <div className="row-actions">
                      <button
                        className="text-button"
                        aria-label={`Đổi tên thư mục “${f.name}”`}
                        onClick={() => setFolderAction({ kind: "rename", folder: f })}
                      >
                        Đổi tên
                      </button>
                      <button
                        className="text-button destructive"
                        aria-label={`Xóa thư mục “${f.name}”`}
                        onClick={() => setFolderAction({ kind: "delete", folder: f })}
                      >
                        Xóa
                      </button>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          </>
        )}
      </section>
      {documents.paused && (
        <Feedback
          title="Tác vụ vẫn có thể đang xử lý"
          action={
            <button className="button" onClick={documents.refresh}>
              Kiểm tra lại
            </button>
          }
        >
          Đã tạm dừng tự kiểm tra sau thời gian chờ. Trạng thái tác vụ trên server không thay đổi.
        </Feedback>
      )}
      {documents.jobError && (
        <Feedback
          title="Chưa tải đủ trạng thái tác vụ"
          kind="warning"
          action={
            <button className="button" onClick={documents.refresh}>
              Kiểm tra lại
            </button>
          }
        >
          Một số thông tin retry có thể tạm thời chưa hiển thị.
        </Feedback>
      )}
      {documents.loading ? (
        <Loading label="Đang tải tài liệu…" />
      ) : documents.error ? (
        <ErrorFeedback error={documents.error} retry={documents.refresh} />
      ) : documents.items.length === 0 ? (
        <div className="empty-state">
          <h2>{folderId ? "Thư mục chưa có tài liệu" : "Chưa có tài liệu"}</h2>
          <p>
            {admin
              ? "Tải tài liệu đầu tiên để bắt đầu tìm kiếm và hỏi đáp."
              : "Quản trị viên chưa thêm tài liệu vào không gian làm việc."}
          </p>
          {admin && (
            <button className="button" onClick={() => setUpload(true)}>
              Tải tài liệu
            </button>
          )}
        </div>
      ) : (
        <>
          <div className="list-toolbar">
            <label className="search-field">
              <Search size={16} aria-hidden="true" />
              <span className="sr-only">Tìm tài liệu</span>
              <input
                type="search"
                placeholder="Tìm theo tên tài liệu"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </label>
            <div className="filter-group" role="group" aria-label="Lọc theo trạng thái">
              {FILTERS.map((option) => (
                <button
                  key={option.key}
                  type="button"
                  className="filter-chip"
                  aria-pressed={filter === option.key}
                  onClick={() => setFilter(option.key)}
                >
                  {option.label}
                  <span className="count">
                    {documents.items.filter((d) => option.match(d.status)).length}
                  </span>
                </button>
              ))}
            </div>
            <button
              className="text-button"
              onClick={() => {
                documents.refresh();
                folders.refresh();
              }}
            >
              <RotateCw size={14} aria-hidden="true" />
              Làm mới
            </button>
          </div>
          {documents.items.length === 100 && (
            <p className="hint">Đang hiển thị tối đa 100 tài liệu gần nhất.</p>
          )}
          {visible.length === 0 && (
            <p className="hint">Không có tài liệu nào khớp bộ lọc hiện tại.</p>
          )}
          <table className="document-table">
            <thead>
              <tr>
                <th scope="col">Tên tài liệu</th>
                <th scope="col">Thư mục</th>
                <th scope="col">Trạng thái</th>
                <th scope="col">Tải lên</th>
                <th scope="col">Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((doc) => {
                const job = doc.latest_job_id ? documents.jobs[doc.latest_job_id] : undefined;
                const cleanupFailed = doc.status === "deleting" && job?.status === "failed";
                const retryable =
                  job?.status === "failed" &&
                  job.retryable &&
                  (doc.status === "failed" || doc.status === "deleting");
                const warning = warningsFor(doc);
                return (
                  <tr key={doc.id} id={`document-${doc.id}`}>
                    <td>
                      <div className="file-cell">
                        <span
                          className={`file-badge file-${fileKind(doc.filename).toLowerCase()}`}
                          aria-hidden="true"
                        >
                          {fileKind(doc.filename)}
                        </span>
                        <div>
                          <span className="filename">{doc.filename}</span>
                          <small>{fileSize(doc.size_bytes)}</small>
                        </div>
                      </div>
                    </td>
                    <td data-label="Thư mục">
                      {doc.folder_id
                        ? (folders.items.find((f) => f.id === doc.folder_id)?.name ??
                          "Chưa tải được tên thư mục")
                        : "Chưa phân loại"}
                    </td>
                    <td data-label="Trạng thái">
                      <span className={`status status-${cleanupFailed ? "failed" : doc.status}`}>
                        {cleanupFailed ? "Lỗi dọn dẹp" : statusLabels[doc.status]}
                      </span>
                      {(doc.status === "queued" || doc.status === "processing") && (
                        <small className="elapsed-note">
                          {clock(
                            Math.max(0, Math.floor((now - Date.parse(doc.created_at)) / 1000)),
                          )}{" "}
                          kể từ lúc tải lên
                        </small>
                      )}
                      {doc.status === "processing" && job && (
                        <>
                          <small>{progressText(job)}</small>
                          {INGEST_STAGES.includes(job.stage) && (
                            <span className="stage-bar" aria-hidden="true">
                              <span
                                style={{
                                  width: `${((INGEST_STAGES.indexOf(job.stage) + 1) / INGEST_STAGES.length) * 100}%`,
                                }}
                              />
                            </span>
                          )}
                        </>
                      )}
                      {job?.status === "retry_wait" && <small>Đang chờ thử lại tự động.</small>}
                      {doc.status === "needs_ocr" && (
                        <small>Hãy sử dụng bản tài liệu có text.</small>
                      )}
                      {doc.status === "deleting" && <small>Đã ngừng dùng để hỏi đáp.</small>}
                      {doc.status === "failed" && (
                        <small>
                          {job?.retryable
                            ? "Có thể thử lại tác vụ."
                            : "Cần kiểm tra hoặc thay tài liệu đầu vào."}
                        </small>
                      )}
                      {warning.length > 0 && (
                        <details className="document-warning">
                          <summary>Có phần chưa đọc đủ</summary>
                          {warning.map((text, i) => (
                            <p key={i}>{text}</p>
                          ))}
                        </details>
                      )}
                    </td>
                    <td data-label="Tải lên">
                      <time dateTime={doc.created_at}>{formatDate(doc.created_at)}</time>
                    </td>
                    <td>
                      <div className="row-actions">
                        {admin && !["deleting", "deleted"].includes(doc.status) && (
                          <button
                            className="text-button"
                            disabled={folders.loading || Boolean(folders.error)}
                            onClick={() => setMove(doc)}
                          >
                            Chuyển thư mục
                          </button>
                        )}
                        {doc.status === "ready" && (
                          <button
                            className="text-button"
                            onClick={() =>
                              openSource({ documentId: doc.id, filename: doc.filename })
                            }
                          >
                            <Eye size={15} aria-hidden="true" />
                            Xem
                          </button>
                        )}
                        {admin && retryable && job && (
                          <button
                            className="text-button"
                            disabled={busy !== null}
                            onClick={() => void retry(job)}
                          >
                            <RotateCw size={15} aria-hidden="true" />
                            {busy === job.id
                              ? "Đang gửi…"
                              : job.kind === "cleanup"
                                ? "Thử lại dọn dẹp"
                                : "Thử lại"}
                          </button>
                        )}
                        {admin && !["deleting", "deleted"].includes(doc.status) && (
                          <button
                            className="text-button destructive"
                            onClick={() => setRemove(doc)}
                          >
                            <Trash2 size={15} aria-hidden="true" />
                            Xóa
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          <p className="hint">
            Chỉ tài liệu sẵn sàng được dùng để hỏi đáp. Tài liệu đang xóa không còn được dùng, kể cả
            khi dọn dẹp chưa hoàn tất.
          </p>
        </>
      )}
      {upload && (
        <UploadDialog
          folders={folders.items}
          initialFolderId={folderId}
          onClose={() => setUpload(false)}
          onDone={(text) => {
            setUpload(false);
            setNotice(text);
            documents.refresh();
          }}
        />
      )}
      {folderAction && (
        <FolderDialog
          action={folderAction}
          onClose={() => setFolderAction(null)}
          onDone={() => {
            if (folderAction.kind === "delete" && folderAction.folder.id === folderId)
              setFolderId("");
            setFolderAction(null);
            setNotice("Đã cập nhật thư mục.");
            documents.refresh();
          }}
        />
      )}
      {move && (
        <MoveDocumentDialog
          document={move}
          folders={folders.items}
          onClose={() => setMove(null)}
          onDone={() => {
            setMove(null);
            setNotice("Đã cập nhật thư mục của tài liệu.");
            documents.refresh();
          }}
        />
      )}
      {remove && (
        <DeleteDialog
          key={remove.id}
          document={remove}
          onClose={() => setRemove(null)}
          onDone={() => {
            setRemove(null);
            setNotice(
              "Đã yêu cầu xóa và ngừng dùng tài liệu. Dữ liệu liên quan đang được dọn dẹp.",
            );
            documents.refresh();
          }}
        />
      )}
    </section>
  );
}
