import { useState } from "react";
import { Funnel, X } from "lucide-react";
import type { Folder, KnowledgeDocument } from "../../api/types";
export function ScopePicker({
  documents,
  folders,
  selected,
  selectedFolders,
  setSelected,
  setSelectedFolders,
  disabled,
  documentCount,
}: {
  documents: KnowledgeDocument[];
  folders: Folder[];
  selected: string[];
  selectedFolders: string[];
  setSelected: (ids: string[]) => void;
  setSelectedFolders: (ids: string[]) => void;
  disabled: boolean;
  documentCount: number;
}) {
  const [tab, setTab] = useState<"documents" | "folders">("documents");
  const summary = [
    selectedFolders.length ? `${selectedFolders.length} thư mục` : "",
    selected.length ? `${selected.length} tài liệu` : "",
  ]
    .filter(Boolean)
    .join(" · ");
  return (
    <>
      <details className="document-picker">
        <summary>
          <Funnel size={14} aria-hidden="true" />
          Phạm vi: {summary || "Tất cả tài liệu sẵn sàng"}
        </summary>
        <div className="document-options">
          <div className="scope-tabs" role="group" aria-label="Loại phạm vi">
            <button
              type="button"
              className="filter-chip"
              aria-pressed={tab === "documents"}
              onClick={() => setTab("documents")}
            >
              Tài liệu
            </button>
            <button
              type="button"
              className="filter-chip"
              aria-pressed={tab === "folders"}
              onClick={() => setTab("folders")}
            >
              Thư mục
            </button>
          </div>
          <label>
            <input
              type="checkbox"
              checked={!selected.length && !selectedFolders.length}
              disabled={disabled}
              onChange={() => {
                setSelected([]);
                setSelectedFolders([]);
              }}
            />
            Tất cả tài liệu sẵn sàng
          </label>
          <p className="hint">
            Chọn nhiều thư mục để gộp nguồn. Nếu chọn thêm tài liệu, chỉ hỏi trong phần giao của hai
            lựa chọn.
          </p>
          {tab === "documents" ? (
            <>
              {documents.map((doc) => (
                <label key={doc.id}>
                  <input
                    type="checkbox"
                    checked={selected.includes(doc.id)}
                    disabled={disabled || (selected.length >= 50 && !selected.includes(doc.id))}
                    onChange={(e) =>
                      setSelected(
                        e.target.checked
                          ? [...selected, doc.id]
                          : selected.filter((id) => id !== doc.id),
                      )
                    }
                  />
                  <span>{doc.filename}</span>
                </label>
              ))}
              {!documents.length && <p className="hint">Chưa có tài liệu sẵn sàng.</p>}
              {selected.length >= 50 && <p className="hint">Đã đạt giới hạn 50 tài liệu.</p>}
              {documentCount === 100 && (
                <p className="hint">
                  Bộ chọn hiện hiển thị trong 100 tài liệu đã tải. “Tất cả” vẫn tìm trên toàn bộ tài
                  liệu sẵn sàng của workspace.
                </p>
              )}
            </>
          ) : (
            <>
              {folders.map((folder) => (
                <label key={folder.id}>
                  <input
                    type="checkbox"
                    checked={selectedFolders.includes(folder.id)}
                    disabled={
                      disabled ||
                      (selectedFolders.length >= 20 && !selectedFolders.includes(folder.id))
                    }
                    onChange={(e) =>
                      setSelectedFolders(
                        e.target.checked
                          ? [...selectedFolders, folder.id]
                          : selectedFolders.filter((id) => id !== folder.id),
                      )
                    }
                  />
                  <span>
                    {folder.name} <small>· {folder.ready_document_count} tài liệu sẵn sàng</small>
                  </span>
                </label>
              ))}
              {!folders.length && <p className="hint">Chưa có thư mục để chọn.</p>}
              {selectedFolders.length >= 20 && <p className="hint">Đã đạt giới hạn 20 thư mục.</p>}
              <p className="hint">
                Thư mục không có tài liệu sẵn sàng sẽ không cung cấp bằng chứng.
              </p>
            </>
          )}
        </div>
      </details>
      {Boolean(selected.length || selectedFolders.length) && (
        <ul className="scope-chips" aria-label="Nguồn đang hỏi">
          {selectedFolders.map((id) => {
            const name =
              folders.find((f) => f.id === id)?.name ?? "Thư mục không còn trong danh sách";
            return (
              <li key={`folder-${id}`}>
                <span>Thư mục: {name}</span>
                <button
                  type="button"
                  aria-label={`Bỏ thư mục ${name} khỏi phạm vi`}
                  disabled={disabled}
                  onClick={() => setSelectedFolders(selectedFolders.filter((key) => key !== id))}
                >
                  <X size={14} aria-hidden="true" />
                </button>
              </li>
            );
          })}
          {selected.map((id) => {
            const name =
              documents.find((d) => d.id === id)?.filename ?? "Tài liệu không còn trong danh sách";
            return (
              <li key={id}>
                <span>{name}</span>
                <button
                  type="button"
                  aria-label={`Bỏ ${name} khỏi phạm vi`}
                  disabled={disabled}
                  onClick={() => setSelected(selected.filter((key) => key !== id))}
                >
                  <X size={14} aria-hidden="true" />
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </>
  );
}
