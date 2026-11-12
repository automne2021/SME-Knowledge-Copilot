const KEY = "sme.auth.v1";
export const AUTH_EXPIRED = "sme:auth-expired";
export const DOCUMENT_CHANGED = "sme:document-changed";
export interface StoredSession {
  token: string;
  expiresAt: number;
}
let memory: StoredSession | null = null;

export function readSession(): StoredSession | null {
  try {
    const raw = sessionStorage.getItem(KEY);
    if (raw) {
      const parsed = JSON.parse(raw) as StoredSession;
      if (
        typeof parsed.token === "string" &&
        /^[A-Za-z0-9_-]{43}$/.test(parsed.token) &&
        Number.isFinite(parsed.expiresAt)
      )
        memory = parsed;
      else {
        memory = null;
        sessionStorage.removeItem(KEY);
      }
    }
  } catch (error) {
    if (error instanceof SyntaxError) {
      memory = null;
      try {
        sessionStorage.removeItem(KEY);
      } catch {
        /* Storage unavailable. */
      }
    }
  }
  if (memory && memory.expiresAt <= Date.now()) {
    clearSession();
    return null;
  }
  return memory;
}
export function storeSession(token: string, ttl: number) {
  memory = { token, expiresAt: Date.now() + ttl * 1000 };
  try {
    sessionStorage.setItem(KEY, JSON.stringify(memory));
  } catch {
    /* Tab memory remains usable. */
  }
}
export function clearSession() {
  memory = null;
  try {
    sessionStorage.removeItem(KEY);
    Object.keys(sessionStorage)
      .filter((k) => k.startsWith("sme.pending."))
      .forEach((k) => sessionStorage.removeItem(k));
  } catch {
    /* No persistent storage. */
  }
  window.dispatchEvent(new Event("sme:session-cleared"));
}
export function expireSession(token: string) {
  if (readSession()?.token === token) {
    clearSession();
    window.dispatchEvent(new Event(AUTH_EXPIRED));
  }
}
export function documentChanged(id: string) {
  window.dispatchEvent(new CustomEvent(DOCUMENT_CHANGED, { detail: id }));
}
