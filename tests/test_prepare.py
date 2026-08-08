import pandas as pd

from src.data.prepare import build_plate_appearances, build_state_examples


def _pitch_rows() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "game_pk": [1, 1, 1],
            "game_date": ["2026-07-01"] * 3,
            "game_type": ["R"] * 3,
            "home_team": ["BOS"] * 3,
            "away_team": ["NYY"] * 3,
            "inning": [7, 7, 9],
            "inning_topbot": ["Top", "Top", "Bot"],
            "outs_when_up": [1, 1, 2],
            "on_1b": [pd.NA, pd.NA, pd.NA],
            "on_2b": [101, 101, pd.NA],
            "on_3b": [pd.NA, pd.NA, pd.NA],
            "home_score": [2, 2, 2],
            "away_score": [2, 2, 3],
            "post_home_score": [2, 2, 2],
            "post_away_score": [2, 3, 3],
            "bat_score": [2, 2, 2],
            "post_bat_score": [2, 3, 2],
            "pitcher": [10, 10, 11],
            "batter": [20, 20, 21],
            "player_name": ["Pitcher A", "Pitcher A", "Pitcher B"],
            "p_throws": ["R", "R", "L"],
            "stand": ["L", "L", "R"],
            "pitch_type": ["FF", "SL", "FF"],
            "release_speed": [95.0, 86.0, 94.0],
            "events": [pd.NA, "single", "field_out"],
            "at_bat_number": [50, 50, 80],
            "pitch_number": [1, 2, 1],
            "woba_value": [pd.NA, 0.9, 0.0],
            "woba_denom": [pd.NA, 1, 1],
            "delta_home_win_exp": [0.0, -0.1, 0.1],
            "home_win_exp": [0.5, 0.5, 0.1],
            "pitcher_days_since_prev_game": [2, 2, 1],
        }
    )


def test_plate_appearance_builds_canonical_state() -> None:
    plate_appearances, audit = build_plate_appearances(_pitch_rows())

    assert len(plate_appearances) == 2
    assert audit["modelable_pa_rows"] == 2
    first = plate_appearances.iloc[0]
    assert first["outcome_class"] == "SINGLE"
    assert bool(first["on_2b_before"]) is True
    assert first["runs_scored"] == 1
    assert first["fielding_team"] == "BOS"
    assert first["batting_team"] == "NYY"
    assert bool(first["home_team_won"]) is False
    bottom = plate_appearances.iloc[1]
    assert bottom["inning_half"] == "BOTTOM"
    assert bottom["batting_team"] == "BOS"
    assert bottom["fielding_team"] == "NYY"


def test_state_examples_use_fielding_team_perspective() -> None:
    plate_appearances, _ = build_plate_appearances(_pitch_rows())
    states = build_state_examples(plate_appearances)

    top_state = states.iloc[0]
    bottom_state = states.iloc[1]
    assert bool(top_state["fielding_team_is_home"]) is True
    assert bool(top_state["fielding_team_won"]) is False
    assert bool(bottom_state["fielding_team_is_home"]) is False
    assert bool(bottom_state["fielding_team_won"]) is True
