import { render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import type { ChatSession } from "../../api/types";
import { DeleteSessionDialog } from "./SessionDialogs";

vi.mock("../../auth/AuthProvider", () => ({ useAuth: () => ({ user: null }) }));

it("focuses the safe cancel button when the delete-session dialog opens", () => {
  const session = { id: "session-1", title: "Hỏi về nghỉ phép" } as ChatSession;
  render(<DeleteSessionDialog session={session} onClose={vi.fn()} onDone={vi.fn()} />);
  expect(document.activeElement).toBe(screen.getByRole("button", { name: "Hủy" }));
});
