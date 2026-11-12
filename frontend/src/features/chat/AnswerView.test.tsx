import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { it, expect, vi } from "vitest";
import { AnswerView } from "./AnswerView";
import { answer, citation } from "../../test/fixtures";
it("opens backend citations and renders untrusted strings as text", async () => {
  const open = vi.fn();
  render(
    <AnswerView
      answer={{
        ...answer,
        claims: [{ text: '<img src=x onerror="attack()">', evidence_ids: ["E1"] }],
      }}
      onSource={open}
    />,
  );
  expect(screen.getByText('<img src=x onerror="attack()">')).toBeTruthy();
  expect(document.querySelector("img")).toBeNull();
  await userEvent.click(screen.getByRole("button", { name: "Mở nguồn E1" }));
  expect(open).toHaveBeenCalledWith(citation);
  expect(screen.getByText("AI-generated")).toBeTruthy();
});
it("separates partial support from missing information", () => {
  render(
    <AnswerView
      answer={{
        ...answer,
        answer_status: "partial",
        missing_information: ["Approver missing"],
        limitations: ["Only one policy available"],
      }}
      onSource={vi.fn()}
    />,
  );
  expect(screen.getByText("A supported claim.")).toBeTruthy();
  expect(screen.getByText("Approver missing")).toBeTruthy();
  expect(screen.getByText("Một phần thông tin còn thiếu")).toBeTruthy();
});
it("never shows cached text or citations for a revoked answer", () => {
  render(<AnswerView answer={{ ...answer, source_unavailable: true }} onSource={vi.fn()} />);
  expect(screen.queryByText("A supported claim.")).toBeNull();
  expect(screen.queryByRole("button", { name: "Mở nguồn E1" })).toBeNull();
});
it("distinguishes abstention from malformed citations", () => {
  const { rerender } = render(
    <AnswerView
      answer={{ ...answer, answer_status: "insufficient_evidence", claims: [], citations: [] }}
      onSource={vi.fn()}
    />,
  );
  expect(screen.getByText("Chưa đủ bằng chứng trong tài liệu")).toBeTruthy();
  rerender(<AnswerView answer={{ ...answer, citations: [] }} onSource={vi.fn()} />);
  expect(screen.queryByText("A supported claim.")).toBeNull();
  expect(screen.getByRole("alert")).toBeTruthy();
});
it("numbers citations by backend order and labels grounding without a score", () => {
  const second = { ...citation, evidence_id: "E2", chunk_id: "chunk-2", excerpt: "Second text." };
  render(
    <AnswerView
      answer={{
        ...answer,
        claims: [{ text: "Claim.", evidence_ids: ["E2", "E1"] }],
        citations: [citation, second],
      }}
      onSource={vi.fn()}
    />,
  );
  expect(screen.getByRole("button", { name: "Mở nguồn E1" }).firstChild?.textContent).toBe("1");
  expect(screen.getByRole("button", { name: "Mở nguồn E2" }).firstChild?.textContent).toBe("2");
  expect(screen.getByText("Có nguồn dẫn")).toBeTruthy();
  expect(document.body.textContent).not.toMatch(/\d+\s*%/);
});
it("shows a partial badge, and no grounding badge for abstention", () => {
  const { rerender } = render(
    <AnswerView answer={{ ...answer, answer_status: "partial" }} onSource={vi.fn()} />,
  );
  expect(screen.getByText("Trả lời một phần")).toBeTruthy();
  rerender(
    <AnswerView
      answer={{ ...answer, answer_status: "insufficient_evidence", claims: [], citations: [] }}
      onSource={vi.fn()}
    />,
  );
  expect(screen.queryByText("Có nguồn dẫn")).toBeNull();
  expect(screen.queryByText("Trả lời một phần")).toBeNull();
});
