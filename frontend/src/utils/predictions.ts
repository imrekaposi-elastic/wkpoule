import type { Match } from "../types";

/** First upcoming editable match (by match number) without a user prediction. */
export function firstMatchNeedingPrediction(
  matches: Match[],
  predictedMatchIds: Set<number>,
): Match | null {
  return (
    matches
      .filter((m) => m.status === "upcoming" && m.prediction_editable)
      .sort((a, b) => a.match_number - b.match_number)
      .find((m) => !predictedMatchIds.has(m.id)) ?? null
  );
}

const SECOND_KNOCKOUT_ROUND_STAGES = new Set([
  "round_of_16",
  "quarter_final",
  "semi_final",
  "third_place",
  "final",
]);

/** From round of 16 onward (2nd knockout round). */
export function isSecondKnockoutRoundOnwards(stage: string): boolean {
  return SECOND_KNOCKOUT_ROUND_STAGES.has(stage);
}

export function isKnockoutStage(stage: string): boolean {
  return stage !== "group";
}

export function isPredictedDraw(
  homeScore: number | "",
  awayScore: number | "",
): boolean {
  return (
    homeScore !== "" &&
    awayScore !== "" &&
    typeof homeScore === "number" &&
    typeof awayScore === "number" &&
    homeScore === awayScore
  );
}
