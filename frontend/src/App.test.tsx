import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { it, expect, vi } from "vitest";
import App from "./App";
import { storeSession } from "./auth/session";
import { answer, citation, doc, failure, messages, ok, token, user } from "./test/fixtures";
function app(path = "/chat") {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );
}
function transport(options: { role?: string; noSources?: boolean; queryFailure?: boolean } = {}) {
  let complete = false;
  return vi.fn(async (path: string, init?: RequestInit) => {
    if (path.endsWith("/auth/me")) return ok({ ...user, role: options.role ?? "knowledge_admin" });
    if (path.endsWith("/auth/login")) return ok({ access_token: token, expires_in: 3600 });
    if (path.includes("/documents?")) return ok({ items: options.noSources ? [] : [doc] });
    if (path.endsWith("/chat/sessions") && init?.method === "POST")
      return ok({ id: "session-1", title: "A question", created_at: doc.created_at });
    if (path.includes("/chat/sessions?"))
      return ok({
        items: complete
          ? [{ id: "session-1", title: "A question", created_at: doc.created_at }]
          : [],
      });
    if (path.includes("/messages?")) return ok({ items: complete ? messages : [] });
    if (path.endsWith("/chat/query")) {
      complete = true;
      return options.queryFailure ? failure(502, "invalid_model_output") : ok(answer);
    }
    if (path.endsWith("/chat/runs/run-1")) return ok(answer);
    if (path.includes("/chunks/")) return ok({ ...citation, text: "Trusted actual source" });
    if (path.endsWith("/documents/doc-1")) return ok(doc);
    throw new Error(`Unhandled fixture endpoint: ${path}`);
  });
}
it("requires login before any document API call", async () => {
  const fetcher = transport();
  vi.stubGlobal("fetch", fetcher);
  app("/documents");
  await screen.findByRole("heading", { name: "Đăng nhập" });
  expect(fetcher).not.toHaveBeenCalled();
});
it("authenticates with server identity and removes tab data on logout", async () => {
  const fetcher = transport();
  vi.stubGlobal("fetch", fetcher);
  app("/login");
  await userEvent.type(screen.getByLabelText("Tên đăng nhập"), "demo.admin");
  await userEvent.type(screen.getByLabelText("Mật khẩu"), "private-test-password");
  await userEvent.click(screen.getByRole("button", { name: "Đăng nhập" }));
  await screen.findByRole("heading", { name: "Hỏi đáp tài liệu" });
  expect(screen.getByText("Quản trị tri thức")).toBeTruthy();
  expect(JSON.stringify(sessionStorage)).not.toContain("private-test-password");
  await userEvent.click(screen.getByRole("button", { name: "Đăng xuất" }));
  await screen.findByRole("heading", { name: "Đăng nhập" });
  expect(sessionStorage.getItem("sme.auth.v1")).toBeNull();
});
it("does not give members write controls", async () => {
  storeSession(token, 3600);
  vi.stubGlobal("fetch", transport({ role: "member" }));
  app("/documents");
  await screen.findByText(doc.filename);
  expect(screen.queryByRole("button", { name: "Tải tài liệu" })).toBeNull();
  expect(screen.queryByRole("button", { name: "Xóa" })).toBeNull();
  expect(screen.getByRole("button", { name: "Xem" })).toBeTruthy();
});
it("opens authenticated source bytes from the document list", async () => {
  storeSession(token, 3600);
  const fetcher = transport();
  vi.stubGlobal(
    "fetch",
    vi.fn(async (path: string, init?: RequestInit) =>
      path.endsWith("/content")
        ? new Response("Text <script> is data", { headers: { "Content-Type": "text/plain" } })
        : fetcher(path, init),
    ),
  );
  app("/documents");
  await screen.findByText(doc.filename);
  await userEvent.click(screen.getByRole("button", { name: "Xem" }));
  await waitFor(() =>
    expect(document.querySelector(".source-panel")?.textContent).toContain("Text <script> is data"),
  );
  expect(document.querySelector("pre script")).toBeNull();
});
it("creates a real session request, queries, and opens the returned citation", async () => {
  storeSession(token, 3600);
  const fetcher = transport();
  vi.stubGlobal("fetch", fetcher);
  app();
  await screen.findByRole("heading", { name: "Hỏi đáp tài liệu" });
  await userEvent.type(screen.getByLabelText("Câu hỏi của bạn"), "A question");
  await userEvent.click(screen.getByRole("button", { name: "Gửi câu hỏi" }));
  await screen.findByText("A supported claim.");
  const call = fetcher.mock.calls.find(([path]) => path.endsWith("/chat/query"));
  expect(JSON.parse(call![1]!.body as string)).toMatchObject({
    session_id: "session-1",
    question: "A question",
    retrieval_mode: "dense",
    filters: { document_ids: [] },
  });
  await userEvent.click(screen.getByRole("button", { name: "Mở nguồn E1" }));
  await screen.findByText("Trusted actual source");
  expect(screen.getAllByText("Trang 2").length).toBeGreaterThan(0);
});
it("preserves an unsent draft when the window regains focus", async () => {
  storeSession(token, 3600);
  vi.stubGlobal("fetch", transport());
  app();
  await screen.findByLabelText("Câu hỏi của bạn");
  await userEvent.type(screen.getByLabelText("Câu hỏi của bạn"), "Unsent text");
  act(() => window.dispatchEvent(new Event("focus")));
  await waitFor(() =>
    expect((screen.getByLabelText("Câu hỏi của bạn") as HTMLTextAreaElement).value).toBe(
      "Unsent text",
    ),
  );
});
it("keeps a technical answering failure distinct from insufficient evidence", async () => {
  storeSession(token, 3600);
  vi.stubGlobal("fetch", transport({ queryFailure: true }));
  app("/chat/session-1");
  await screen.findByLabelText("Câu hỏi của bạn");
  await waitFor(() =>
    expect(
      (screen.getByRole("button", { name: "Gửi câu hỏi" }) as HTMLButtonElement).disabled,
    ).toBe(true),
  );
  await userEvent.type(screen.getByLabelText("Câu hỏi của bạn"), "A question");
  await userEvent.click(screen.getByRole("button", { name: "Gửi câu hỏi" }));
  await screen.findByRole("alert");
  expect(screen.queryByText("Chưa đủ bằng chứng trong tài liệu")).toBeNull();
  await waitFor(() =>
    expect((screen.getByLabelText("Câu hỏi của bạn") as HTMLTextAreaElement).value).toBe(
      "A question",
    ),
  );
});
it("prevents new messages from exceeding the backend history cap", async () => {
  storeSession(token, 3600);
  const fetcher = transport();
  const history = Array.from({ length: 49 }, (_, i) =>
    messages.map((m) => ({ ...m, id: `${m.id}-${i}` })),
  ).flat();
  vi.stubGlobal(
    "fetch",
    vi.fn(async (path: string, init?: RequestInit) =>
      path.includes("/messages?") ? ok({ items: history }) : fetcher(path, init),
    ),
  );
  app("/chat/session-1");
  await screen.findByText("Phiên gần giới hạn hiển thị lịch sử");
  expect((screen.getByLabelText("Câu hỏi của bạn") as HTMLTextAreaElement).disabled).toBe(true);
  expect(screen.getByRole("link", { name: "Tạo cuộc trò chuyện mới" })).toBeTruthy();
});
it("fills the composer from a suggestion without sending a query", async () => {
  storeSession(token, 3600);
  const fetcher = transport();
  vi.stubGlobal("fetch", fetcher);
  app();
  const [first] = await screen.findAllByRole("button", { name: /nghỉ phép/ });
  await userEvent.click(first);
  expect((screen.getByLabelText("Câu hỏi của bạn") as HTMLTextAreaElement).value).toBe(
    first.textContent,
  );
  expect(fetcher.mock.calls.some(([path]) => path.endsWith("/chat/query"))).toBe(false);
  expect(
    fetcher.mock.calls.some(
      ([path, init]) => path.endsWith("/chat/sessions") && init?.method === "POST",
    ),
  ).toBe(false);
});
it("hides suggestions when no document is ready", async () => {
  storeSession(token, 3600);
  vi.stubGlobal("fetch", transport({ noSources: true }));
  app();
  await screen.findByText("0 tài liệu sẵn sàng");
  expect(screen.queryByRole("button", { name: /nghỉ phép/ })).toBeNull();
  expect(screen.getByRole("link", { name: "Xem tài liệu" })).toBeTruthy();
});
