import type { ReactNode } from "react";
import { CircleExclamationPoint, Info, LoaderCircle } from "lucide-react";
import { ApiError, errorMessage } from "../../api/client";
const icons = { info: Info, warning: CircleExclamationPoint, error: CircleExclamationPoint };
export function Feedback({
  title,
  children,
  kind = "info",
  action,
}: {
  title: string;
  children?: ReactNode;
  kind?: "info" | "error" | "warning";
  action?: ReactNode;
}) {
  const Icon = icons[kind];
  return (
    <div className={`feedback feedback-${kind}`} role={kind === "error" ? "alert" : "status"}>
      <Icon className="feedback-icon" size={18} aria-hidden="true" />
      <div className="feedback-content">
        <h3>{title}</h3>
        {children && <div className="feedback-body">{children}</div>}
        {action && <div className="feedback-actions">{action}</div>}
      </div>
    </div>
  );
}
export function ErrorFeedback({ error, retry }: { error: unknown; retry?: () => void }) {
  return (
    <Feedback
      title="Chưa thể hoàn tất thao tác"
      kind="error"
      action={
        retry && (
          <button className="button" onClick={retry}>
            Thử lại
          </button>
        )
      }
    >
      <p>{errorMessage(error)}</p>
      {error instanceof ApiError && error.requestId && (
        <details>
          <summary>Thông tin hỗ trợ</summary>
          <p>Mã yêu cầu: {error.requestId}</p>
        </details>
      )}
    </Feedback>
  );
}
export function Loading({ label = "Đang tải…" }: { label?: string }) {
  return (
    <p className="loading" role="status">
      <LoaderCircle className="spin" size={18} aria-hidden="true" />
      {label}
    </p>
  );
}
