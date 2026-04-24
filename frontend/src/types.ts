export interface User {
  id: number;
  username: string;
  email: string;
  is_admin: boolean;
  preferred_language: string;
}

/** GET /admin/users */
export interface AdminUserRow {
  id: number;
  username: string;
  email: string;
  is_admin: boolean;
  preferred_language: string;
  created_at: string;
}

/** GET /subgroups/mine */
export interface SubgroupMine {
  id: number;
  name: string;
  member_count: number;
  my_role: string;
  unread_message_count: number;
}

/** GET /subgroups/invites/pending */
export interface SubgroupInvitePending {
  id: number;
  subgroup_id: number;
  subgroup_name: string;
  email: string;
  created_at: string;
}

/** GET /subgroups/:id */
export interface SubgroupMemberBrief {
  user_id: number;
  username: string;
  role: string;
}

/** GET /subgroups/:id */
export interface SubgroupDetail {
  id: number;
  name: string;
  my_role: string;
  members: SubgroupMemberBrief[];
  rankings: ParticipantRanking[];
}

/** GET /admin/subgroups */
export interface AdminSubgroupMember {
  user_id: number;
  username: string;
  role: string;
}

/** GET /admin/subgroups */
export interface AdminSubgroupRow {
  id: number;
  name: string;
  created_at: string;
  member_count: number;
  members: AdminSubgroupMember[];
}

/** GET /subgroups/:id/messages */
export interface SubgroupMessage {
  id: number;
  user_id: number;
  username: string;
  body: string;
  created_at: string;
}

export interface Team {
  id: number;
  name: string;
  fifa_code: string;
  group_letter: string;
  world_ranking: number;
  flag_url: string;
}

export interface Venue {
  id: number;
  name: string;
  city: string;
  country: string;
  capacity: number;
}

export interface FunComment {
  comment_text: string;
  comment_text_nl?: string;
  comment_text_pt?: string;
  comment_text_de?: string;
  style: string;
}

export interface ExpertPrediction {
  home_goals: number;
  away_goals: number;
  label: string;
}

export interface Match {
  id: number;
  match_number: number;
  stage: string;
  group_letter: string | null;
  home_team: Team | null;
  away_team: Team | null;
  /** FIFA-style bracket slots when resolved (e.g. E1 vs F3) */
  bracket_home_slot?: string | null;
  bracket_away_slot?: string | null;
  venue: Venue;
  kickoff_utc: string;
  home_score: number | null;
  away_score: number | null;
  status: string;
  fun_comment: FunComment | null;
  temperature_celsius: number | null;
  expert_prediction: ExpertPrediction | null;
  /** False when the match is within 4 hours of kickoff or not upcoming */
  prediction_editable: boolean;
}

export interface Prediction {
  id: number;
  user_id: number;
  username: string;
  match_id: number;
  home_score: number;
  away_score: number;
  points: number | null;
  created_at: string;
  updated_at: string;
}

export interface MyPrediction {
  match_id: number;
  match_number: number;
  home_team: string | null;
  away_team: string | null;
  home_score: number;
  away_score: number;
  points: number | null;
  match_status: string;
}

export interface ParticipantRanking {
  rank: number;
  user_id: number;
  username: string;
  total_points: number;
  correct_results: number;
  correct_scores: number;
  correct_goal_counts: number;
  predictions_made: number;
}

export interface GroupStanding {
  team_id: number;
  team_name: string;
  fifa_code: string;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goals_for: number;
  goals_against: number;
  goal_difference: number;
  points: number;
}

export interface GroupTable {
  group_letter: string;
  standings: GroupStanding[];
}

/** Predicted group table from current user's tips (GET /predictions/virtual-groups) */
export interface VirtualGroupTable extends GroupTable {
  third_place_qualifies: boolean | null;
}

/** GET /venues — scheduled row with heuristic hype score */
export interface VenueScheduledMatch {
  match_id: number;
  match_number: number;
  stage: string;
  group_letter: string | null;
  kickoff_utc: string;
  home_team_name: string | null;
  away_team_name: string | null;
  attractiveness_stars: number;
}

export interface VenueDetail {
  id: number;
  name: string;
  city: string;
  country: string;
  capacity: number;
  latitude: number;
  longitude: number;
  year_built: number | null;
  image_url: string | null;
  rating: number | null;
  review_en: string | null;
  review_nl: string | null;
  review_pt: string | null;
  review_de: string | null;
  expected_temp_celsius: number | null;
  city_attractiveness: number | null;
  accessibility_en: string | null;
  accessibility_nl: string | null;
  accessibility_pt: string | null;
  accessibility_de: string | null;
  matches: VenueScheduledMatch[];
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
