import { describe, expect, it } from "vitest";
import { answerText } from "./AnswerView";
import { answer } from "../../test/fixtures";
import { clock } from "../../hooks/useElapsed";
import { progressText } from "../../pages/DocumentsPage";
import { groupSessions } from "../../pages/HistoryPage";
import type { Job } from "../../api/types";

describe("plain-text helpers", () => {
  it("copies claims with numbered sources and the AI label", () => {
    expect(answerText(answer)).toBe(
      [
        "- A supported claim. [1]",
        "",
        "Nguồn:",
        "[1] policy.pdf, Trang 2",
        "",
        "(Câu trả lời do AI tạo, hãy kiểm tra nguồn.)",
      ].join("\n"),
    );
  });
  it("formats elapsed seconds as m:ss", () => {
    expect(clock(0)).toBe("0:00");
    expect(clock(38)).toBe("0:38");
    expect(clock(125)).toBe("2:05");
  });
  it("describes ingest progress only from real job fields", () => {
    const job: Job = {
      id: "j",
      document_id: "d",
      kind: "ingest",
      status: "running",
      stage: "embed",
      attempts: 1,
      retryable: false,
      error_code: null,
      progress: { completed_units: 8, total_units: 14, unit: "chunks" },
    };
    expect(progressText(job)).toBe("Bước 4/6 · Lập chỉ mục · 8/14 đoạn");
    expect(progressText({ ...job, stage: "parse", progress: null })).toBe(
      "Bước 2/6 · Đọc nội dung",
    );
    expect(progressText({ ...job, stage: "unknown", progress: null })).toBe("Đang xử lý tài liệu");
  });
  it("groups sessions by Vietnam calendar day", () => {
    const now = Date.parse("2026-11-13T02:00:00Z"); // 09:00 on 13/11 in Asia/Ho_Chi_Minh
    const groups = groupSessions(
      [
        { id: "a", title: "today", created_at: "2026-11-12T18:30:00Z" }, // 01:30 on 13/11 VN
        { id: "b", title: "week", created_at: "2026-11-12T16:00:00Z" }, // 23:00 on 12/11 VN
        { id: "c", title: "old", created_at: "2026-10-01T00:00:00Z" },
      ],
      now,
    );
    expect(groups.map((g) => [g.label, g.items.map((i) => i.id)])).toEqual([
      ["Hôm nay", ["a"]],
      ["7 ngày qua", ["b"]],
      ["Cũ hơn", ["c"]],
    ]);
  });
});
