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
import { errorMessage, isAbort } from "../api/client";
import type { User } from "../api/types";
import { AUTH_EXPIRED, clearSession, readSession, storeSession } from "./session";

interface AuthState {
  user: User | null;
  loading: boolean;
  error: string;
  expired: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  /** User-initiated sign-out: revoke the token on the server, then clear the tab. */
  signOut: () => Promise<void>;
  revalidate: () => void;
}
const Context = createContext<AuthState | null>(null);
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(Boolean(readSession()));
  const [error, setError] = useState("");
  const [expired, setExpired] = useState(false);
  const controller = useRef<AbortController | null>(null);
  const currentUser = useRef<User | null>(null);
  const logout = useCallback(() => {
    controller.current?.abort();
    currentUser.current = null;
    clearSession();
    setUser(null);
    setLoading(false);
    setError("");
  }, []);
  const signOut = useCallback(async () => {
    controller.current?.abort();
    if (readSession()) {
      try {
        await api.logout();
      } catch {
        /* Local sign-out still proceeds; the token then expires on its own TTL. */
      }
    }
    logout();
  }, [logout]);
  const revalidate = useCallback(() => {
    controller.current?.abort();
    if (!readSession()) {
      currentUser.current = null;
      setUser(null);
      setLoading(false);
      return;
    }
    const next = new AbortController();
    controller.current = next;
    setLoading(currentUser.current === null);
    setError("");
    api
      .me(next.signal)
      .then((result) => {
        if (next.signal.aborted) return;
        if (result.role !== "member" && result.role !== "knowledge_admin") {
          logout();
          setError("Tài khoản không có quyền truy cập ứng dụng.");
          return;
        }
        currentUser.current = result;
        setUser(result);
      })
      .catch((e) => {
        if (!isAbort(e)) {
          currentUser.current = null;
          setUser(null);
          setError(errorMessage(e));
        }
      })
      .finally(() => {
        if (!next.signal.aborted) setLoading(false);
      });
  }, [logout]);
  useEffect(() => {
    revalidate();
    const expiredSession = () => {
      logout();
      setExpired(true);
    };
    const focus = () => {
      if (readSession()) revalidate();
      else if (currentUser.current) expiredSession();
    };
    window.addEventListener(AUTH_EXPIRED, expiredSession);
    window.addEventListener("focus", focus);
    return () => {
      controller.current?.abort();
      window.removeEventListener(AUTH_EXPIRED, expiredSession);
      window.removeEventListener("focus", focus);
    };
  }, [revalidate, logout]);
  useEffect(() => {
    if (!user) return;
    const expires = readSession()?.expiresAt;
    if (!expires) return;
    const timer = setTimeout(
      () => {
        logout();
        setExpired(true);
      },
      Math.max(0, expires - Date.now()),
    );
    return () => clearTimeout(timer);
  }, [user, logout]);
  const login = async (username: string, password: string) => {
    controller.current?.abort();
    const next = new AbortController();
    controller.current = next;
    const result = await api.login(username.trim().toLowerCase(), password, next.signal);
    if (next.signal.aborted) return;
    clearSession();
    storeSession(result.access_token, result.expires_in);
    try {
      const account = await api.me(next.signal);
      if (!next.signal.aborted) {
        currentUser.current = account;
        setUser(account);
        setError("");
        setExpired(false);
        setLoading(false);
      }
    } catch (e) {
      if (!next.signal.aborted) clearSession();
      throw e;
    }
  };
  return (
    <Context.Provider value={{ user, loading, error, expired, login, logout, signOut, revalidate }}>
      {children}
    </Context.Provider>
  );
}
export function useAuth() {
  const state = useContext(Context);
  if (!state) throw new Error("Missing AuthProvider");
  return state;
}
