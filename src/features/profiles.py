"""Build leakage-safe, league-pooled pitcher and batter profiles."""

from __future__ import annotations

import pandas as pd

from src.config import LEAGUE_PRIORS, PROFILE_PRIOR_WEIGHT


OUTCOME_CLASSES = ("OUT", "FREE_PASS", "SINGLE", "EXTRA_BASE")


def _prior_cumulative(series: pd.Series, groups: pd.Series) -> pd.Series:
    return series.groupby(groups, observed=True).cumsum() - series


def add_prior_player_features(
    plate_appearances: pd.DataFrame,
    *,
    player_column: str,
    prefix: str,
) -> pd.DataFrame:
    """Add prior-only cumulative/shrunk features for one player role."""

    frame = plate_appearances.copy()
    groups = frame[player_column]
    prior_pa = frame.groupby(player_column, observed=True).cumcount().astype("int32")
    frame[f"{prefix}_pa_before"] = prior_pa

    for outcome in OUTCOME_CLASSES:
        indicator = frame["outcome_class"].eq(outcome).astype("int8")
        prior_count = _prior_cumulative(indicator, groups)
        frame[f"{prefix}_{outcome.lower()}_count_before"] = prior_count.astype("int32")
        frame[f"{prefix}_{outcome.lower()}_rate"] = (
            prior_count + PROFILE_PRIOR_WEIGHT * LEAGUE_PRIORS[outcome]
        ) / (prior_pa + PROFILE_PRIOR_WEIGHT)

    prior_k = _prior_cumulative(frame["is_strikeout"].astype("int8"), groups)
    prior_walk = _prior_cumulative(frame["is_walk"].astype("int8"), groups)
    frame[f"{prefix}_k_rate"] = (
        prior_k + PROFILE_PRIOR_WEIGHT * LEAGUE_PRIORS["K_RATE"]
    ) / (prior_pa + PROFILE_PRIOR_WEIGHT)
    frame[f"{prefix}_walk_rate"] = (
        prior_walk + PROFILE_PRIOR_WEIGHT * LEAGUE_PRIORS["WALK_RATE"]
    ) / (prior_pa + PROFILE_PRIOR_WEIGHT)

    woba_is_valid = frame["woba_value"].notna() & frame["woba_denom"].fillna(0).gt(0)
    woba_value = frame["woba_value"].fillna(0).where(woba_is_valid, 0.0)
    woba_count = woba_is_valid.astype("int8")
    prior_woba_sum = _prior_cumulative(woba_value, groups)
    prior_woba_count = _prior_cumulative(woba_count, groups)
    frame[f"{prefix}_woba_count_before"] = prior_woba_count.astype("int32")
    frame[f"{prefix}_woba"] = (
        prior_woba_sum + PROFILE_PRIOR_WEIGHT * LEAGUE_PRIORS["WOBA"]
    ) / (prior_woba_count + PROFILE_PRIOR_WEIGHT)
    return frame


def add_all_prior_features(plate_appearances: pd.DataFrame) -> pd.DataFrame:
    """Add pitcher then batter prior-only features to chronologically sorted PAs."""

    ordered = plate_appearances.sort_values(
        ["game_date", "game_pk", "at_bat_number"]
    ).reset_index(drop=True)
    with_pitcher = add_prior_player_features(
        ordered, player_column="pitcher_id", prefix="pitcher"
    )
    return add_prior_player_features(
        with_pitcher, player_column="batter_id", prefix="batter"
    )


def build_monthly_profiles(
    featured_pa: pd.DataFrame,
    *,
    role: str,
) -> pd.DataFrame:
    """Take the latest prior-only player profile observed in each calendar month."""

    if role not in {"pitcher", "batter"}:
        raise ValueError("role must be `pitcher` or `batter`")
    player_column = f"{role}_id"
    frame = featured_pa.copy()
    frame["profile_month"] = frame["game_date"].dt.to_period("M").astype(str)
    latest = (
        frame.sort_values(["game_date", "game_pk", "at_bat_number"])
        .groupby([player_column, "profile_month"], observed=True)
        .tail(1)
        .copy()
    )
    common = [
        player_column,
        "game_date",
        "profile_month",
        f"{role}_pa_before",
        f"{role}_out_rate",
        f"{role}_free_pass_rate",
        f"{role}_single_rate",
        f"{role}_extra_base_rate",
        f"{role}_k_rate",
        f"{role}_walk_rate",
        f"{role}_woba",
    ]
    role_fields = (
        ["pitcher_name", "pitcher_hand", "pitcher_days_since_prev_game"]
        if role == "pitcher"
        else ["batter_stand"]
    )
    result = latest[common + role_fields].rename(columns={"game_date": "as_of_date"})
    return result.sort_values([player_column, "as_of_date"]).reset_index(drop=True)
