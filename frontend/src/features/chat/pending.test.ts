import { expect, it } from "vitest";
import { readPending, savePending, type PendingQuery } from "./pending";
function pending(folderIds?: unknown): PendingQuery {
  return {
    startedAt: Date.now(),
    payload: {
      session_id: "session",
      client_request_id: "request",
      question: "Question",
      retrieval_mode: "dense",
      filters: {
        document_ids: [],
        ...(folderIds === undefined ? {} : { folder_ids: folderIds as string[] }),
      },
    },
  };
}
it("reads legacy pending requests without folder IDs and preserves new folder scope", () => {
  savePending("user", "session", pending());
  expect(readPending("user", "session")?.payload.filters).toEqual({ document_ids: [] });
  savePending("user", "session", pending(["folder-1"]));
  expect(readPending("user", "session")?.payload.filters.folder_ids).toEqual(["folder-1"]);
});
it.each(["bad", [5], ["duplicate", "duplicate"], Array.from({ length: 21 }, (_, i) => `f-${i}`)])(
  "rejects malformed pending folder scope: %j",
  (value) => {
    savePending("user", "session", pending(value));
    expect(readPending("user", "session")).toBeNull();
    expect(sessionStorage.getItem("sme.pending.user.session")).toBeNull();
  },
);
