import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";

import QualificationTables from "./QualificationTables";
import { renderWithProviders } from "../test/renderWithProviders";

describe("QualificationTables", () => {
  it("renders standings and results with highlighted team", () => {
    renderWithProviders(
      <QualificationTables
        highlightCode="NED"
        data={{
          competition: { en: "UEFA Group G", nl: "UEFA Groep G" },
          standings: [
            {
              pos: 1,
              code: "NED",
              name: "Netherlands",
              p: 6,
              w: 4,
              d: 1,
              l: 1,
              gf: 12,
              ga: 4,
              gd: 8,
              pts: 13,
              highlight: true,
            },
          ],
          results: [
            { date: "2025-03-21", home: "NED", away: "FIN", score: "2-0" },
          ],
        }}
      />,
    );

    expect(screen.getByText("UEFA Group G")).toBeInTheDocument();
    expect(screen.getAllByText("Netherlands").length).toBeGreaterThan(0);
    expect(screen.getByText("2-0")).toBeInTheDocument();
  });
});
