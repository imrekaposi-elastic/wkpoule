"""Cache key builders and patterns for wkpoule endpoints (Phase 3 consumers)."""

PREFIX = "wkpoule"


class CacheKeys:
    PREFIX = PREFIX

    @staticmethod
    def rankings(page: int, page_size: int) -> str:
        return f"{PREFIX}:rankings:page={page}:size={page_size}"

    @staticmethod
    def rankings_me(user_id: int) -> str:
        return f"{PREFIX}:rankings:me:user={user_id}"

    @staticmethod
    def rankings_pattern() -> str:
        return f"{PREFIX}:rankings:*"

    @staticmethod
    def matches_list(
        stage: str | None,
        group: str | None,
        search: str | None,
        page: int,
        page_size: int,
        predicted_teams: bool,
        user_id: int,
    ) -> str:
        stage_part = stage or "all"
        group_part = group or "all"
        search_part = (search or "").strip().casefold() or "none"
        return (
            f"{PREFIX}:matches:list:stage={stage_part}:group={group_part}:"
            f"search={search_part}:page={page}:size={page_size}:"
            f"pred={int(predicted_teams)}:user={user_id}"
        )

    @staticmethod
    def match_detail(match_id: int, predicted_teams: bool, user_id: int) -> str:
        return (
            f"{PREFIX}:matches:detail:id={match_id}:"
            f"pred={int(predicted_teams)}:user={user_id}"
        )

    @staticmethod
    def matches_pattern() -> str:
        return f"{PREFIX}:matches:*"

    @staticmethod
    def subgroup_detail(subgroup_id: int, user_id: int, page: int, page_size: int) -> str:
        return (
            f"{PREFIX}:subgroups:detail:id={subgroup_id}:user={user_id}:"
            f"page={page}:size={page_size}"
        )

    @staticmethod
    def subgroup_detail_pattern(subgroup_id: int) -> str:
        return f"{PREFIX}:subgroups:detail:id={subgroup_id}:*"

    @staticmethod
    def subgroups_pattern() -> str:
        return f"{PREFIX}:subgroups:*"

    @staticmethod
    def virtual_groups(user_id: int) -> str:
        return f"{PREFIX}:predictions:virtual-groups:user={user_id}"

    @staticmethod
    def virtual_groups_pattern() -> str:
        return f"{PREFIX}:predictions:virtual-groups:*"

    @staticmethod
    def teams_list() -> str:
        return f"{PREFIX}:teams:list"

    @staticmethod
    def teams_pattern() -> str:
        return f"{PREFIX}:teams:*"
