/** Synthetic API transport: UI contracts only, no Gemini or development DB. */
import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { expect, it, vi } from "vitest";
import App from "../../App";
import type { Folder } from "../../api/types";
import { storeSession } from "../../auth/session";
import { answer, doc, failure, messages, ok, token, user } from "../../test/fixtures";
import { savePending } from "../chat/pending";

const hr: Folder = {
  id: "folder-hr",
  name: "Nhân sự",
  ready_document_count: 1,
  created_at: doc.created_at,
  updated_at: doc.created_at,
};
const sales: Folder = { ...hr, id: "folder-sales", name: "Kinh doanh", ready_document_count: 0 };
function setup(
  path = "/documents",
  options: {
    member?: boolean;
    folders?: Folder[];
    error?: "duplicate_folder" | "folder_not_empty";
    folderReadError?: boolean;
    queryError?: boolean;
  } = {},
) {
  const state = {
    folders: options.folders ?? [hr, sales],
    docs: [{ ...doc, folder_id: hr.id }],
    complete: false,
  };
  const fetcher = vi.fn(async (path: string, init?: RequestInit) => {
    const method = init?.method ?? "GET";
    if (path.endsWith("/auth/me"))
      return ok({ ...user, role: options.member ? "member" : "knowledge_admin" });
    if (path.endsWith("/folders") && method === "GET")
      return options.folderReadError
        ? failure(503, "database_unavailable")
        : ok({ items: state.folders });
    if (path.endsWith("/folders") && method === "POST") {
      if (options.error === "duplicate_folder") return failure(409, options.error);
      const folder = { ...sales, id: "folder-new", name: JSON.parse(init!.body as string).name };
      state.folders = [...state.folders, folder];
      return ok(folder);
    }
    if (path.includes("/folders/") && method === "PATCH") {
      if (options.error === "duplicate_folder") return failure(409, options.error);
      const id = path.split("/").pop();
      const name = JSON.parse(init!.body as string).name;
      state.folders = state.folders.map((f) => (f.id === id ? { ...f, name } : f));
      return ok(state.folders.find((f) => f.id === id));
    }
    if (path.includes("/folders/") && method === "DELETE") {
      if (options.error === "folder_not_empty") return failure(409, options.error);
      const id = path.split("/").pop();
      state.folders = state.folders.filter((f) => f.id !== id);
      return ok({ id, deleted: true });
    }
    if (path.includes("/documents?") && method === "GET") {
      const folder = new URL(path, "http://test").searchParams.get("folder_id");
      return ok({ items: state.docs.filter((d) => !folder || d.folder_id === folder) });
    }
    if (path.endsWith(`/documents/${doc.id}`) && method === "PATCH") {
      const folder_id = JSON.parse(init!.body as string).folder_id;
      state.docs = state.docs.map((d) => ({ ...d, folder_id }));
      return ok(state.docs[0]);
    }
    if (path.endsWith("/documents") && method === "POST")
      return ok({ document_id: "uploaded", job_id: "job-upload", status: "queued" });
    if (path.endsWith("/chat/sessions") && method === "POST")
      return ok({ id: "session-1", title: "Question", created_at: doc.created_at });
    if (path.includes("/chat/sessions?")) return ok({ items: [] });
    if (path.includes("/messages?")) return ok({ items: state.complete ? messages : [] });
    if (path.endsWith("/chat/query")) {
      if (options.queryError) return failure(404, "not_found");
      state.complete = true;
      return ok(answer);
    }
    throw new Error(`Unhandled folder UI fixture: ${method} ${path}`);
  });
  storeSession(token, 3600);
  vi.stubGlobal("fetch", fetcher);
  const view = render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );
  return { state, fetcher, ...view };
}
const mutations = (fetcher: ReturnType<typeof setup>["fetcher"]) =>
  fetcher.mock.calls.filter(([, init]) =>
    ["PATCH", "POST", "DELETE"].includes(init?.method ?? "GET"),
  );
async function chooseFolder(name = /Nhân sự/) {
  await userEvent.click(await screen.findByText(/Phạm vi:/));
  await userEvent.click(screen.getByRole("button", { name: "Thư mục" }));
  await userEvent.click(await screen.findByRole("checkbox", { name }));
}
it("filters through the server, keeps the filter visible when empty, and clears it", async () => {
  const { fetcher } = setup();
  await screen.findByText(doc.filename);
  await userEvent.selectOptions(screen.getByLabelText("Lọc theo thư mục"), sales.id);
  await screen.findByRole("heading", { name: "Thư mục chưa có tài liệu" });
  expect(fetcher.mock.calls.some(([path]) => path.endsWith(`&folder_id=${sales.id}`))).toBe(true);
  expect(screen.queryByText(doc.filename)).toBeNull();
  await userEvent.selectOptions(screen.getByLabelText("Lọc theo thư mục"), "");
  await screen.findByText(doc.filename);
});
it("creates a folder and refreshes the list", async () => {
  const { fetcher } = setup();
  await userEvent.click(await screen.findByRole("button", { name: "Tạo thư mục" }));
  await userEvent.type(screen.getByLabelText("Tên thư mục"), " Kỹ thuật ");
  await userEvent.click(
    within(screen.getByRole("dialog")).getByRole("button", { name: "Tạo thư mục" }),
  );
  await screen.findByRole("button", { name: "Đổi tên thư mục “Kỹ thuật”" });
  expect(JSON.parse(mutations(fetcher)[0][1]!.body as string)).toEqual({ name: "Kỹ thuật" });
});
it("requires rename confirmation and sends nothing after cancel", async () => {
  const { fetcher } = setup();
  const open = await screen.findByRole("button", { name: "Đổi tên thư mục “Nhân sự”" });
  await userEvent.click(open);
  await userEvent.clear(screen.getByLabelText("Tên thư mục"));
  await userEvent.type(screen.getByLabelText("Tên thư mục"), "Nhân sự mới");
  expect(mutations(fetcher)).toHaveLength(0);
  await userEvent.click(screen.getByRole("button", { name: "Hủy" }));
  expect(mutations(fetcher)).toHaveLength(0);
  await userEvent.click(open);
  await userEvent.clear(screen.getByLabelText("Tên thư mục"));
  await userEvent.type(screen.getByLabelText("Tên thư mục"), "Nhân sự mới");
  await userEvent.click(screen.getByRole("button", { name: "Xác nhận đổi tên" }));
  await screen.findByRole("button", { name: "Đổi tên thư mục “Nhân sự mới”" });
  expect(mutations(fetcher)[0][0]).toBe(`/api/v1/folders/${hr.id}`);
});
it("confirms deletion and resets a deleted active filter", async () => {
  const { fetcher } = setup();
  await screen.findByLabelText("Lọc theo thư mục");
  await userEvent.selectOptions(screen.getByLabelText("Lọc theo thư mục"), sales.id);
  await userEvent.click(screen.getByRole("button", { name: "Xóa thư mục “Kinh doanh”" }));
  expect(mutations(fetcher)).toHaveLength(0);
  await userEvent.click(screen.getByRole("button", { name: "Hủy" }));
  expect(mutations(fetcher)).toHaveLength(0);
  await userEvent.click(screen.getByRole("button", { name: "Xóa thư mục “Kinh doanh”" }));
  await userEvent.click(screen.getByRole("button", { name: "Xóa thư mục" }));
  await waitFor(() =>
    expect(screen.queryByRole("button", { name: "Xóa thư mục “Kinh doanh”" })).toBeNull(),
  );
  expect((screen.getByLabelText("Lọc theo thư mục") as HTMLSelectElement).value).toBe("");
  await screen.findByText(doc.filename);
});
it("shows duplicate name errors without closing or reporting success", async () => {
  setup("/documents", { error: "duplicate_folder" });
  await userEvent.click(await screen.findByRole("button", { name: "Đổi tên thư mục “Nhân sự”" }));
  await userEvent.click(screen.getByRole("button", { name: "Xác nhận đổi tên" }));
  expect((await screen.findByRole("alert")).textContent).toContain("Tên thư mục đã tồn tại");
  expect(screen.getByRole("dialog")).toBeTruthy();
  expect(screen.queryByText("Đã cập nhật thư mục.")).toBeNull();
});
it("allows a zero-ready folder deletion attempt but displays the authoritative 409", async () => {
  setup("/documents", { error: "folder_not_empty" });
  await userEvent.click(await screen.findByRole("button", { name: "Xóa thư mục “Kinh doanh”" }));
  await userEvent.click(screen.getByRole("button", { name: "Xóa thư mục" }));
  expect((await screen.findByRole("alert")).textContent).toContain(
    "Thư mục còn tài liệu tham chiếu",
  );
  expect(screen.getByRole("dialog")).toBeTruthy();
});
it("moves a document out of an active folder then supports removing classification", async () => {
  const { fetcher } = setup();
  await screen.findByText(doc.filename);
  await userEvent.selectOptions(screen.getByLabelText("Lọc theo thư mục"), hr.id);
  await userEvent.click(await screen.findByRole("button", { name: "Chuyển thư mục" }));
  await userEvent.selectOptions(screen.getByLabelText("Thư mục đích"), sales.id);
  await userEvent.click(screen.getByRole("button", { name: "Lưu thư mục" }));
  await screen.findByRole("heading", { name: "Thư mục chưa có tài liệu" });
  expect(JSON.parse(mutations(fetcher)[0][1]!.body as string)).toEqual({ folder_id: sales.id });
  await userEvent.selectOptions(screen.getByLabelText("Lọc theo thư mục"), "");
  await userEvent.click(await screen.findByRole("button", { name: "Chuyển thư mục" }));
  await userEvent.selectOptions(screen.getByLabelText("Thư mục đích"), "");
  await userEvent.click(screen.getByRole("button", { name: "Lưu thư mục" }));
  await screen.findByText("Chưa phân loại");
  expect(JSON.parse(mutations(fetcher)[1][1]!.body as string)).toEqual({ folder_id: null });
});
it("uploads with the active folder ID in multipart", async () => {
  const { fetcher } = setup();
  await screen.findByLabelText("Lọc theo thư mục");
  await userEvent.selectOptions(screen.getByLabelText("Lọc theo thư mục"), hr.id);
  await userEvent.click(screen.getAllByRole("button", { name: "Tải tài liệu" })[0]);
  expect((screen.getByLabelText("Thư mục (tùy chọn)") as HTMLSelectElement).value).toBe(hr.id);
  await userEvent.upload(
    screen.getByLabelText("Chọn hoặc thả một tài liệu"),
    new File(["synthetic"], "sample.txt", { type: "text/plain" }),
  );
  await userEvent.click(
    within(screen.getByRole("dialog")).getByRole("button", { name: "Tải tài liệu" }),
  );
  await screen.findByText("Đã nhận tài liệu. Nội dung sẽ được dùng khi xử lý hoàn tất.");
  const body = mutations(fetcher)[0][1]!.body as FormData;
  expect(body.get("folder_id")).toBe(hr.id);
  expect((body.get("file") as File).name).toBe("sample.txt");
});
it("gives members read filters and chat scope without folder write controls", async () => {
  setup("/documents", { member: true });
  await screen.findByLabelText("Lọc theo thư mục");
  expect(screen.queryByRole("button", { name: "Tạo thư mục" })).toBeNull();
  expect(screen.queryByRole("button", { name: /Đổi tên thư mục/ })).toBeNull();
  expect(screen.queryByRole("button", { name: /Xóa thư mục/ })).toBeNull();
  expect(screen.queryByRole("button", { name: "Chuyển thư mục" })).toBeNull();
});
it.each(["/chat", "/chat/session-1"])(
  "sends folder IDs with document intersection from %s",
  async (path) => {
    const { fetcher } = setup(path, { member: true });
    await screen.findByText("1 tài liệu sẵn sàng", { selector: ".chip" });
    await chooseFolder();
    await userEvent.click(screen.getByRole("button", { name: "Tài liệu" }));
    await userEvent.click(screen.getByRole("checkbox", { name: doc.filename }));
    await userEvent.type(screen.getByLabelText("Câu hỏi của bạn"), "Question");
    await userEvent.click(screen.getByRole("button", { name: "Gửi câu hỏi" }));
    await screen.findByText("A supported claim.");
    const call = fetcher.mock.calls.find(([path]) => path.endsWith("/chat/query"));
    expect(JSON.parse(call![1]!.body as string).filters).toEqual({
      folder_ids: [hr.id],
      document_ids: [doc.id],
    });
    expect(screen.getByText("Thư mục: Nhân sự")).toBeTruthy();
  },
);
it("sends a zero-ready folder as scope without falling back to all documents", async () => {
  const { fetcher } = setup("/chat/session-1");
  await chooseFolder(/Kinh doanh/);
  await userEvent.type(screen.getByLabelText("Câu hỏi của bạn"), "Question");
  await userEvent.click(screen.getByRole("button", { name: "Gửi câu hỏi" }));
  await screen.findByText("A supported claim.");
  const call = fetcher.mock.calls.find(([path]) => path.endsWith("/chat/query"));
  expect(JSON.parse(call![1]!.body as string).filters).toEqual({
    folder_ids: [sales.id],
    document_ids: [],
  });
});
it("blocks a folder removed on refresh and retains the chip until explicitly cleared", async () => {
  const { state, fetcher } = setup("/chat/session-1");
  await chooseFolder();
  state.folders = [sales];
  act(() => window.dispatchEvent(new Event("focus")));
  await screen.findByText("Chưa xác minh được thư mục đã chọn");
  await userEvent.type(screen.getByLabelText("Câu hỏi của bạn"), "Question");
  expect((screen.getByRole("button", { name: "Gửi câu hỏi" }) as HTMLButtonElement).disabled).toBe(
    true,
  );
  expect(mutations(fetcher)).toHaveLength(0);
  await userEvent.click(
    screen.getByRole("button", {
      name: "Bỏ thư mục Thư mục không còn trong danh sách khỏi phạm vi",
    }),
  );
  expect((screen.getByRole("button", { name: "Gửi câu hỏi" }) as HTMLButtonElement).disabled).toBe(
    false,
  );
});
it("updates folder chip names on refresh without changing selected IDs", async () => {
  const { state } = setup("/chat/session-1");
  await chooseFolder();
  state.folders = [{ ...hr, name: "Nhân sự mới" }, sales];
  act(() => window.dispatchEvent(new Event("focus")));
  await screen.findByText("Thư mục: Nhân sự mới");
  expect(screen.queryByText("Thư mục: Nhân sự")).toBeNull();
});
it("recovers the original pending folder scope and request ID after remount", async () => {
  savePending(user.id, "session-1", {
    startedAt: Date.now(),
    payload: {
      session_id: "session-1",
      client_request_id: "original-request",
      question: "Question",
      retrieval_mode: "dense",
      filters: { document_ids: [], folder_ids: [hr.id] },
    },
  });
  const { fetcher } = setup("/chat/session-1");
  await screen.findByText("Thư mục: Nhân sự");
  await userEvent.click(await screen.findByRole("button", { name: "Kiểm tra lại truy vấn" }));
  await screen.findByText("A supported claim.");
  const call = fetcher.mock.calls.find(([path]) => path.endsWith("/chat/query"));
  expect(JSON.parse(call![1]!.body as string)).toMatchObject({
    client_request_id: "original-request",
    filters: { folder_ids: [hr.id] },
  });
});
it("renders a folder list error and does not expose document move controls as usable", async () => {
  setup("/documents", { folderReadError: true });
  await screen.findByRole("alert");
  await screen.findByText(doc.filename);
  expect(
    (screen.getByRole("button", { name: "Chuyển thư mục" }) as HTMLButtonElement).disabled,
  ).toBe(true);
});
it("keeps folder scope when chat returns an API error", async () => {
  setup("/chat/session-1", { queryError: true });
  await chooseFolder();
  await userEvent.type(screen.getByLabelText("Câu hỏi của bạn"), "Question");
  await userEvent.click(screen.getByRole("button", { name: "Gửi câu hỏi" }));
  await screen.findByRole("alert");
  expect(screen.getByText("Thư mục: Nhân sự")).toBeTruthy();
  expect((screen.getByLabelText("Câu hỏi của bạn") as HTMLTextAreaElement).value).toBe("Question");
});
