import { useEffect, useRef, useState } from "react";
import {
  CircleCheck,
  CircleExclamationPoint,
  Eye,
  Files,
  LoaderCircle,
  RotateCw,
  Trash,
  Upload,
} from "lucide-react";
import { api } from "../api";
import { isAbort } from "../api/client";
import type { KnowledgeDocument, Job } from "../api/types";
import { useAuth } from "../auth/AuthProvider";
import { useWorkspace } from "../workspace/WorkspaceProvider";
import { ErrorFeedback, Feedback, Loading } from "../components/ui/Feedback";
import { DeleteDialog, UploadDialog } from "../features/documents/DocumentDialogs";
import { useDocuments } from "../features/documents/useDocuments";
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
export default function DocumentsPage() {
  const { user } = useAuth();
  const { openSource } = useWorkspace();
  const documents = useDocuments();
  const admin = user?.role === "knowledge_admin";
  const [upload, setUpload] = useState(false),
    [remove, setRemove] = useState<KnowledgeDocument | null>(null);
  const [notice, setNotice] = useState(""),
    [actionError, setActionError] = useState<unknown>(null),
    [busy, setBusy] = useState<string | null>(null);
  const controller = useRef<AbortController | null>(null);
  useEffect(() => () => controller.current?.abort(), []);
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
          <h2>Chưa có tài liệu</h2>
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
          <div className="stats" aria-label="Tổng quan tài liệu">
            {(
              [
                ["Tổng tài liệu", documents.items.length, Files, ""],
                [
                  "Sẵn sàng",
                  documents.items.filter((d) => d.status === "ready").length,
                  CircleCheck,
                  "ok",
                ],
                [
                  "Đang xử lý",
                  documents.items.filter((d) => ["queued", "processing"].includes(d.status)).length,
                  LoaderCircle,
                  "busy",
                ],
                [
                  "Cần chú ý",
                  documents.items.filter((d) => ["failed", "needs_ocr"].includes(d.status)).length,
                  CircleExclamationPoint,
                  "warn",
                ],
              ] as const
            ).map(([label, value, Icon, tone]) => (
              <div key={label} className={`stat stat-${tone || "total"}`}>
                <Icon size={18} aria-hidden="true" />
                <div>
                  <strong>{value}</strong>
                  <span>{label}</span>
                </div>
              </div>
            ))}
          </div>
          <div className="list-toolbar">
            <span>
              {documents.items.length} tài liệu
              {documents.items.length === 100 && " · Đang hiển thị tối đa 100 tài liệu gần nhất"}
            </span>
            <button className="text-button" onClick={documents.refresh}>
              Làm mới
            </button>
          </div>
          <table className="document-table">
            <thead>
              <tr>
                <th scope="col">Tên tài liệu</th>
                <th scope="col">Trạng thái</th>
                <th scope="col">Tải lên</th>
                <th scope="col">Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {documents.items.map((doc) => {
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
                    <td data-label="Trạng thái">
                      <span className={`status status-${cleanupFailed ? "failed" : doc.status}`}>
                        {cleanupFailed ? "Lỗi dọn dẹp" : statusLabels[doc.status]}
                      </span>
                      {doc.status === "processing" && job && (
                        <>
                          <small>{stageLabel[job.stage] ?? "Đang xử lý tài liệu"}</small>
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
                            <Trash size={15} aria-hidden="true" />
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
          onClose={() => setUpload(false)}
          onDone={(text) => {
            setUpload(false);
            setNotice(text);
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
