import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { it, expect, vi } from "vitest";
import { DeleteDialog, UploadDialog } from "./DocumentDialogs";
import { storeSession } from "../../auth/session";
import { doc, failure, ok, token } from "../../test/fixtures";
it("requires an exact filename before destructive submission", async () => {
  storeSession(token, 3600);
  const transport = vi.fn(async () =>
    ok({ status: "deleting", document_id: doc.id, job_id: "cleanup-1" }),
  );
  vi.stubGlobal("fetch", transport);
  const done = vi.fn();
  render(<DeleteDialog document={doc} onClose={vi.fn()} onDone={done} />);
  const confirm = screen.getByRole("button", { name: "Xóa tài liệu" });
  expect((confirm as HTMLButtonElement).disabled).toBe(true);
  await userEvent.type(screen.getByLabelText("Nhập đúng tên tài liệu để xác nhận"), "wrong.pdf");
  expect((confirm as HTMLButtonElement).disabled).toBe(true);
  await userEvent.clear(screen.getByLabelText("Nhập đúng tên tài liệu để xác nhận"));
  await userEvent.type(screen.getByLabelText("Nhập đúng tên tài liệu để xác nhận"), doc.filename);
  await userEvent.click(confirm);
  await waitFor(() => expect(done).toHaveBeenCalledTimes(1));
  expect(transport.mock.calls).toHaveLength(1);
});
it("rejects unsupported uploads before contacting the API", async () => {
  storeSession(token, 3600);
  const transport = vi.fn();
  vi.stubGlobal("fetch", transport);
  render(<UploadDialog onClose={vi.fn()} onDone={vi.fn()} />);
  const file = new File(["fake"], "malware.exe", { type: "application/octet-stream" });
  await userEvent.upload(screen.getByLabelText("Chọn hoặc thả một tài liệu"), file, {
    applyAccept: false,
  });
  expect(await screen.findByText("Chọn file PDF, DOCX, TXT hoặc MD.")).toBeTruthy();
  expect(transport).not.toHaveBeenCalled();
});
it("shows duplicate-document recovery instead of a fake success", async () => {
  storeSession(token, 3600);
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => failure(409, "duplicate_document", { document_id: doc.id })),
  );
  const done = vi.fn();
  render(<UploadDialog onClose={vi.fn()} onDone={done} />);
  await userEvent.upload(
    screen.getByLabelText("Chọn hoặc thả một tài liệu"),
    new File(["policy"], "policy.txt", { type: "text/plain" }),
  );
  await userEvent.click(screen.getByRole("button", { name: "Tải tài liệu" }));
  expect(
    await screen.findByRole("link", { name: "Xem tài liệu đã có trong danh sách" }),
  ).toBeTruthy();
  expect(done).not.toHaveBeenCalled();
});
it("omits folder_id for an unclassified upload", async () => {
  storeSession(token, 3600);
  const fetcher = vi.fn<(path: string, init?: RequestInit) => Promise<Response>>(async () =>
    ok({ document_id: "new", job_id: "job", status: "queued" }),
  );
  vi.stubGlobal("fetch", fetcher);
  const done = vi.fn();
  render(<UploadDialog onClose={vi.fn()} onDone={done} />);
  await userEvent.upload(
    screen.getByLabelText("Chọn hoặc thả một tài liệu"),
    new File(["synthetic"], "file.txt", { type: "text/plain" }),
  );
  await userEvent.click(screen.getByRole("button", { name: "Tải tài liệu" }));
  await waitFor(() => expect(done).toHaveBeenCalledOnce());
  expect((fetcher.mock.calls[0][1]!.body as FormData).has("folder_id")).toBe(false);
});
it("focuses the safe cancel button when the delete dialog opens", () => {
  storeSession(token, 3600);
  render(<DeleteDialog document={doc} onClose={vi.fn()} onDone={vi.fn()} />);
  expect(document.activeElement).toBe(screen.getByRole("button", { name: "Hủy" }));
});
