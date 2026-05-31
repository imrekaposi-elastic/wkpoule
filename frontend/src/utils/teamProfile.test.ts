import { describe, expect, it } from "vitest";

import type { TeamDetail, TeamSummary } from "../types";
import {
  localizedTeamProfileField,
  teamProfileBulletLines,
} from "./teamProfile";

function sampleSummary(): TeamSummary {
  return {
    id: 1,
    name: "Netherlands",
    fifa_code: "NED",
    group_letter: "F",
    world_ranking: 7,
    flag_url: "",
    qualification_en: "Qualified via UEFA.",
    qualification_nl: "Gekwalificeerd via UEFA.",
    qualification_pt: "Classificou-se via UEFA.",
    qualification_de: "Qualifiziert über UEFA.",
    qualification_es: "Clasificado vía UEFA.",
    qualification_it: "Qualificato via UEFA.",
    qualification_he: "התמקד דרך UEFA.",
  };
}

function sampleDetail(): TeamDetail {
  return {
    ...sampleSummary(),
    strengths_en: "Midfield\nWings",
    strengths_nl: "Middenveld\nFlanken",
    strengths_pt: "Meio\nFlancos",
    strengths_de: "Mittelfeld\nFlanken",
    strengths_es: "Medio\nFlancos",
    strengths_it: "Centrocampo\nAli",
    strengths_he: "קשר\nאגפים",
    weaknesses_en: "Counters",
    weaknesses_nl: "Counters",
    weaknesses_pt: "Contra-ataques",
    weaknesses_de: "Konter",
    weaknesses_es: "Contraataques",
    weaknesses_it: "Contropiedi",
    weaknesses_he: "מתפרצות",
    players: [],
  };
}

describe("localizedTeamProfileField", () => {
  it("returns text for the active language", () => {
    const team = sampleSummary();
    expect(localizedTeamProfileField(team, "qualification", "nl")).toBe(
      "Gekwalificeerd via UEFA.",
    );
    expect(localizedTeamProfileField(team, "qualification", "de")).toBe(
      "Qualifiziert über UEFA.",
    );
  });

  it("falls back to another supported language when preferred is empty", () => {
    const team = { ...sampleSummary(), qualification_de: null };
    expect(localizedTeamProfileField(team, "qualification", "de")).toBe(
      "Qualified via UEFA.",
    );
  });

  it("reads strengths and weaknesses from detail records", () => {
    const team = sampleDetail();
    expect(localizedTeamProfileField(team, "strengths", "it")).toBe(
      "Centrocampo\nAli",
    );
    expect(localizedTeamProfileField(team, "weaknesses", "pt")).toBe("Contra-ataques");
  });
});

describe("teamProfileBulletLines", () => {
  it("splits non-empty lines", () => {
    expect(teamProfileBulletLines("One\n\nTwo\n  Three  ")).toEqual([
      "One",
      "Two",
      "Three",
    ]);
  });
});
