import { useEffect, useId, useRef, type ReactNode } from "react";
import { X } from "lucide-react";
interface Props {
  title: string;
  children: ReactNode;
  onClose: () => void;
  busy?: boolean;
  className?: string;
}
export function Dialog({ title, children, onClose, busy = false, className = "" }: Props) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const close = useRef(onClose);
  close.current = onClose;
  useEffect(() => {
    const dialog = ref.current!;
    const previous = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    dialog.showModal();
    // A close event from an earlier close() is queued, not synchronous. Under React StrictMode the
    // effect re-runs and reopens the dialog before that stale event fires, so ignore it while open.
    const closed = () => {
      if (!dialog.open) close.current();
    };
    dialog.addEventListener("close", closed);
    return () => {
      dialog.removeEventListener("close", closed);
      dialog.close();
      if (previous?.isConnected) previous.focus();
    };
  }, []);
  return (
    <dialog
      ref={ref}
      className={`dialog ${className}`}
      aria-labelledby={titleId}
      aria-busy={busy}
      onCancel={(e) => {
        e.preventDefault();
        if (!busy) onClose();
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget && !busy) onClose();
      }}
    >
      <div className="dialog-inner">
        <div className="dialog-header">
          <h2 id={titleId}>{title}</h2>
          <button
            type="button"
            className="icon-button"
            aria-label="Đóng"
            onClick={onClose}
            disabled={busy}
          >
            <X size={18} aria-hidden="true" />
          </button>
        </div>
        {children}
      </div>
    </dialog>
  );
}
