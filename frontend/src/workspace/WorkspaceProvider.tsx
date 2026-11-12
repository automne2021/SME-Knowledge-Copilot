import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { api } from "../api";
import { isAbort } from "../api/client";
import type { ChatSession, SourceTarget } from "../api/types";
interface WorkspaceState {
  sessions: ChatSession[];
  sessionError: unknown;
  sessionsLoading: boolean;
  refreshSessions: () => void;
  source: SourceTarget | null;
  openSource: (source: SourceTarget) => void;
  closeSource: () => void;
}
const Context = createContext<WorkspaceState | null>(null);
export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [sessions, setSessions] = useState<ChatSession[]>([]),
    [sessionError, setError] = useState<unknown>(null);
  const [sessionsLoading, setLoading] = useState(true),
    [source, setSource] = useState<SourceTarget | null>(null);
  const controller = useRef<AbortController | null>(null);
  const opener = useRef<HTMLElement | null>(null);
  const openSource = useCallback((target: SourceTarget) => {
    opener.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    setSource(target);
  }, []);
  const closeSource = useCallback(() => {
    setSource(null);
    queueMicrotask(() => {
      if (opener.current?.isConnected) opener.current.focus();
    });
  }, []);
  const refreshSessions = useCallback(() => {
    controller.current?.abort();
    const next = new AbortController();
    controller.current = next;
    setLoading(true);
    setError(null);
    api
      .sessions(next.signal)
      .then((result) => {
        if (!next.signal.aborted) setSessions(result.items);
      })
      .catch((error) => {
        if (!isAbort(error)) setError(error);
      })
      .finally(() => {
        if (!next.signal.aborted) setLoading(false);
      });
  }, []);
  useEffect(() => {
    refreshSessions();
    return () => controller.current?.abort();
  }, [refreshSessions]);
  return (
    <Context.Provider
      value={{
        sessions,
        sessionError,
        sessionsLoading,
        refreshSessions,
        source,
        openSource,
        closeSource,
      }}
    >
      {children}
    </Context.Provider>
  );
}
export function useWorkspace() {
  const value = useContext(Context);
  if (!value) throw new Error("Missing WorkspaceProvider");
  return value;
}
