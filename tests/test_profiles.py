import pandas as pd

from src.config import LEAGUE_PRIORS
from src.features.profiles import add_all_prior_features, build_monthly_profiles


def _plate_appearances() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "game_pk": [1, 2, 3],
            "game_date": pd.to_datetime(["2026-05-01", "2026-05-02", "2026-06-01"]),
            "at_bat_number": [1, 1, 1],
            "pitcher_id": [10, 10, 10],
            "pitcher_name": ["Pitcher A"] * 3,
            "pitcher_hand": ["R"] * 3,
            "pitcher_days_since_prev_game": [5, 1, 3],
            "batter_id": [20, 21, 22],
            "batter_stand": ["L", "R", "L"],
            "outcome_class": ["OUT", "SINGLE", "OUT"],
            "is_strikeout": [1, 0, 0],
            "is_walk": [0, 0, 0],
            "woba_value": [0.0, 0.9, 0.0],
            "woba_denom": [1, 1, 1],
        }
    )


def test_first_profile_uses_only_league_prior() -> None:
    featured = add_all_prior_features(_plate_appearances())
    first = featured.iloc[0]
    assert first["pitcher_pa_before"] == 0
    assert first["pitcher_out_rate"] == LEAGUE_PRIORS["OUT"]
    assert first["pitcher_k_rate"] == LEAGUE_PRIORS["K_RATE"]


def test_later_profile_uses_only_previous_events() -> None:
    featured = add_all_prior_features(_plate_appearances())
    second = featured.iloc[1]
    assert second["pitcher_pa_before"] == 1
    assert second["pitcher_out_rate"] > LEAGUE_PRIORS["OUT"]
    assert second["pitcher_single_rate"] < LEAGUE_PRIORS["SINGLE"]


def test_monthly_profiles_are_unique_per_player_month() -> None:
    featured = add_all_prior_features(_plate_appearances())
    profiles = build_monthly_profiles(featured, role="pitcher")
    assert len(profiles) == 2
    assert profiles[["pitcher_id", "profile_month"]].duplicated().sum() == 0
