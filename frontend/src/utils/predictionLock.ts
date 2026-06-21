/** Must stay in sync with backend PREDICTION_LOCK_MINUTES_BEFORE_KICKOFF. */
export const PREDICTION_LOCK_MINUTES_BEFORE_KICKOFF = 30;

/** True when the user may still create or change a tip (group and knockout alike). */
export function isPredictionEditable(
  status: string,
  kickoffUtc: string,
  now: Date = new Date(),
): boolean {
  if (status !== "upcoming") return false;
  const kickoff = new Date(kickoffUtc);
  if (Number.isNaN(kickoff.getTime())) return false;
  const cutoffMs =
    kickoff.getTime() - PREDICTION_LOCK_MINUTES_BEFORE_KICKOFF * 60 * 1000;
  return now.getTime() < cutoffMs;
}

/** Combine API flag with local kickoff window (covers stale cached match lists). */
export function canEditMatchPrediction(
  status: string,
  kickoffUtc: string,
  predictionEditable: boolean,
  now: Date = new Date(),
): boolean {
  return (
    predictionEditable &&
    isPredictionEditable(status, kickoffUtc, now)
  );
}
