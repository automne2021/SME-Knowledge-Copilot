export type Role = "knowledge_admin" | "member";
export interface User {
  id: string;
  workspace_id: string;
  username: string;
  display_name: string;
  role: Role;
}
export type DocumentStatus =
  "queued" | "processing" | "ready" | "failed" | "needs_ocr" | "deleting" | "deleted";
export interface KnowledgeDocument {
  id: string;
  folder_id: string | null;
  filename: string;
  mime: string;
  size_bytes: number;
  status: DocumentStatus;
  active_revision_id: string | null;
  created_at: string;
  latest_job_id: string | null;
  warnings: { code?: string; skipped_pages?: number[] }[];
}
export interface Job {
  id: string;
  document_id: string;
  kind: "ingest" | "cleanup";
  status: "queued" | "running" | "retry_wait" | "completed" | "failed" | "cancelled";
  stage: string;
  attempts: number;
  retryable: boolean;
  error_code: string | null;
  progress: Record<string, unknown> | null;
}
export interface DocumentOperation {
  document_id: string;
  job_id: string | null;
  status: DocumentStatus;
}
export interface ChatSession {
  id: string;
  title: string;
  created_at: string;
}
export interface SourceLocation {
  kind?: string;
  page_start?: number;
  page_end?: number;
  block_start?: number;
  block_end?: number;
  line_start?: number;
  line_end?: number;
  table?: number;
  row_start?: number;
  row_end?: number;
}
export interface Citation {
  evidence_id: string;
  document_id: string;
  chunk_id: string;
  file_name: string;
  location: SourceLocation;
  excerpt: string;
  content_url?: string;
  chunk_url?: string;
}
export interface Answer {
  run_id: string;
  session_id: string;
  message_id?: string;
  id?: string;
  status: "running" | "completed" | "failed";
  error_code?: string | null;
  source_unavailable?: boolean;
  answer_status?: "grounded" | "partial" | "insufficient_evidence";
  answer?: string;
  claims?: { text: string; evidence_ids: string[] }[];
  citations?: Citation[];
  limitations?: string[];
  missing_information?: string[];
  conflict_detected?: boolean;
  reason_code?: string | null;
}
export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  source_unavailable: boolean;
  query_run_id: string | null;
  answer: Answer | null;
  created_at: string;
}
export interface ChatQuery {
  session_id: string;
  client_request_id: string;
  question: string;
  retrieval_mode: "dense";
  filters: { document_ids: string[]; folder_ids?: string[] };
}
export interface Folder {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
  ready_document_count: number;
}
export interface SourceTarget {
  documentId: string;
  chunkId?: string;
  filename: string;
  location?: SourceLocation;
}
export interface SourceChunk {
  document_id: string;
  chunk_id: string;
  file_name: string;
  text: string;
  location: SourceLocation;
}
