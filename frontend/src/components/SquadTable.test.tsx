import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";

import SquadTable from "./SquadTable";
import { renderWithProviders } from "../test/renderWithProviders";

describe("SquadTable", () => {
  it("renders player rows", () => {
    renderWithProviders(
      <SquadTable
        players={[
          {
            id: 1,
            name: "Virgil van Dijk",
            position: "DF",
            shirt_number: 4,
            club: "Liverpool",
            caps: 75,
          },
        ]}
      />,
    );

    expect(screen.getByText("Virgil van Dijk")).toBeInTheDocument();
    expect(screen.getByText("Liverpool")).toBeInTheDocument();
    expect(screen.getByText("75")).toBeInTheDocument();
  });
});
