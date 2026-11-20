import { StrictMode, useRef } from "react";
import { act, fireEvent, render, screen } from "@testing-library/react";
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
it("focuses initialFocus after showModal, closes on Escape and restores focus", () => {
  // Browsers focus the first focusable element in showModal(); mimic that so the test proves
  // Dialog moves focus afterwards instead of passing only because the polyfill does nothing.
  const showModal = vi.spyOn(HTMLDialogElement.prototype, "showModal").mockImplementation(function (
    this: HTMLDialogElement,
  ) {
    this.setAttribute("open", "");
    this.querySelector<HTMLElement>("button")?.focus();
  });
  try {
    const opener = document.createElement("button");
    document.body.append(opener);
    opener.focus();
    const onClose = vi.fn();
    function Harness() {
      const cancel = useRef<HTMLButtonElement>(null);
      return (
        <Dialog title="Xóa?" onClose={onClose} initialFocus={cancel}>
          <button ref={cancel} type="button">
            Hủy
          </button>
        </Dialog>
      );
    }
    const view = render(<Harness />);
    expect(document.activeElement).toBe(screen.getByRole("button", { name: "Hủy" }));
    fireEvent(document.querySelector("dialog")!, new Event("cancel", { cancelable: true }));
    expect(onClose).toHaveBeenCalledTimes(1);
    view.unmount();
    expect(document.activeElement).toBe(opener);
    opener.remove();
  } finally {
    showModal.mockRestore();
  }
});
