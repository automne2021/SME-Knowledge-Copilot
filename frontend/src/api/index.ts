import { apiBlob, apiFetch } from "./client";
import type {
  Answer,
  ChatMessage,
  ChatQuery,
  ChatSession,
  DocumentOperation,
  Folder,
  Job,
  KnowledgeDocument,
  SourceChunk,
  User,
} from "./types";

const id = encodeURIComponent;
export const api = {
  login: (username: string, password: string, signal?: AbortSignal) =>
    apiFetch<{ access_token: string; expires_in: number }>("/auth/login", {
      auth: false,
      method: "POST",
      body: JSON.stringify({ username, password }),
      signal,
    }),
  me: (signal?: AbortSignal) => apiFetch<User>("/auth/me", { signal }),
  logout: () => apiFetch<{ revoked: boolean }>("/auth/logout", { method: "POST", timeout: 5000 }),
  folders: (signal?: AbortSignal) => apiFetch<{ items: Folder[] }>("/folders", { signal }),
  createFolder: (name: string, signal?: AbortSignal) =>
    apiFetch<Folder>("/folders", { method: "POST", body: JSON.stringify({ name }), signal }),
  renameFolder: (key: string, name: string, signal?: AbortSignal) =>
    apiFetch<Folder>(`/folders/${id(key)}`, {
      method: "PATCH",
      body: JSON.stringify({ name }),
      signal,
    }),
  deleteFolder: (key: string, signal?: AbortSignal) =>
    apiFetch<{ id: string; deleted: boolean }>(`/folders/${id(key)}`, { method: "DELETE", signal }),
  moveDocument: (key: string, folderId: string | null, signal?: AbortSignal) =>
    apiFetch<KnowledgeDocument>(`/documents/${id(key)}`, {
      method: "PATCH",
      body: JSON.stringify({ folder_id: folderId }),
      signal,
    }),
  documents: (signal?: AbortSignal, folderId?: string) =>
    apiFetch<{ items: KnowledgeDocument[] }>(
      `/documents?limit=100${folderId ? `&folder_id=${id(folderId)}` : ""}`,
      { signal },
    ),
  document: (key: string, signal?: AbortSignal) =>
    apiFetch<KnowledgeDocument>(`/documents/${id(key)}`, { signal }),
  job: (key: string, signal?: AbortSignal) => apiFetch<Job>(`/jobs/${id(key)}`, { signal }),
  upload: (file: File, signal?: AbortSignal, folderId?: string) => {
    const data = new FormData();
    data.append("file", file);
    if (folderId) data.append("folder_id", folderId);
    return apiFetch<DocumentOperation>("/documents", {
      method: "POST",
      body: data,
      timeout: 90000,
      signal,
    });
  },
  retry: (key: string, signal?: AbortSignal) =>
    apiFetch<DocumentOperation>(`/jobs/${id(key)}/retry`, { method: "POST", signal }),
  remove: (key: string, signal?: AbortSignal) =>
    apiFetch<DocumentOperation>(`/documents/${id(key)}`, { method: "DELETE", signal }),
  sessions: (signal?: AbortSignal) =>
    apiFetch<{ items: ChatSession[] }>("/chat/sessions?limit=100", { signal }),
  createSession: (title: string, signal?: AbortSignal) =>
    apiFetch<ChatSession>("/chat/sessions", {
      method: "POST",
      body: JSON.stringify({ title }),
      signal,
    }),
  renameSession: (key: string, title: string, signal?: AbortSignal) =>
    apiFetch<ChatSession>(`/chat/sessions/${id(key)}`, {
      method: "PATCH",
      body: JSON.stringify({ title }),
      signal,
    }),
  deleteSession: (key: string, signal?: AbortSignal) =>
    apiFetch<{ id: string; deleted: boolean }>(`/chat/sessions/${id(key)}`, {
      method: "DELETE",
      signal,
    }),
  messages: (key: string, signal?: AbortSignal) =>
    apiFetch<{ items: ChatMessage[] }>(`/chat/sessions/${id(key)}/messages?limit=100`, { signal }),
  query: (payload: ChatQuery, signal?: AbortSignal) =>
    apiFetch<Answer>("/chat/query", {
      method: "POST",
      body: JSON.stringify(payload),
      timeout: 175000,
      signal,
    }),
  run: (key: string, signal?: AbortSignal) => apiFetch<Answer>(`/chat/runs/${id(key)}`, { signal }),
  chunk: (doc: string, chunk: string, signal?: AbortSignal) =>
    apiFetch<SourceChunk>(`/documents/${id(doc)}/chunks/${id(chunk)}`, { signal }),
  content: (doc: string, signal?: AbortSignal) => apiBlob(`/documents/${id(doc)}/content`, signal),
};
