"""Curate reproducible high-leverage bullpen decision scenarios."""

from __future__ import annotations

from datetime import timedelta
from typing import Iterable

import pandas as pd
import requests


def resolve_mlb_player_names(
    player_ids: Iterable[int],
    *,
    known_names: dict[int, str] | None = None,
) -> dict[int, str]:
    """Resolve a small set of MLBAM identifiers for offline scenario storage."""

    names = dict(known_names or {})
    unresolved = sorted({int(value) for value in player_ids if int(value) not in names})
    for offset in range(0, len(unresolved), 50):
        batch = unresolved[offset : offset + 50]
        response = requests.get(
            "https://statsapi.mlb.com/api/v1/people",
            params={"personIds": ",".join(str(value) for value in batch)},
            timeout=30,
        )
        response.raise_for_status()
        for person in response.json().get("people", []):
            names[int(person["id"])] = str(person["fullName"])
    return names


def _recent_reliever_candidates(
    workload: pd.DataFrame,
    plate_appearances: pd.DataFrame,
    *,
    game_pk: int,
    game_date: pd.Timestamp,
    at_bat_number: int,
    fielding_team: str,
    actual_pitcher_id: int,
    current_pitcher_id: int,
    target_count: int = 4,
) -> list[int]:
    """Build a plausible candidate pool from recent relief usage."""

    prior_in_game = set(
        plate_appearances.loc[
            (plate_appearances["game_pk"].eq(game_pk))
            & (plate_appearances["at_bat_number"].lt(at_bat_number)),
            "pitcher_id",
        ].astype(int)
    )
    cutoff_start = game_date - timedelta(days=30)
    recent = workload.loc[
        workload["fielding_team"].eq(fielding_team)
        & workload["game_date"].lt(game_date)
        & workload["game_date"].ge(cutoff_start)
        & workload["is_relief_appearance"]
    ].copy()
    if recent.empty:
        return []

    summary = (
        recent.groupby("pitcher_id", observed=True, as_index=False)
        .agg(
            appearances=("game_pk", "nunique"),
            most_recent_game=("game_date", "max"),
            recent_pitch_count=("pitch_count", "sum"),
        )
        .sort_values(
            ["appearances", "most_recent_game", "recent_pitch_count"],
            ascending=[False, False, True],
        )
    )

    selected: list[int] = []
    for pitcher_id in (actual_pitcher_id, current_pitcher_id):
        if pitcher_id not in selected:
            selected.append(pitcher_id)
    for pitcher_id in summary["pitcher_id"].astype(int):
        if pitcher_id in selected:
            continue
        if pitcher_id in prior_in_game:
            continue
        selected.append(pitcher_id)
        if len(selected) >= target_count:
            break
    return selected[:target_count]


def find_scenario_candidates(
    plate_appearances: pd.DataFrame,
    workload: pd.DataFrame,
    *,
    limit: int = 12,
) -> list[dict[str, object]]:
    """Find high-leverage late-game pitching changes for manual review."""

    ordered = plate_appearances.sort_values(
        ["game_date", "game_pk", "at_bat_number"]
    ).reset_index(drop=True)
    ordered["previous_pitcher_id"] = ordered.groupby(
        ["game_pk", "inning", "inning_half"], observed=True
    )["pitcher_id"].shift(1)
    ordered["pitching_change"] = (
        ordered["previous_pitcher_id"].notna()
        & ordered["pitcher_id"].ne(ordered["previous_pitcher_id"])
    )
    ordered["score_margin"] = (
        ordered["home_score_before"] - ordered["away_score_before"]
    ).abs()
    ordered["base_count"] = ordered[
        ["on_1b_before", "on_2b_before", "on_3b_before"]
    ].sum(axis=1)
    fielding_wp = ordered["home_win_exp"].where(
        ordered["inning_half"].eq("TOP"), 1.0 - ordered["home_win_exp"]
    )
    ordered["fielding_wp"] = fielding_wp
    ordered["leverage_score"] = (
        ordered["inning"].clip(upper=12) / 12.0
        + (2 - ordered["score_margin"].clip(upper=2)) * 0.45
        + ordered["base_count"] * 0.30
        + (2 - ordered["outs_before"].clip(upper=2)) * 0.10
        + (0.5 - (ordered["fielding_wp"] - 0.5).abs()).clip(lower=0) * 0.8
    )

    eligible = ordered.loc[
        ordered["pitching_change"]
        & ordered["inning"].ge(7)
        & ordered["score_margin"].le(2)
        & ordered["fielding_wp"].between(0.10, 0.90)
    ].sort_values(["leverage_score", "game_date"], ascending=[False, False])

    scenarios: list[dict[str, object]] = []
    used_games: set[int] = set()
    used_teams: set[str] = set()
    for row in eligible.itertuples(index=True):
        game_pk = int(row.game_pk)
        fielding_team = str(row.fielding_team)
        if game_pk in used_games:
            continue
        # Prefer breadth, but allow a repeated team if needed after six cases.
        if fielding_team in used_teams and len(scenarios) < 6:
            continue

        game_future = ordered.loc[
            ordered["game_pk"].eq(game_pk)
            & ordered["at_bat_number"].ge(row.at_bat_number)
            & ordered["batting_team"].eq(row.batting_team)
        ].sort_values("at_bat_number")
        upcoming = game_future["batter_id"].astype(int).head(3).tolist()
        if len(upcoming) < 3:
            continue

        candidates = _recent_reliever_candidates(
            workload,
            ordered,
            game_pk=game_pk,
            game_date=pd.Timestamp(row.game_date),
            at_bat_number=int(row.at_bat_number),
            fielding_team=fielding_team,
            actual_pitcher_id=int(row.pitcher_id),
            current_pitcher_id=int(row.previous_pitcher_id),
        )
        if len(candidates) < 3:
            continue

        bases = {
            "first": bool(row.on_1b_before),
            "second": bool(row.on_2b_before),
            "third": bool(row.on_3b_before),
        }
        date_text = pd.Timestamp(row.game_date).date().isoformat()
        scenario_id = f"{date_text}-{fielding_team.lower()}-{game_pk}"
        scenarios.append(
            {
                "scenario_id": scenario_id,
                "title": (
                    f"{fielding_team} bullpen decision · {row.inning_half.title()} "
                    f"{int(row.inning)}"
                ),
                "is_flagship": False,
                "game_pk": game_pk,
                "game_date": date_text,
                "as_of_timestamp": f"{date_text}T00:00:00Z",
                "batting_team": str(row.batting_team),
                "fielding_team": fielding_team,
                "home_team": str(row.home_team),
                "away_team": str(row.away_team),
                "inning": int(row.inning),
                "inning_half": str(row.inning_half),
                "home_score": int(row.home_score_before),
                "away_score": int(row.away_score_before),
                "outs": int(row.outs_before),
                "bases": bases,
                "current_pitcher_id": int(row.previous_pitcher_id),
                "upcoming_batter_ids": upcoming,
                "actual_choice_id": int(row.pitcher_id),
                "candidate_reliever_ids": candidates,
                "at_bat_number": int(row.at_bat_number),
                "fielding_win_probability_before": float(row.fielding_wp),
                "leverage_score": float(row.leverage_score),
                "decision_note": (
                    "Late-game pitching change with a close score; candidate alternatives "
                    "come from the club's recent relief usage and exclude pitchers already used."
                ),
                "source_urls": [f"https://www.mlb.com/gameday/{game_pk}/final/box"],
                "manual_reviewed": False,
            }
        )
        used_games.add(game_pk)
        used_teams.add(fielding_team)
        if len(scenarios) >= limit:
            break
    return scenarios


def attach_player_names(
    scenarios: list[dict[str, object]],
    names: dict[int, str],
) -> list[dict[str, object]]:
    """Store display names in the offline scenario artifact."""

    for scenario in scenarios:
        player_ids = {
            int(scenario["current_pitcher_id"]),
            int(scenario["actual_choice_id"]),
            *[int(value) for value in scenario["candidate_reliever_ids"]],
            *[int(value) for value in scenario["upcoming_batter_ids"]],
        }
        scenario["player_names"] = {
            str(player_id): names.get(player_id, f"MLB #{player_id}")
            for player_id in sorted(player_ids)
        }
    return scenarios
