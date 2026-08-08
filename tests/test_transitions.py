from src.simulation.transitions import GameState, transition


def _state(**overrides) -> GameState:
    values = {
        "inning": 7,
        "inning_half": "TOP",
        "outs": 1,
        "on_first": False,
        "on_second": False,
        "on_third": False,
        "home_score": 3,
        "away_score": 2,
    }
    values.update(overrides)
    return GameState(**values)


def test_bases_loaded_walk_forces_one_run() -> None:
    result = transition(
        _state(on_first=True, on_second=True, on_third=True), "FREE_PASS"
    )
    assert result.away_score == 3
    assert result.on_first and result.on_second and result.on_third


def test_single_scores_runner_from_second() -> None:
    result = transition(_state(on_second=True), "SINGLE")
    assert result.away_score == 3
    assert result.on_first is True
    assert result.on_second is False


def test_double_advances_runner_from_first_to_third() -> None:
    result = transition(_state(on_first=True), "EXTRA_BASE", "DOUBLE")
    assert result.on_second is True
    assert result.on_third is True
    assert result.away_score == 2


def test_home_run_clears_bases_and_scores_everyone() -> None:
    result = transition(
        _state(on_first=True, on_second=True, on_third=True),
        "EXTRA_BASE",
        "HOME_RUN",
    )
    assert result.away_score == 6
    assert not result.on_first and not result.on_second and not result.on_third


def test_third_out_freezes_future_transition() -> None:
    ended = transition(_state(outs=2), "OUT")
    assert ended.outs == 3
    assert transition(ended, "EXTRA_BASE", "HOME_RUN") == ended
