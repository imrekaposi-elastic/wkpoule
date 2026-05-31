import { describe, expect, it, vi } from "vitest";
import { fireEvent, screen } from "@testing-library/react";

import Pagination from "./Pagination";
import { renderWithProviders } from "../test/renderWithProviders";

describe("Pagination", () => {
  it("renders nothing for a single short page", () => {
    const { container } = renderWithProviders(
      <Pagination page={1} totalPages={1} total={10} onPageChange={vi.fn()} />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("navigates between pages", () => {
    const onPageChange = vi.fn();
    renderWithProviders(
      <Pagination page={2} totalPages={4} total={80} onPageChange={onPageChange} />,
    );

    fireEvent.click(screen.getByRole("button", { name: /previous/i }));
    fireEvent.click(screen.getByRole("button", { name: /next/i }));

    expect(onPageChange).toHaveBeenCalledWith(1);
    expect(onPageChange).toHaveBeenCalledWith(3);
  });
});
