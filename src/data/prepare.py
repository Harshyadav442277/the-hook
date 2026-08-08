"""Build compact Phase 2 tables from cached Statcast pitch data."""

from __future__ import annotations

import pandas as pd

from src.data.schemas import DOCUMENTED_EXCLUSIONS, OUTCOME_EVENT_MAP


PROCESSING_COLUMNS = [
    "game_pk",
    "game_date",
    "game_type",
    "home_team",
    "away_team",
    "inning",
    "inning_topbot",
    "outs_when_up",
    "on_1b",
    "on_2b",
    "on_3b",
    "home_score",
    "away_score",
    "post_home_score",
    "post_away_score",
    "bat_score",
    "post_bat_score",
    "pitcher",
    "batter",
    "player_name",
    "p_throws",
    "stand",
    "pitch_type",
    "release_speed",
    "events",
    "at_bat_number",
    "pitch_number",
    "woba_value",
    "woba_denom",
    "delta_home_win_exp",
    "home_win_exp",
    "pitcher_days_since_prev_game",
]


def _normalize_inning_half(series: pd.Series) -> pd.Series:
    return series.astype(str).str.upper().replace({"BOT": "BOTTOM"})


def build_plate_appearances(pitches: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    """Return canonical modelable terminal plate appearances and audit counts."""

    terminal = pitches.loc[pitches["events"].notna()].copy()
    terminal["events"] = terminal["events"].astype(str)
    terminal["outcome_class"] = terminal["events"].map(OUTCOME_EVENT_MAP)

    unknown = sorted(
        set(terminal.loc[terminal["outcome_class"].isna(), "events"])
        - set(DOCUMENTED_EXCLUSIONS)
    )
    if unknown:
        raise ValueError(f"Unknown terminal Statcast events: {unknown}")

    excluded_counts = (
        terminal.loc[terminal["outcome_class"].isna(), "events"]
        .value_counts()
        .sort_index()
        .to_dict()
    )
    modelable = terminal.loc[terminal["outcome_class"].notna()].copy()
    modelable.sort_values(
        ["game_date", "game_pk", "at_bat_number", "pitch_number"], inplace=True
    )

    # Last recorded pitch supplies the final score for each game.
    game_finals = (
        pitches.sort_values(["game_pk", "at_bat_number", "pitch_number"])
        .groupby("game_pk", observed=True)
        .tail(1)[["game_pk", "post_home_score", "post_away_score"]]
        .rename(
            columns={
                "post_home_score": "final_home_score",
                "post_away_score": "final_away_score",
            }
        )
    )
    modelable = modelable.merge(game_finals, on="game_pk", how="left", validate="many_to_one")

    modelable["game_date"] = pd.to_datetime(modelable["game_date"]).dt.normalize()
    modelable["inning_half"] = _normalize_inning_half(modelable["inning_topbot"])
    modelable["outs_before"] = pd.to_numeric(modelable["outs_when_up"], errors="coerce")
    for base in (1, 2, 3):
        modelable[f"on_{base}b_before"] = modelable[f"on_{base}b"].notna()
    modelable["home_score_before"] = pd.to_numeric(modelable["home_score"], errors="coerce")
    modelable["away_score_before"] = pd.to_numeric(modelable["away_score"], errors="coerce")
    modelable["runs_scored"] = (
        pd.to_numeric(modelable["post_bat_score"], errors="coerce")
        - pd.to_numeric(modelable["bat_score"], errors="coerce")
    ).clip(lower=0)
    modelable["home_team_won"] = modelable["final_home_score"] > modelable["final_away_score"]
    modelable["batting_team"] = modelable["home_team"].where(
        modelable["inning_half"].eq("BOTTOM"), modelable["away_team"]
    )
    modelable["fielding_team"] = modelable["away_team"].where(
        modelable["inning_half"].eq("BOTTOM"), modelable["home_team"]
    )
    modelable["pitcher_id"] = modelable["pitcher"]
    modelable["batter_id"] = modelable["batter"]
    modelable["pitcher_hand"] = modelable["p_throws"]
    modelable["batter_stand"] = modelable["stand"]
    modelable["event"] = modelable["events"]
    modelable["pitcher_name"] = modelable["player_name"]
    modelable["is_strikeout"] = modelable["events"].isin(
        ["strikeout", "strikeout_double_play"]
    ).astype("int8")
    modelable["is_walk"] = modelable["events"].isin(
        ["walk", "intent_walk", "hit_by_pitch"]
    ).astype("int8")
    modelable["woba_value"] = pd.to_numeric(modelable["woba_value"], errors="coerce")
    modelable["woba_denom"] = pd.to_numeric(modelable["woba_denom"], errors="coerce")

    keep = [
        "game_pk",
        "game_date",
        "game_type",
        "home_team",
        "away_team",
        "batting_team",
        "fielding_team",
        "inning",
        "inning_half",
        "outs_before",
        "on_1b_before",
        "on_2b_before",
        "on_3b_before",
        "home_score_before",
        "away_score_before",
        "final_home_score",
        "final_away_score",
        "pitcher_id",
        "pitcher_name",
        "batter_id",
        "pitcher_hand",
        "batter_stand",
        "event",
        "outcome_class",
        "runs_scored",
        "home_team_won",
        "at_bat_number",
        "pitch_type",
        "release_speed",
        "woba_value",
        "woba_denom",
        "is_strikeout",
        "is_walk",
        "home_win_exp",
        "delta_home_win_exp",
        "pitcher_days_since_prev_game",
    ]
    result = modelable[keep].reset_index(drop=True)
    audit = {
        "raw_pitch_rows": int(len(pitches)),
        "terminal_event_rows": int(len(terminal)),
        "modelable_pa_rows": int(len(result)),
        "documented_exclusion_rows": int(len(terminal) - len(result)),
        "documented_exclusion_counts": excluded_counts,
        "unknown_events": unknown,
        "outcome_counts": result["outcome_class"].value_counts().sort_index().to_dict(),
        "game_count": int(result["game_pk"].nunique()),
        "date_min": result["game_date"].min().date().isoformat(),
        "date_max": result["game_date"].max().date().isoformat(),
    }
    return result, audit


def build_pitcher_workload(pitches: pd.DataFrame) -> pd.DataFrame:
    """Aggregate pitch counts and rest evidence for each pitcher appearance."""

    frame = pitches.copy()
    frame["game_date"] = pd.to_datetime(frame["game_date"]).dt.normalize()
    frame["inning_half"] = _normalize_inning_half(frame["inning_topbot"])
    frame["fielding_team"] = frame["away_team"].where(
        frame["inning_half"].eq("BOTTOM"), frame["home_team"]
    )
    workload = (
        frame.groupby(
            ["pitcher", "game_pk", "game_date", "fielding_team"],
            observed=True,
            as_index=False,
        )
        .agg(
            pitcher_name=("player_name", "first"),
            pitcher_hand=("p_throws", "first"),
            pitch_count=("pitch_type", "size"),
            first_inning=("inning", "min"),
            last_inning=("inning", "max"),
            days_since_prev_game=("pitcher_days_since_prev_game", "max"),
        )
        .rename(columns={"pitcher": "pitcher_id"})
    )
    workload["is_relief_appearance"] = workload["first_inning"] > 1
    return workload.sort_values(["game_date", "game_pk", "pitcher_id"]).reset_index(drop=True)


def build_state_examples(plate_appearances: pd.DataFrame) -> pd.DataFrame:
    """Create compact game-state rows for the later win-expectancy model."""

    states = plate_appearances[
        [
            "game_pk",
            "game_date",
            "inning",
            "inning_half",
            "outs_before",
            "on_1b_before",
            "on_2b_before",
            "on_3b_before",
            "home_score_before",
            "away_score_before",
            "home_team_won",
        ]
    ].copy()
    states["fielding_team_is_home"] = states["inning_half"].eq("TOP")
    home_diff = states["home_score_before"] - states["away_score_before"]
    states["fielding_score_diff"] = home_diff.where(
        states["fielding_team_is_home"], -home_diff
    )
    states["fielding_team_won"] = states["home_team_won"].where(
        states["fielding_team_is_home"], ~states["home_team_won"]
    )
    return states.reset_index(drop=True)
