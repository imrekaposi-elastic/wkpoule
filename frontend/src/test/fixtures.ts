import type { Match, Team, Venue } from "../types";

export const sampleVenue: Venue = {
  id: 1,
  name: "Arena",
  city: "Amsterdam",
  country: "Netherlands",
  capacity: 50000,
};

export const sampleTeamHome: Team = {
  id: 1,
  name: "Netherlands",
  fifa_code: "NED",
  group_letter: "A",
  world_ranking: 6,
  flag_url: "",
};

export const sampleTeamAway: Team = {
  id: 2,
  name: "Belgium",
  fifa_code: "BEL",
  group_letter: "A",
  world_ranking: 3,
  flag_url: "",
};

export const sampleMatch: Match = {
  id: 1,
  match_number: 1,
  stage: "group",
  group_letter: "A",
  home_team: sampleTeamHome,
  away_team: sampleTeamAway,
  venue: sampleVenue,
  kickoff_utc: "2026-06-11T18:00:00Z",
  home_score: null,
  away_score: null,
  status: "upcoming",
  fun_comment: null,
  temperature_celsius: null,
  expert_prediction: null,
  prediction_editable: true,
};
