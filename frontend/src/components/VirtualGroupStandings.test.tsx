import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";

import VirtualGroupStandings, { virtualRowClass } from "./VirtualGroupStandings";
import { renderWithProviders } from "../test/renderWithProviders";

describe("virtualRowClass", () => {
  it("maps qualification colours by rank", () => {
    expect(virtualRowClass(0, true)).toContain("emerald");
    expect(virtualRowClass(2, true)).toContain("amber");
    expect(virtualRowClass(2, false)).toContain("red");
    expect(virtualRowClass(3, null)).toContain("red");
  });
});

describe("VirtualGroupStandings", () => {
  it("renders predicted group table", () => {
    renderWithProviders(
      <VirtualGroupStandings
        groupLetter="A"
        virtualGroup={{
          group_letter: "A",
          third_place_qualifies: true,
          standings: [
            {
              team_id: 1,
              team_name: "Mexico",
              fifa_code: "MEX",
              played: 1,
              won: 1,
              drawn: 0,
              lost: 0,
              goals_for: 2,
              goals_against: 0,
              goal_difference: 2,
              points: 3,
            },
          ],
        }}
      />,
    );

    expect(screen.getByText("MEX")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
  });
});
