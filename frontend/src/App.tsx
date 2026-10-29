import { NavLink, Route, Routes } from "react-router-dom";

import BackendStatus from "./components/BackendStatus";
import PlaceholderPage from "./pages/PlaceholderPage";

// Màn hình M1 (spec 4.5). Knowledge và AI Copilot thêm ở M2.
const pages = [
  { path: "/", label: "Dự án", description: "Chọn dự án dùng cho demo." },
  {
    path: "/meetings",
    label: "Cuộc họp",
    description: "Upload audio, xem tiến trình xử lý, transcript, summary và action items.",
  },
  {
    path: "/approvals",
    label: "Phê duyệt",
    description: "Xem proposal đang chờ, chỉnh sửa và duyệt hoặc từ chối.",
  },
  { path: "/tasks", label: "Task", description: "Danh sách task đã được duyệt và nguồn gốc." },
];

export default function App() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-4 px-4 py-3">
          <span className="font-semibold">SME AI Operations Copilot</span>
          <nav className="flex flex-wrap gap-1">
            {pages.map((page) => (
              <NavLink
                key={page.path}
                to={page.path}
                end
                className={({ isActive }) =>
                  `rounded px-3 py-1.5 text-sm ${isActive ? "bg-slate-900 text-white" : "hover:bg-slate-100"}`
                }
              >
                {page.label}
              </NavLink>
            ))}
          </nav>
          <div className="ml-auto">
            <BackendStatus />
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">
        <Routes>
          {pages.map((page) => (
            <Route
              key={page.path}
              path={page.path}
              element={<PlaceholderPage title={page.label} description={page.description} />}
            />
          ))}
        </Routes>
      </main>
    </div>
  );
}
