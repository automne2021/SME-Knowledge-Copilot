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
type SessionRow = { id: string; title: string; created_at: string };
function transport(
  options: {
    role?: string;
    noSources?: boolean;
    queryFailure?: boolean;
    sessions?: SessionRow[];
  } = {},
) {
  let complete = false;
  let sessions = options.sessions;
  return vi.fn(async (path: string, init?: RequestInit) => {
    if (path.endsWith("/auth/logout")) return ok({ revoked: true });
    if (sessions && path.includes("/chat/sessions/") && init?.method === "PATCH") {
      const key = decodeURIComponent(path.split("/chat/sessions/")[1]);
      const title = JSON.parse(init.body as string).title as string;
      sessions = sessions.map((row) => (row.id === key ? { ...row, title } : row));
      return ok(sessions.find((row) => row.id === key));
    }
    if (sessions && path.includes("/chat/sessions/") && init?.method === "DELETE") {
      const key = decodeURIComponent(path.split("/chat/sessions/")[1]);
      sessions = sessions.filter((row) => row.id !== key);
      return ok({ id: key, deleted: true });
    }
    if (sessions && path.includes("/chat/sessions?")) return ok({ items: sessions });
    if (path.endsWith("/auth/me")) return ok({ ...user, role: options.role ?? "knowledge_admin" });
    if (path.endsWith("/auth/login")) return ok({ access_token: token, expires_in: 3600 });
    if (path.endsWith("/folders")) return ok({ items: [] });
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
  expect(screen.getByText("Quản trị viên")).toBeTruthy();
  expect(JSON.stringify(sessionStorage)).not.toContain("private-test-password");
  await userEvent.click(screen.getByRole("button", { name: "Đăng xuất" }));
  await screen.findByRole("heading", { name: "Đăng nhập" });
  expect(sessionStorage.getItem("sme.auth.v1")).toBeNull();
  const revoke = fetcher.mock.calls.find(([path]) => path.endsWith("/auth/logout"));
  expect(revoke?.[1]?.method).toBe("POST");
  expect(new Headers(revoke?.[1]?.headers).get("Authorization")).toBe(`Bearer ${token}`);
});
it("still signs out locally when the revoke request fails", async () => {
  storeSession(token, 3600);
  const fetcher = transport();
  vi.stubGlobal(
    "fetch",
    vi.fn(async (path: string, init?: RequestInit) => {
      if (path.endsWith("/auth/logout")) throw new TypeError("network down");
      return fetcher(path, init);
    }),
  );
  app();
  await screen.findByRole("heading", { name: "Hỏi đáp tài liệu" });
  await userEvent.click(screen.getByRole("button", { name: "Đăng xuất" }));
  await screen.findByRole("heading", { name: "Đăng nhập" });
  expect(sessionStorage.getItem("sme.auth.v1")).toBeNull();
});
const SESSIONS: SessionRow[] = [
  { id: "session-1", title: "Hoàn ứng công tác", created_at: new Date().toISOString() },
  { id: "session-2", title: "Quy trình duyệt", created_at: "2026-01-02T03:00:00Z" },
];
it("renames a conversation from the sidebar", async () => {
  storeSession(token, 3600);
  const fetcher = transport({ sessions: SESSIONS });
  vi.stubGlobal("fetch", fetcher);
  app();
  await userEvent.click(await screen.findByRole("button", { name: "Đổi tên “Hoàn ứng công tác”" }));
  const input = screen.getByLabelText("Tên mới");
  await userEvent.clear(input);
  await userEvent.type(input, "Công tác tháng 11");
  await userEvent.click(screen.getByRole("button", { name: "Lưu" }));
  await screen.findByRole("link", { name: "Công tác tháng 11" });
  const call = fetcher.mock.calls.find(([, init]) => init?.method === "PATCH");
  expect(call?.[0]).toBe("/api/v1/chat/sessions/session-1");
  expect(JSON.parse(call![1]!.body as string)).toEqual({ title: "Công tác tháng 11" });
});
it("asks before deleting the open conversation and then leaves it", async () => {
  storeSession(token, 3600);
  const fetcher = transport({ sessions: SESSIONS });
  vi.stubGlobal("fetch", fetcher);
  app("/chat/session-1");
  const deleted = () => fetcher.mock.calls.some(([, init]) => init?.method === "DELETE");
  await userEvent.click(await screen.findByRole("button", { name: "Xóa “Hoàn ứng công tác”" }));
  expect(deleted()).toBe(false);
  await userEvent.click(screen.getByRole("button", { name: "Hủy" }));
  expect(deleted()).toBe(false);
  await userEvent.click(screen.getByRole("button", { name: "Xóa “Hoàn ứng công tác”" }));
  await userEvent.click(screen.getByRole("button", { name: "Xóa cuộc trò chuyện" }));
  await waitFor(() => expect(screen.queryByRole("link", { name: "Hoàn ứng công tác" })).toBeNull());
  const call = fetcher.mock.calls.find(([, init]) => init?.method === "DELETE");
  expect(call?.[0]).toBe("/api/v1/chat/sessions/session-1");
  await screen.findByText("Bạn cần tìm thông tin gì?");
});
it("lists history grouped by day and filters by title", async () => {
  storeSession(token, 3600);
  vi.stubGlobal("fetch", transport({ sessions: SESSIONS }));
  app("/history");
  await screen.findByRole("heading", { name: "Lịch sử hội thoại" });
  expect((await screen.findByRole("region", { name: "Hôm nay" })).textContent).toContain(
    "Hoàn ứng công tác",
  );
  expect(screen.getByRole("region", { name: "Cũ hơn" }).textContent).toContain("Quy trình duyệt");
  await userEvent.type(screen.getByLabelText("Tìm cuộc trò chuyện"), "duyệt");
  expect(screen.queryByRole("link", { name: "Hoàn ứng công tác" })).toBeNull();
  expect(screen.getByRole("link", { name: "Quy trình duyệt" })).toBeTruthy();
});
it("filters documents by name and status", async () => {
  storeSession(token, 3600);
  const failed = { ...doc, id: "doc-2", filename: "scan.pdf", status: "failed" as const };
  const fetcher = transport();
  vi.stubGlobal(
    "fetch",
    vi.fn(async (path: string, init?: RequestInit) =>
      path.includes("/documents?") ? ok({ items: [doc, failed] }) : fetcher(path, init),
    ),
  );
  app("/documents");
  await screen.findByText("scan.pdf");
  await userEvent.click(screen.getByRole("button", { name: /Cần chú ý/ }));
  expect(screen.queryByText(doc.filename)).toBeNull();
  expect(screen.getByText("scan.pdf")).toBeTruthy();
  await userEvent.click(screen.getByRole("button", { name: /Tất cả/ }));
  await userEvent.type(screen.getByLabelText("Tìm tài liệu"), "policy");
  expect(screen.getByText(doc.filename)).toBeTruthy();
  expect(screen.queryByText("scan.pdf")).toBeNull();
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
/** A query that never returns while the server already stored the question (as in production). */
function hangingQuery() {
  const base = transport();
  const state = { started: 0, historyLoads: 0 };
  const fetcher = vi.fn(async (path: string, init?: RequestInit) => {
    if (path.endsWith("/chat/query")) {
      state.started = Date.now();
      return new Promise<Response>((_, reject) =>
        init?.signal?.addEventListener("abort", () =>
          reject(new DOMException("Aborted", "AbortError")),
        ),
      );
    }
    if (path.includes("/messages?")) {
      state.historyLoads += 1;
      return ok({
        items: state.started
          ? [{ ...messages[0], created_at: new Date(state.started).toISOString() }]
          : [],
      });
    }
    return base(path, init);
  });
  return { fetcher, state };
}
async function askAndWait(question: string) {
  app("/chat/session-1");
  const box = await screen.findByLabelText("Câu hỏi của bạn");
  await waitFor(() => expect((box as HTMLTextAreaElement).disabled).toBe(false));
  await userEvent.type(box, question);
  await userEvent.click(screen.getByRole("button", { name: "Gửi câu hỏi" }));
  await screen.findByText("Đang tìm tài liệu và soạn câu trả lời…");
}
it("shows one question bubble and no reload spinner when returning to the tab mid-answer", async () => {
  storeSession(token, 3600);
  const { fetcher, state } = hangingQuery();
  vi.stubGlobal("fetch", fetcher);
  await askAndWait("A question");
  const before = state.historyLoads;
  act(() => {
    document.dispatchEvent(new Event("visibilitychange"));
    window.dispatchEvent(new Event("focus"));
  });
  expect(screen.queryByText("Đang kiểm tra lịch sử…")).toBeNull();
  await waitFor(() => expect(state.historyLoads).toBe(before + 1));
  await waitFor(() => expect(screen.getAllByText("A question")).toHaveLength(1));
  expect(screen.getByText("Đang tìm tài liệu và soạn câu trả lời…")).toBeTruthy();
});
it("tells the user when a wait is longer than usual and when it will stop", async () => {
  storeSession(token, 3600);
  vi.stubGlobal("fetch", hangingQuery().fetcher);
  await askAndWait("A question");
  expect(screen.queryByText(/Lâu hơn bình thường/)).toBeNull();
  const realNow = Date.now.bind(Date);
  const now = vi.spyOn(Date, "now").mockImplementation(() => realNow() + 70_000);
  try {
    await screen.findByText(/Lâu hơn bình thường/, undefined, { timeout: 2500 });
    expect(screen.getByText(/2:30/)).toBeTruthy();
  } finally {
    now.mockRestore();
  }
});
it("explains a model timeout once, as an error with a way to ask again", async () => {
  storeSession(token, 3600);
  const base = transport();
  let failed = false;
  vi.stubGlobal(
    "fetch",
    vi.fn(async (path: string, init?: RequestInit) => {
      if (path.endsWith("/chat/query")) {
        failed = true;
        return failure(504, "model_timeout");
      }
      if (path.includes("/messages?")) return ok({ items: failed ? [messages[0]] : [] });
      if (path.endsWith("/chat/runs/run-1"))
        return ok({ ...answer, status: "failed", error_code: "model_timeout" });
      return base(path, init);
    }),
  );
  app("/chat/session-1");
  const box = await screen.findByLabelText("Câu hỏi của bạn");
  await waitFor(() => expect((box as HTMLTextAreaElement).disabled).toBe(false));
  await userEvent.type(box, "A question");
  await userEvent.click(screen.getByRole("button", { name: "Gửi câu hỏi" }));
  await screen.findByText("Gemini không phản hồi kịp");
  expect(screen.getAllByRole("alert")).toHaveLength(1);
  expect(screen.queryByText(/chưa hoàn tất thành công/)).toBeNull();
  expect(screen.queryByText("Chưa đủ bằng chứng trong tài liệu")).toBeNull();
  await userEvent.click(screen.getByRole("button", { name: "Hỏi lại" }));
  expect((screen.getByLabelText("Câu hỏi của bạn") as HTMLTextAreaElement).value).toBe(
    "A question",
  );
});
