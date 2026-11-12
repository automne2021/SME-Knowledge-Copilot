import { afterEach, beforeEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";
import { clearSession } from "../auth/session";
// jsdom's Blob lacks text(); browsers expose it. Keep the polyfill test-only.
if (!Blob.prototype.text)
  Object.defineProperty(Blob.prototype, "text", {
    value: function (this: Blob) {
      return new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result));
        reader.onerror = () => reject(reader.error);
        reader.readAsText(this);
      });
    },
  });
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  })),
});
Object.defineProperty(HTMLDialogElement.prototype, "showModal", {
  configurable: true,
  value: function (this: HTMLDialogElement) {
    this.setAttribute("open", "");
  },
});
Object.defineProperty(HTMLDialogElement.prototype, "close", {
  configurable: true,
  value: function (this: HTMLDialogElement) {
    this.removeAttribute("open");
    this.dispatchEvent(new Event("close"));
  },
});
Object.defineProperty(URL, "createObjectURL", {
  configurable: true,
  writable: true,
  value: vi.fn(() => "blob:local-test"),
});
Object.defineProperty(URL, "revokeObjectURL", {
  configurable: true,
  writable: true,
  value: vi.fn(),
});
beforeEach(() => {
  clearSession();
  sessionStorage.clear();
});
afterEach(() => {
  cleanup();
  clearSession();
  vi.useRealTimers();
  vi.unstubAllGlobals();
});
