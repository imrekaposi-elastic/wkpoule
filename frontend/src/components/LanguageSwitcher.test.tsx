import { describe, expect, it, vi } from "vitest";
import { fireEvent, screen } from "@testing-library/react";

import LanguageSwitcher from "./LanguageSwitcher";
import { renderWithProviders } from "../test/renderWithProviders";
import i18n from "../i18n/i18n";

describe("LanguageSwitcher", () => {
  it("changes language from the dropdown", async () => {
    const changeLanguage = vi.spyOn(i18n, "changeLanguage").mockResolvedValue(i18n.t);

    renderWithProviders(<LanguageSwitcher />);

    fireEvent.click(screen.getByRole("button", { name: /change language/i }));
    fireEvent.click(screen.getByRole("button", { name: /Nederlands/i }));

    expect(changeLanguage).toHaveBeenCalledWith("nl");
    changeLanguage.mockRestore();
  });
});
