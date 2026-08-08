"""Pure single-state baseball transitions used for correctness tests."""

from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class GameState:
    inning: int
    inning_half: str
    outs: int
    on_first: bool
    on_second: bool
    on_third: bool
    home_score: int
    away_score: int


def _score_runs(state: GameState, runs: int) -> GameState:
    if state.inning_half == "TOP":
        return replace(state, away_score=state.away_score + runs)
    return replace(state, home_score=state.home_score + runs)


def transition(state: GameState, outcome: str, extra_base_subtype: str = "DOUBLE") -> GameState:
    """Apply the documented deterministic MVP advancement rules."""

    if state.outs >= 3:
        return state
    if outcome == "OUT":
        return replace(state, outs=state.outs + 1)
    if outcome == "FREE_PASS":
        run = int(state.on_first and state.on_second and state.on_third)
        scored = _score_runs(state, run)
        return replace(
            scored,
            on_first=True,
            on_second=state.on_second or state.on_first,
            on_third=state.on_third or (state.on_second and state.on_first),
        )
    if outcome == "SINGLE":
        scored = _score_runs(state, int(state.on_second) + int(state.on_third))
        return replace(
            scored,
            on_first=True,
            on_second=state.on_first,
            on_third=False,
        )
    if outcome != "EXTRA_BASE":
        raise ValueError(f"Unknown outcome: {outcome}")

    subtype = extra_base_subtype.upper()
    if subtype == "DOUBLE":
        scored = _score_runs(state, int(state.on_second) + int(state.on_third))
        return replace(
            scored,
            on_first=False,
            on_second=True,
            on_third=state.on_first,
        )
    if subtype == "TRIPLE":
        scored = _score_runs(
            state, int(state.on_first) + int(state.on_second) + int(state.on_third)
        )
        return replace(scored, on_first=False, on_second=False, on_third=True)
    if subtype == "HOME_RUN":
        scored = _score_runs(
            state,
            1 + int(state.on_first) + int(state.on_second) + int(state.on_third),
        )
        return replace(scored, on_first=False, on_second=False, on_third=False)
    raise ValueError(f"Unknown extra-base subtype: {extra_base_subtype}")
