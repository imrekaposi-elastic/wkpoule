"""Cache key builders and patterns for wkpoule endpoints (Phase 3 consumers)."""

PREFIX = "wkpoule"


class CacheKeys:
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
    def matches_list(stage: str | None, page: int, page_size: int) -> str:
        stage_part = stage or "all"
        return f"{PREFIX}:matches:list:stage={stage_part}:page={page}:size={page_size}"

    @staticmethod
    def match_detail(match_id: int) -> str:
        return f"{PREFIX}:matches:detail:id={match_id}"

    @staticmethod
    def matches_pattern() -> str:
        return f"{PREFIX}:matches:*"

    @staticmethod
    def subgroup_detail(subgroup_id: int) -> str:
        return f"{PREFIX}:subgroups:detail:id={subgroup_id}"

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
