import { StrictMode } from "react";
import { act, render, screen } from "@testing-library/react";
import { it, expect, vi } from "vitest";
import { Dialog } from "./Dialog";
it("ignores a stale close event that arrives after the dialog reopened", () => {
  const onClose = vi.fn();
  render(
    <StrictMode>
      <Dialog title="Tải tài liệu" onClose={onClose}>
        <p>Body</p>
      </Dialog>
    </StrictMode>,
  );
  const dialog = document.querySelector("dialog")!;
  expect(dialog.open).toBe(true);
  // Browsers queue the close event from close(); simulate it arriving while the dialog is open.
  act(() => {
    dialog.dispatchEvent(new Event("close"));
  });
  expect(onClose).not.toHaveBeenCalled();
  expect(screen.getByText("Body")).toBeTruthy();
});
it("still reports a real close", () => {
  const onClose = vi.fn();
  render(
    <Dialog title="Tải tài liệu" onClose={onClose}>
      <p>Body</p>
    </Dialog>,
  );
  const dialog = document.querySelector("dialog")!;
  act(() => {
    dialog.removeAttribute("open");
    dialog.dispatchEvent(new Event("close"));
  });
  expect(onClose).toHaveBeenCalledTimes(1);
});
