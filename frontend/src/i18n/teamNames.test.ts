import { describe, expect, it } from "vitest";

import { localizedTeamName, localizedVenueCountry } from "./teamNames";

describe("localizedTeamName", () => {
  it("returns subdivision names for UK nations", () => {
    expect(localizedTeamName("ENG", "England", "nl")).toBe("Engeland");
    expect(localizedTeamName("SCO", "Scotland", "de")).toBe("Schottland");
  });

  it("localizes FIFA codes via region display names", () => {
    expect(localizedTeamName("NED", "Netherlands", "en")).toBe("Netherlands");
    expect(localizedTeamName("NED", "Netherlands", "nl")).toBe("Nederland");
  });

  it("falls back when code is unknown", () => {
    expect(localizedTeamName("XXX", "Mystery FC", "en")).toBe("Mystery FC");
    expect(localizedTeamName(null, "Guest Team", "en")).toBe("Guest Team");
  });
});

describe("localizedVenueCountry", () => {
  it("localizes host countries", () => {
    expect(localizedVenueCountry("USA", "en")).toBe("United States");
    expect(localizedVenueCountry("Mexico", "nl")).toBe("Mexico");
  });

  it("returns unknown countries unchanged", () => {
    expect(localizedVenueCountry("Brazil", "en")).toBe("Brazil");
  });
});
