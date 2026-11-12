import type { ChatQuery } from "../../api/types";
export interface PendingQuery {
  payload: ChatQuery;
  runId?: string;
  startedAt: number;
}
const prefix = (user: string, session: string) => `sme.pending.${user}.${session}`;
const memory = new Map<string, PendingQuery>();
window.addEventListener("sme:session-cleared", () => memory.clear());
export function savePending(user: string, session: string, pending: PendingQuery | null) {
  if (pending) memory.set(prefix(user, session), pending);
  else memory.delete(prefix(user, session));
  try {
    if (pending) sessionStorage.setItem(prefix(user, session), JSON.stringify(pending));
    else sessionStorage.removeItem(prefix(user, session));
  } catch {
    /* Recovery remains available in the mounted tab. */
  }
}
export function readPending(user: string, session: string): PendingQuery | null {
  try {
    const raw = sessionStorage.getItem(prefix(user, session));
    const value = (
      raw ? JSON.parse(raw) : (memory.get(prefix(user, session)) ?? null)
    ) as PendingQuery | null;
    if (
      value &&
      value.payload.session_id === session &&
      typeof value.payload.client_request_id === "string" &&
      typeof value.payload.question === "string" &&
      value.payload.question.length <= 4000 &&
      Array.isArray(value.payload.filters.document_ids) &&
      value.payload.filters.document_ids.every((id) => typeof id === "string") &&
      Date.now() - value.startedAt < 10 * 60 * 1000
    )
      return value;
  } catch {
    const value = memory.get(prefix(user, session));
    if (value && Date.now() - value.startedAt < 10 * 60 * 1000) return value;
  }
  savePending(user, session, null);
  return null;
}
