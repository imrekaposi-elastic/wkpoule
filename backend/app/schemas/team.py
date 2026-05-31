from pydantic import BaseModel, Field


class TeamPlayerOut(BaseModel):
    id: int
    name: str
    position: str
    shirt_number: int
    club: str
    height_cm: int
    weight_kg: int
    caps: int

    model_config = {"from_attributes": True}


class TeamProfileTextOut(BaseModel):
    qualification_en: str | None = None
    qualification_nl: str | None = None
    qualification_pt: str | None = None
    qualification_de: str | None = None
    qualification_es: str | None = None
    qualification_it: str | None = None
    qualification_he: str | None = None
    strengths_en: str | None = None
    strengths_nl: str | None = None
    strengths_pt: str | None = None
    strengths_de: str | None = None
    strengths_es: str | None = None
    strengths_it: str | None = None
    strengths_he: str | None = None
    weaknesses_en: str | None = None
    weaknesses_nl: str | None = None
    weaknesses_pt: str | None = None
    weaknesses_de: str | None = None
    weaknesses_es: str | None = None
    weaknesses_it: str | None = None
    weaknesses_he: str | None = None

    model_config = {"from_attributes": True}


class TeamSummaryOut(TeamProfileTextOut):
    id: int
    name: str
    fifa_code: str
    group_letter: str
    world_ranking: int
    flag_url: str


class TeamDetailOut(TeamSummaryOut):
    players: list[TeamPlayerOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}
