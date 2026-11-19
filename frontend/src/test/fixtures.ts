/** Synthetic test-only fixtures. Never imported by the production app. */
import type { Answer, ChatMessage, KnowledgeDocument } from "../api/types";
export const token = "a".repeat(43);
export const user = {
  id: "user-1",
  workspace_id: "ws-1",
  username: "demo.admin",
  display_name: "Test User",
  role: "knowledge_admin",
};
export const doc: KnowledgeDocument = {
  id: "doc-1",
  folder_id: null,
  filename: "policy.pdf",
  mime: "application/pdf",
  size_bytes: 1234,
  status: "ready",
  active_revision_id: "rev-1",
  created_at: "2026-11-05T01:00:00Z",
  latest_job_id: null,
  warnings: [],
};
export const citation = {
  evidence_id: "E1",
  document_id: "doc-1",
  chunk_id: "chunk-1",
  file_name: "policy.pdf",
  location: { page_start: 2, page_end: 2 },
  excerpt: "Verified source text.",
};
export const answer: Answer = {
  run_id: "run-1",
  session_id: "session-1",
  message_id: "answer-1",
  status: "completed",
  answer_status: "grounded",
  claims: [{ text: "A supported claim.", evidence_ids: ["E1"] }],
  citations: [citation],
  limitations: [],
  missing_information: [],
  source_unavailable: false,
};
export const messages: ChatMessage[] = [
  {
    id: "q-1",
    role: "user",
    content: "A question",
    query_run_id: "run-1",
    source_unavailable: false,
    answer: null,
    created_at: "2026-11-05T01:00:00Z",
  },
  {
    id: "answer-1",
    role: "assistant",
    content: "Never use this fallback",
    query_run_id: "run-1",
    source_unavailable: false,
    answer,
    created_at: "2026-11-05T01:00:01Z",
  },
];
export function ok(data: unknown) {
  return new Response(JSON.stringify({ data, request_id: "req-test" }), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}
export function failure(status: number, code: string, details?: Record<string, unknown>) {
  return new Response(
    JSON.stringify({ error: { code, message: "Test failure", details }, request_id: "req-test" }),
    { status, headers: { "Content-Type": "application/json" } },
  );
}
export function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((r) => {
    resolve = r;
  });
  return { promise, resolve };
}
