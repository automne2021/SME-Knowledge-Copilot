import { expireSession, readSession } from "../auth/session";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
    public readonly requestId?: string,
    public readonly details?: Record<string, unknown>,
  ) {
    super(message);
  }
}

export interface ApiOptions extends RequestInit {
  auth?: boolean;
  timeout?: number;
}
async function request<T>(path: string, options: ApiOptions, binary: boolean): Promise<T> {
  if (!path.startsWith("/") || path.startsWith("//") || path.includes("://"))
    throw new Error("Invalid API path");
  const { auth = true, timeout = 20000, signal, ...init } = options;
  const token = auth ? readSession()?.token : undefined;
  if (auth && !token) {
    window.dispatchEvent(new Event("sme:auth-expired"));
    throw new ApiError(401, "unauthorized", "Phiên đăng nhập đã hết hạn.");
  }
  const headers = new Headers(init.headers);
  headers.set("Accept", binary ? "application/pdf, text/plain" : "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (typeof init.body === "string") headers.set("Content-Type", "application/json");
  const controller = new AbortController();
  const abort = () => controller.abort();
  if (signal?.aborted) controller.abort();
  signal?.addEventListener("abort", abort, { once: true });
  const timer = setTimeout(abort, timeout);
  try {
    const response = await fetch(`/api/v1${path}`, {
      ...init,
      headers,
      signal: controller.signal,
      cache: "no-store",
      credentials: "omit",
    });
    if (token && readSession()?.token !== token)
      throw new DOMException("Session changed", "AbortError");
    if (!response.ok) {
      const body = await response.json().catch(() => null);
      if (response.status === 401 && token) expireSession(token);
      throw new ApiError(
        response.status,
        body?.error?.code ?? "http_error",
        body?.error?.message ?? "Không thể hoàn tất thao tác.",
        body?.request_id ?? response.headers.get("X-Request-ID") ?? undefined,
        body?.error?.details,
      );
    }
    if (binary) {
      const type = response.headers.get("Content-Type")?.split(";")[0].trim();
      if (type !== "application/pdf" && type !== "text/plain")
        throw new ApiError(502, "invalid_source", "Định dạng nguồn không được hỗ trợ.");
      const blob = await response.blob();
      if (token && readSession()?.token !== token)
        throw new DOMException("Session changed", "AbortError");
      if (blob.size > 20 * 1024 ** 2)
        throw new ApiError(502, "invalid_source", "Nguồn vượt giới hạn xem trước.");
      return blob as T;
    }
    const body = await response.json();
    if (token && readSession()?.token !== token)
      throw new DOMException("Session changed", "AbortError");
    if (!body || !("data" in body))
      throw new ApiError(502, "invalid_response", "Dữ liệu trả về không hợp lệ.");
    return body.data as T;
  } catch (error) {
    if (signal?.aborted) throw new DOMException("Request cancelled", "AbortError");
    if (
      error instanceof ApiError ||
      (error instanceof DOMException &&
        error.name === "AbortError" &&
        token &&
        readSession()?.token !== token)
    )
      throw error;
    throw new ApiError(
      0,
      controller.signal.aborted ? "request_timeout" : "network_error",
      controller.signal.aborted
        ? "Thao tác vượt thời gian chờ. Hãy kiểm tra lại trạng thái."
        : "Không kết nối được dịch vụ. Vui lòng thử lại.",
    );
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener("abort", abort);
  }
}
export function apiFetch<T>(path: string, init: ApiOptions = {}): Promise<T> {
  return request<T>(path, init, false);
}
export function apiBlob(path: string, signal?: AbortSignal): Promise<Blob> {
  return request<Blob>(path, { signal }, true);
}
export const isAbort = (error: unknown) =>
  error instanceof DOMException && error.name === "AbortError";
export function errorMessage(error: unknown) {
  if (error instanceof ApiError && error.code === "duplicate_folder")
    return "Tên thư mục đã tồn tại. Hãy chọn tên khác.";
  if (error instanceof ApiError && error.code === "folder_not_empty")
    return "Thư mục còn tài liệu tham chiếu nên chưa thể xóa, kể cả tài liệu đang hoặc đã xóa. Hãy chuyển tài liệu sang thư mục khác khi có thể.";
  return error instanceof ApiError ? error.message : "Có lỗi xảy ra. Vui lòng thử lại.";
}
