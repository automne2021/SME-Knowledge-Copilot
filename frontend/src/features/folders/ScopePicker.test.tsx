import { useState } from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it } from "vitest";
import { ScopePicker } from "./ScopePicker";
import { doc } from "../../test/fixtures";
function Picker() {
  const [folders, setFolders] = useState<string[]>(Array.from({ length: 20 }, (_, i) => `f-${i}`));
  const [documents, setDocuments] = useState<string[]>([doc.id]);
  return (
    <ScopePicker
      documents={[doc]}
      documentCount={1}
      folders={Array.from({ length: 21 }, (_, i) => ({
        id: `f-${i}`,
        name: `Folder ${i}`,
        ready_document_count: 0,
        created_at: "",
        updated_at: "",
      }))}
      selected={documents}
      setSelected={setDocuments}
      selectedFolders={folders}
      setSelectedFolders={setFolders}
      disabled={false}
    />
  );
}
it("caps folder scope at 20, permits deselection, and clears both scopes with All", async () => {
  render(<Picker />);
  await userEvent.click(screen.getByText(/Phạm vi:/));
  await userEvent.click(screen.getByRole("button", { name: "Thư mục" }));
  const extra = screen.getByRole("checkbox", { name: /^Folder 20 / }) as HTMLInputElement;
  expect(extra.disabled).toBe(true);
  await userEvent.click(screen.getByRole("checkbox", { name: /^Folder 0 / }));
  expect(extra.disabled).toBe(false);
  await userEvent.click(extra);
  expect(screen.getByText("Thư mục: Folder 20")).toBeTruthy();
  await userEvent.click(screen.getByRole("checkbox", { name: "Tất cả tài liệu sẵn sàng" }));
  expect(screen.queryByRole("list", { name: "Nguồn đang hỏi" })).toBeNull();
  expect(
    (screen.getByRole("checkbox", { name: "Tất cả tài liệu sẵn sàng" }) as HTMLInputElement)
      .checked,
  ).toBe(true);
});
