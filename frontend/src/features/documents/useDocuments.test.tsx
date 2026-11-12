import { act, renderHook } from "@testing-library/react";
import { it, expect, vi } from "vitest";
import { useDocuments } from "./useDocuments";
import { storeSession } from "../../auth/session";
import { doc, ok, token } from "../../test/fixtures";
it("polls active jobs and stops after terminal publication", async () => {
  storeSession(token, 3600);
  vi.useFakeTimers();
  let reads = 0;
  vi.stubGlobal(
    "fetch",
    vi.fn(async (path: string) => {
      if (path.includes("/documents?")) {
        reads++;
        return ok({
          items: [{ ...doc, latest_job_id: "job-1", status: reads === 1 ? "queued" : "ready" }],
        });
      }
      return ok({
        id: "job-1",
        document_id: doc.id,
        kind: "ingest",
        status: reads === 1 ? "running" : "completed",
        stage: "publish",
        retryable: false,
      });
    }),
  );
  const { result } = renderHook(() => useDocuments());
  await act(async () => {
    await vi.advanceTimersByTimeAsync(0);
  });
  expect(result.current.items[0]?.status).toBe("queued");
  await act(async () => {
    await vi.advanceTimersByTimeAsync(2100);
  });
  expect(result.current.items[0]?.status).toBe("ready");
  const completeReads = reads;
  await act(async () => {
    await vi.advanceTimersByTimeAsync(30000);
  });
  expect(reads).toBe(completeReads);
});
