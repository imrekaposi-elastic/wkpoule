import { describe, expect, it } from "vitest";
import {
  PREDICTION_LOCK_MINUTES_BEFORE_KICKOFF,
  canEditMatchPrediction,
  isPredictionEditable,
} from "./predictionLock";

describe("predictionLock", () => {
  const kickoff = "2026-07-05T18:00:00.000Z";

  it("allows edits more than 30 minutes before kickoff", () => {
    const now = new Date("2026-07-05T16:00:00.000Z");
    expect(isPredictionEditable("upcoming", kickoff, now)).toBe(true);
    expect(canEditMatchPrediction("upcoming", kickoff, true, now)).toBe(true);
  });

  it("locks within 30 minutes of kickoff", () => {
    const now = new Date("2026-07-05T17:35:00.000Z");
    expect(isPredictionEditable("upcoming", kickoff, now)).toBe(false);
  });

  it("locks after kickoff even if status is still upcoming", () => {
    const now = new Date("2026-07-05T18:10:00.000Z");
    expect(isPredictionEditable("upcoming", kickoff, now)).toBe(false);
  });

  it("locks in-progress and completed matches", () => {
    const now = new Date("2026-07-05T12:00:00.000Z");
    expect(isPredictionEditable("in_progress", kickoff, now)).toBe(false);
    expect(isPredictionEditable("completed", kickoff, now)).toBe(false);
  });

  it("respects server prediction_editable flag", () => {
    const now = new Date("2026-07-05T12:00:00.000Z");
    expect(canEditMatchPrediction("upcoming", kickoff, false, now)).toBe(false);
  });

  it("uses the same lock window constant as the backend", () => {
    expect(PREDICTION_LOCK_MINUTES_BEFORE_KICKOFF).toBe(30);
  });
});
