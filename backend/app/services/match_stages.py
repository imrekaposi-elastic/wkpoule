"""Match stage helpers (group vs knockout)."""

from __future__ import annotations

KNOCKOUT_STAGES = frozenset(
    {
        "round_of_32",
        "round_of_16",
        "quarter_final",
        "semi_final",
        "third_place",
        "final",
    }
)

# From round of 16 onward (2nd knockout round after the round of 32).
KNOCKOUT_SECOND_ROUND_ONWARDS = frozenset(
    {
        "round_of_16",
        "quarter_final",
        "semi_final",
        "third_place",
        "final",
    }
)


def is_knockout_stage(stage: str) -> bool:
    return stage in KNOCKOUT_STAGES


def is_second_knockout_round_onwards(stage: str) -> bool:
    return stage in KNOCKOUT_SECOND_ROUND_ONWARDS
