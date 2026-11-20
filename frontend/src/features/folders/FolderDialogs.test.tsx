import { render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import type { Folder } from "../../api/types";
import { FolderDialog } from "./FolderDialogs";

const folder = { id: "folder-hr", name: "Nhân sự", ready_document_count: 0 } as Folder;

it("focuses the safe cancel button when the delete-folder dialog opens", () => {
  render(<FolderDialog action={{ kind: "delete", folder }} onClose={vi.fn()} onDone={vi.fn()} />);
  expect(document.activeElement).toBe(screen.getByRole("button", { name: "Hủy" }));
});

it("does not move focus to cancel for the rename dialog", () => {
  render(<FolderDialog action={{ kind: "rename", folder }} onClose={vi.fn()} onDone={vi.fn()} />);
  expect(document.activeElement).not.toBe(screen.getByRole("button", { name: "Hủy" }));
});
