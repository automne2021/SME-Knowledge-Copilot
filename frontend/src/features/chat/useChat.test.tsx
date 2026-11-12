import { act, renderHook, waitFor } from "@testing-library/react";
import { it, expect, vi } from "vitest";
import { useChat } from "./useChat";
import { savePending } from "./pending";
import { storeSession, documentChanged } from "../../auth/session";
import { answer, deferred, messages, ok, token } from "../../test/fixtures";
const payload = {
  session_id: "session-1",
  client_request_id: "client-1",
  question: "A question",
  retrieval_mode: "dense" as const,
  filters: { document_ids: [] },
};
it("retries an uncertain query with exactly the same request identity", async () => {
  storeSession(token, 3600);
  let attempts = 0;
  const sent: unknown[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (path: string, options: RequestInit) => {
      if (path.endsWith("/chat/query")) {
        sent.push(JSON.parse(options.body as string));
        attempts++;
        if (attempts === 1) throw new TypeError("Network lost");
        return ok(answer);
      }
      return ok({ items: attempts >= 2 ? messages : [] });
    }),
  );
  const { result } = renderHook(() => useChat("user-1", "session-1"));
  await waitFor(() => expect(result.current.loading).toBe(false));
  await act(async () => {
    await result.current.run(payload);
  });
  expect(result.current.pending?.payload.client_request_id).toBe("client-1");
  expect(result.current.busy).toBe(false);
  await act(async () => {
    await result.current.run();
  });
  expect(sent).toEqual([payload, payload]);
  expect(result.current.pending).toBeNull();
  expect(result.current.messages).toHaveLength(2);
});
it("discards an old session response after navigation", async () => {
  storeSession(token, 3600);
  const old = deferred<Response>();
  vi.stubGlobal(
    "fetch",
    vi.fn(async (path: string) => (path.includes("session-1") ? old.promise : ok({ items: [] }))),
  );
  const { result, unmount } = renderHook(() => useChat("user-1", "session-1"));
  unmount();
  old.resolve(ok({ items: messages }));
  const next = renderHook(() => useChat("user-1", "session-2"));
  await waitFor(() => expect(next.result.current.loading).toBe(false));
  expect(next.result.current.messages).toEqual([]);
  expect(result.current.messages).toEqual([]);
});
it("hides cached answers before revalidating deleted sources", async () => {
  storeSession(token, 3600);
  let erased = false;
  vi.stubGlobal(
    "fetch",
    vi.fn(async () =>
      ok({
        items: erased
          ? messages.map((m) =>
              m.role === "assistant"
                ? { ...m, source_unavailable: true, answer: null, content: "" }
                : m,
            )
          : messages,
      }),
    ),
  );
  const { result } = renderHook(() => useChat("user-1", "session-1"));
  await waitFor(() => expect(result.current.messages).toHaveLength(2));
  erased = true;
  act(() => documentChanged("doc-1"));
  expect(result.current.messages).toEqual([]);
  await waitFor(() => expect(result.current.messages[1]?.source_unavailable).toBe(true));
});
it("restores a pending snapshot after reload without generating automatically", async () => {
  storeSession(token, 3600);
  savePending("user-1", "session-1", { payload, startedAt: Date.now() });
  const transport = vi.fn(async () => ok({ items: [] }));
  vi.stubGlobal("fetch", transport);
  const { result } = renderHook(() => useChat("user-1", "session-1"));
  await waitFor(() => expect(result.current.loading).toBe(false));
  expect(result.current.pending?.payload).toEqual(payload);
  expect(transport.mock.calls).toHaveLength(1);
});
it("recovers a known running run by polling without another generate request", async () => {
  storeSession(token, 3600);
  vi.useFakeTimers();
  let polls = 0;
  const transport = vi.fn(async (path: string) => {
    if (path.endsWith("/chat/runs/run-1")) {
      polls++;
      return ok(polls === 1 ? { ...answer, status: "running" } : answer);
    }
    return ok({ items: polls >= 2 ? messages : [] });
  });
  vi.stubGlobal("fetch", transport);
  savePending("user-1", "session-1", { payload, runId: "run-1", startedAt: Date.now() });
  const { result } = renderHook(() => useChat("user-1", "session-1"));
  await act(async () => {
    await vi.advanceTimersByTimeAsync(0);
  });
  let completion: Promise<void>;
  act(() => {
    completion = result.current.run();
  });
  await act(async () => {
    await vi.advanceTimersByTimeAsync(3100);
    await completion;
  });
  expect(result.current.pending).toBeNull();
  expect(result.current.messages).toHaveLength(2);
  expect(transport.mock.calls.some(([p]) => p.endsWith("/chat/query"))).toBe(false);
});
