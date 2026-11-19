import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../../api";
import { isAbort } from "../../api/client";
import type { Folder } from "../../api/types";
import { DOCUMENT_CHANGED } from "../../auth/session";

export const FOLDER_CHANGED = "sme:folder-changed";
export function foldersChanged() {
  window.dispatchEvent(new Event(FOLDER_CHANGED));
}
export function useFolders() {
  const [items, setItems] = useState<Folder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const controller = useRef<AbortController | null>(null);
  const refresh = useCallback(() => {
    controller.current?.abort();
    const next = new AbortController();
    controller.current = next;
    api
      .folders(next.signal)
      .then((result) => {
        if (!next.signal.aborted) {
          setItems(result.items);
          setError(null);
        }
      })
      .catch((e) => {
        if (!isAbort(e)) setError(e);
      })
      .finally(() => {
        if (!next.signal.aborted) setLoading(false);
      });
  }, []);
  useEffect(() => {
    refresh();
    window.addEventListener("focus", refresh);
    window.addEventListener(FOLDER_CHANGED, refresh);
    window.addEventListener(DOCUMENT_CHANGED, refresh);
    return () => {
      controller.current?.abort();
      window.removeEventListener("focus", refresh);
      window.removeEventListener(FOLDER_CHANGED, refresh);
      window.removeEventListener(DOCUMENT_CHANGED, refresh);
    };
  }, [refresh]);
  return { items, loading, error, refresh };
}
