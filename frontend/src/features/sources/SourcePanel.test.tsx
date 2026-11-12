import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { it, expect, vi } from "vitest";
import { SourcePanel } from "./SourcePanel";
import { documentChanged, storeSession } from "../../auth/session";
import { citation, doc, failure, ok, token } from "../../test/fixtures";
it("clears revoked excerpts immediately on document invalidation", async () => {
  storeSession(token, 3600);
  let revoked = false;
  vi.stubGlobal(
    "fetch",
    vi.fn(async (path: string) =>
      revoked
        ? failure(410, "source_unavailable")
        : path.includes("/chunks/")
          ? ok({ ...citation, text: "Private original excerpt" })
          : ok(doc),
    ),
  );
  render(
    <SourcePanel
      target={{ documentId: doc.id, chunkId: "chunk-1", filename: doc.filename }}
      onClose={vi.fn()}
    />,
  );
  await screen.findByText("Private original excerpt");
  revoked = true;
  act(() => documentChanged(doc.id));
  expect(screen.queryByText("Private original excerpt")).toBeNull();
  await screen.findByText("Nguồn không còn khả dụng");
  expect(screen.queryByText(doc.filename)).toBeNull();
});
it("revokes PDF URLs when the source closes", async () => {
  storeSession(token, 3600);
  vi.stubGlobal(
    "fetch",
    vi.fn(async (path: string) =>
      path.endsWith("/content")
        ? new Response("%PDF-1.7 fake-test-bytes", {
            headers: { "Content-Type": "application/pdf" },
          })
        : ok(doc),
    ),
  );
  const { unmount } = render(
    <SourcePanel target={{ documentId: doc.id, filename: doc.filename }} onClose={vi.fn()} />,
  );
  await screen.findByTitle(`Nội dung ${doc.filename}`);
  expect(URL.createObjectURL).toHaveBeenCalledTimes(1);
  unmount();
  expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:local-test");
});
it("does not use snapshot source URLs from citations", async () => {
  storeSession(token, 3600);
  const transport = vi.fn(async (path: string) =>
    path.includes("/chunks/") ? ok({ ...citation, text: "Checked excerpt" }) : ok(doc),
  );
  vi.stubGlobal("fetch", transport);
  render(
    <SourcePanel
      target={{ documentId: "doc-1", chunkId: "chunk-1", filename: "untrusted title" }}
      onClose={vi.fn()}
    />,
  );
  await screen.findByText("Checked excerpt");
  await userEvent.click(screen.getByRole("button", { name: "Đóng" }));
  await waitFor(() =>
    expect(transport.mock.calls.every(([p]) => p.startsWith("/api/v1/documents/doc-1"))).toBe(true),
  );
});
