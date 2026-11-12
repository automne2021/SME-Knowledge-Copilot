import { describe, it, expect, vi } from "vitest";
import { apiBlob, apiFetch } from "./client";
import { readSession, storeSession } from "../auth/session";
import { deferred, failure, ok, token } from "../test/fixtures";
describe("authenticated API boundary", () => {
  it("adds bearer and JSON headers while preserving multipart boundaries", async () => {
    storeSession(token, 3600);
    const transport = vi.fn().mockImplementation(() => Promise.resolve(ok({ saved: true })));
    vi.stubGlobal("fetch", transport);
    await apiFetch("/example", { method: "POST", body: JSON.stringify({ x: 1 }) });
    const json = transport.mock.calls[0][1];
    expect(json.headers.get("Authorization")).toBe(`Bearer ${token}`);
    expect(json.headers.get("Content-Type")).toBe("application/json");
    await apiFetch("/documents", { method: "POST", body: new FormData() });
    expect(transport.mock.calls[1][1].headers.has("Content-Type")).toBe(false);
  });
  it("does not log out a new session on a stale 401", async () => {
    storeSession(token, 3600);
    const result = deferred<Response>();
    vi.stubGlobal(
      "fetch",
      vi.fn(() => result.promise),
    );
    const request = apiFetch("/auth/me").catch((e) => e);
    storeSession("b".repeat(43), 3600);
    result.resolve(failure(401, "unauthorized"));
    expect(await request).toMatchObject({ name: "AbortError" });
    expect(readSession()?.token).toBe("b".repeat(43));
  });
  it("discards late JSON bodies after account changes", async () => {
    storeSession(token, 3600);
    const body = deferred<unknown>();
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({ ok: true, json: () => body.promise })),
    );
    const request = apiFetch("/documents").catch((e) => e);
    await Promise.resolve();
    await Promise.resolve();
    storeSession("b".repeat(43), 3600);
    body.resolve({ data: { privateText: "old-account" } });
    expect(await request).toMatchObject({ name: "AbortError" });
  });
  it("expires only the matching credential and keeps error details", async () => {
    storeSession(token, 3600);
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => failure(401, "unauthorized", { reason: "expired" })),
    );
    await expect(apiFetch("/auth/me")).rejects.toMatchObject({
      status: 401,
      requestId: "req-test",
      details: { reason: "expired" },
    });
    expect(readSession()).toBeNull();
  });
  it("refuses HTML source bodies and never creates blob URLs", async () => {
    storeSession(token, 3600);
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response("<script>bad()</script>", { headers: { "Content-Type": "text/html" } }),
      ),
    );
    await expect(apiBlob("/documents/doc/content")).rejects.toMatchObject({
      code: "invalid_source",
    });
    expect(URL.createObjectURL).not.toHaveBeenCalled();
  });
  it("does not send credentials on login or accept remote paths", async () => {
    storeSession(token, 3600);
    const transport = vi.fn<(path: RequestInfo | URL, options?: RequestInit) => Promise<Response>>(
      async () => ok({}),
    );
    vi.stubGlobal("fetch", transport);
    await apiFetch("/auth/login", { auth: false });
    expect(new Headers(transport.mock.calls[0][1]?.headers).has("Authorization")).toBe(false);
    await expect(apiFetch("https://other.invalid")).rejects.toThrow("Invalid API path");
    expect(transport).toHaveBeenCalledTimes(1);
  });
});
