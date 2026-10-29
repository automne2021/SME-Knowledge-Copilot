import { useEffect, useState } from "react";

import { apiFetch } from "../api/client";

type Status = "checking" | "ok" | "error";

export default function BackendStatus() {
  const [status, setStatus] = useState<Status>("checking");

  useEffect(() => {
    apiFetch<{ status: string }>("/health")
      .then(() => setStatus("ok"))
      .catch(() => setStatus("error"));
  }, []);

  const label = {
    checking: "Đang kiểm tra backend…",
    ok: "Backend: kết nối được",
    error: "Backend: không kết nối được",
  }[status];
  const color = { checking: "bg-slate-400", ok: "bg-emerald-500", error: "bg-red-500" }[status];

  return (
    <span className="flex items-center gap-2 text-xs text-slate-600">
      <span className={`h-2 w-2 rounded-full ${color}`} />
      {label}
    </span>
  );
}
