import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Pencil, Trash2 } from "lucide-react";
import type { ChatSession } from "../../api/types";
import { useWorkspace } from "../../workspace/WorkspaceProvider";
import { DeleteSessionDialog, RenameSessionDialog } from "./SessionDialogs";

type Pending = { kind: "rename" | "delete"; session: ChatSession } | null;

/** Rename/delete buttons plus their dialogs; shared by the sidebar and the history page. */
export function useSessionActions(onNotice?: (text: string) => void) {
  const [pending, setPending] = useState<Pending>(null);
  const workspace = useWorkspace();
  const navigate = useNavigate();
  const location = useLocation();
  const close = () => setPending(null);
  const buttons = (session: ChatSession) => (
    <span className="session-actions">
      <button
        type="button"
        className="icon-button small"
        aria-label={`Đổi tên “${session.title}”`}
        title="Đổi tên"
        onClick={() => setPending({ kind: "rename", session })}
      >
        <Pencil size={15} aria-hidden="true" />
      </button>
      <button
        type="button"
        className="icon-button small danger"
        aria-label={`Xóa “${session.title}”`}
        title="Xóa"
        onClick={() => setPending({ kind: "delete", session })}
      >
        <Trash2 size={15} aria-hidden="true" />
      </button>
    </span>
  );
  const dialogs =
    pending?.kind === "rename" ? (
      <RenameSessionDialog
        key={pending.session.id}
        session={pending.session}
        onClose={close}
        onDone={(saved) => {
          close();
          workspace.refreshSessions();
          onNotice?.(`Đã đổi tên thành “${saved.title}”.`);
        }}
      />
    ) : pending?.kind === "delete" ? (
      <DeleteSessionDialog
        key={pending.session.id}
        session={pending.session}
        onClose={close}
        onDone={(removed) => {
          close();
          workspace.refreshSessions();
          if (location.pathname === `/chat/${encodeURIComponent(removed.id)}`)
            navigate("/chat", { replace: true });
          onNotice?.(`Đã xóa cuộc trò chuyện “${removed.title}”.`);
        }}
      />
    ) : null;
  return { buttons, dialogs };
}
