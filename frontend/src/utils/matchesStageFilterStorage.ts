const STAGE_PIN_KEY = "wkpoule_matches_stage_pin";
const STAGE_KEY = "wkpoule_matches_stage";
const GROUP_KEY = "wkpoule_matches_group";

export type MatchesStageFilter = {
  stage: string;
  group: string;
  pinned: boolean;
};

export function readMatchesStageFilter(): MatchesStageFilter {
  try {
    const pinned = localStorage.getItem(STAGE_PIN_KEY) === "1";
    if (!pinned) {
      return { stage: "", group: "", pinned: false };
    }
    return {
      stage: localStorage.getItem(STAGE_KEY) ?? "",
      group: localStorage.getItem(GROUP_KEY) ?? "",
      pinned: true,
    };
  } catch {
    return { stage: "", group: "", pinned: false };
  }
}

export function writeMatchesStageFilter(
  stage: string,
  group: string,
  pinned: boolean,
): void {
  try {
    if (pinned) {
      localStorage.setItem(STAGE_PIN_KEY, "1");
      localStorage.setItem(STAGE_KEY, stage);
      localStorage.setItem(GROUP_KEY, group);
    } else {
      localStorage.removeItem(STAGE_PIN_KEY);
      localStorage.removeItem(STAGE_KEY);
      localStorage.removeItem(GROUP_KEY);
    }
  } catch {
    // ignore storage failures
  }
}
