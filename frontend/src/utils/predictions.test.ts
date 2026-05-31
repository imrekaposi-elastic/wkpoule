import { describe, expect, it } from "vitest";

import { firstMatchNeedingPrediction, isKnockoutStage, isPredictedDraw, isSecondKnockoutRoundOnwards } from "./predictions";
import type { Match } from "../types";

function match(
  id: number,
  matchNumber: number,
  opts: Partial<Match> = {},
): Match {
  return {
    id,
    match_number: matchNumber,
    stage: "group",
    group_letter: "A",
    home_team: null,
    away_team: null,
    venue: { id: 1, name: "V", city: "C", country: "X", capacity: 1 },
    kickoff_utc: "2026-06-11T15:00:00Z",
    home_score: null,
    away_score: null,
    status: "upcoming",
    fun_comment: null,
    temperature_celsius: null,
    expert_prediction: null,
    prediction_editable: true,
    ...opts,
  };
}

describe("firstMatchNeedingPrediction", () => {
  it("returns lowest match number without a prediction", () => {
    const matches = [
      match(2, 2),
      match(1, 1),
      match(3, 3, { prediction_editable: false }),
    ];
    const result = firstMatchNeedingPrediction(matches, new Set([1]));
    expect(result?.match_number).toBe(2);
  });

  it("returns null when all editable upcoming matches are predicted", () => {
    const matches = [match(1, 1), match(2, 2)];
    expect(firstMatchNeedingPrediction(matches, new Set([1, 2]))).toBeNull();
  });
});

describe("knockout helpers", () => {
  it("detects knockout stages", () => {
    expect(isKnockoutStage("group")).toBe(false);
    expect(isKnockoutStage("round_of_16")).toBe(true);
    expect(isSecondKnockoutRoundOnwards("round_of_16")).toBe(true);
    expect(isSecondKnockoutRoundOnwards("round_of_32")).toBe(false);
  });

  it("detects predicted draws", () => {
    expect(isPredictedDraw(1, 1)).toBe(true);
    expect(isPredictedDraw(2, 1)).toBe(false);
    expect(isPredictedDraw("", 1)).toBe(false);
  });
});
