import type { KnowledgeDocument, SourceLocation } from "../api/types";
export function formatDate(value: string) {
  return new Intl.DateTimeFormat("vi-VN", {
    dateStyle: "short",
    timeStyle: "short",
    timeZone: "Asia/Ho_Chi_Minh",
  }).format(new Date(value));
}
export function fileSize(size: number) {
  return size >= 1024 ** 2
    ? `${(size / 1024 ** 2).toFixed(1)} MB`
    : `${Math.max(1, Math.round(size / 1024))} KB`;
}
export function sourceLocation(location?: SourceLocation) {
  if (!location) return "Vị trí nguồn";
  for (const [axis, label] of [
    ["page", "Trang"],
    ["line", "Dòng"],
    ["block", "Đoạn"],
    ["row", "Hàng"],
  ] as const) {
    const start = location[`${axis}_start`],
      end = location[`${axis}_end`];
    if (typeof start === "number")
      return `${label} ${start}${end && end !== start ? `–${end}` : ""}`;
  }
  return "Trích đoạn nguồn";
}
export function warningsFor(doc: KnowledgeDocument) {
  return doc.warnings.map((w) =>
    w.skipped_pages?.length
      ? `Một số trang scan chưa được đọc: ${w.skipped_pages.join(", ")}.`
      : "Tài liệu có phần chưa được xử lý đầy đủ.",
  );
}
/** Ordered ingest stages reported by the worker; used only to draw progress from real job.stage. */
export const INGEST_STAGES = ["validate", "parse", "chunk", "embed", "upsert", "publish"];
export function fileKind(filename: string) {
  return (filename.split(".").pop() ?? "").toUpperCase().slice(0, 4) || "FILE";
}
export const stageLabel: Record<string, string> = {
  validate: "Kiểm tra tài liệu",
  parse: "Đọc nội dung",
  chunk: "Chuẩn bị nội dung",
  embed: "Lập chỉ mục",
  upsert: "Lưu chỉ mục",
  publish: "Hoàn tất",
  cleanup: "Dọn dữ liệu",
  delete_vectors: "Dọn chỉ mục",
  delete_files: "Dọn file",
  delete_sql: "Dọn nội dung",
};
