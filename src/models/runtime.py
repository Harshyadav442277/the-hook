"""Build compact point-in-time inference artifacts for the offline app."""

from __future__ import annotations

from copy import deepcopy
from datetime import date
from typing import Any

import numpy as np
import pandas as pd

from src.config import LEAGUE_PRIORS
from src.models.explain import candidate_reasons
from src.models.matchup import MATCHUP_FEATURES
from src.simulation.engine import OUTCOME_CLASSES, rank_candidates, simulate_candidate, stable_seed


def display_name(value: str) -> str:
    """Normalize Baseball Savant's `Last, First` display style."""

    if "," not in value:
        return value
    last, first = (part.strip() for part in value.split(",", 1))
    return f"{first} {last}"


def _latest_profile(
    profiles: pd.DataFrame,
    player_column: str,
    player_id: int,
    cutoff: pd.Timestamp,
) -> pd.Series | None:
    rows = profiles.loc[
        profiles[player_column].eq(player_id)
        & pd.to_datetime(profiles["as_of_date"]).lt(cutoff)
    ].sort_values("as_of_date")
    return None if rows.empty else rows.iloc[-1]


def _fallback_profile(role: str) -> dict[str, Any]:
    return {
        f"{role}_pa_before": 0,
        f"{role}_out_rate": LEAGUE_PRIORS["OUT"],
        f"{role}_free_pass_rate": LEAGUE_PRIORS["FREE_PASS"],
        f"{role}_single_rate": LEAGUE_PRIORS["SINGLE"],
        f"{role}_extra_base_rate": LEAGUE_PRIORS["EXTRA_BASE"],
        f"{role}_k_rate": LEAGUE_PRIORS["K_RATE"],
        f"{role}_walk_rate": LEAGUE_PRIORS["WALK_RATE"],
        f"{role}_woba": LEAGUE_PRIORS["WOBA"],
    }


def _profile_values(row: pd.Series | None, role: str) -> dict[str, Any]:
    fallback = _fallback_profile(role)
    if row is None:
        return fallback
    return {key: row.get(key, value) for key, value in fallback.items()}


def _days_rest(
    workload: pd.DataFrame,
    pitcher_id: int,
    cutoff: pd.Timestamp,
    *,
    already_pitching: bool,
) -> int:
    if already_pitching:
        return 0
    prior = workload.loc[
        workload["pitcher_id"].eq(pitcher_id)
        & pd.to_datetime(workload["game_date"]).lt(cutoff)
    ]
    if prior.empty:
        return 7
    return max(0, min(30, int((cutoff - pd.to_datetime(prior["game_date"]).max()).days)))


def build_runtime_scenarios(
    scenarios: list[dict[str, Any]],
    pitcher_profiles: pd.DataFrame,
    batter_profiles: pd.DataFrame,
    workload: pd.DataFrame,
    matchup_model: Any,
    state_model: Any,
    *,
    simulation_count: int,
) -> list[dict[str, Any]]:
    """Attach strictly prior profiles, matrices, reasons, and default rankings."""

    class_order = list(matchup_model.named_steps["model"].classes_)
    reorder = [class_order.index(name) for name in OUTCOME_CLASSES]
    output: list[dict[str, Any]] = []

    for source in scenarios:
        scenario = deepcopy(source)
        cutoff = pd.Timestamp(scenario["game_date"])
        candidate_evidence: list[dict[str, Any]] = []
        probability_by_candidate: dict[str, list[list[float]]] = {}

        for candidate_id in scenario["candidate_reliever_ids"]:
            candidate_id = int(candidate_id)
            pitcher_row = _latest_profile(
                pitcher_profiles, "pitcher_id", candidate_id, cutoff
            )
            pitcher = _profile_values(pitcher_row, "pitcher")
            pitcher_hand = (
                str(pitcher_row.get("pitcher_hand", "R"))
                if pitcher_row is not None
                else "R"
            )
            days_rest = _days_rest(
                workload,
                candidate_id,
                cutoff,
                already_pitching=candidate_id == int(scenario["current_pitcher_id"]),
            )
            feature_rows: list[dict[str, Any]] = []
            for batter_id in scenario["upcoming_batter_ids"]:
                batter_row = _latest_profile(
                    batter_profiles, "batter_id", int(batter_id), cutoff
                )
                batter = _profile_values(batter_row, "batter")
                feature_rows.append(
                    {
                        **pitcher,
                        **batter,
                        "pitcher_days_since_prev_game": days_rest,
                        "pitcher_hand": pitcher_hand,
                        "batter_stand": (
                            str(batter_row.get("batter_stand", "R"))
                            if batter_row is not None
                            else "R"
                        ),
                    }
                )
            feature_frame = pd.DataFrame(feature_rows)[MATCHUP_FEATURES]
            probabilities = matchup_model.predict_proba(feature_frame)[:, reorder]
            if probabilities.shape != (3, 4) or not np.allclose(
                probabilities.sum(axis=1), 1.0
            ):
                raise RuntimeError("Invalid scenario matchup probability matrix")
            probability_by_candidate[str(candidate_id)] = probabilities.tolist()
            candidate_evidence.append(
                {
                    "candidate_id": candidate_id,
                    "candidate_name": display_name(
                        str(scenario["player_names"][str(candidate_id)])
                    ),
                    "pitcher_hand": pitcher_hand,
                    "pitcher_pa_before": int(pitcher["pitcher_pa_before"]),
                    "pitcher_k_rate": float(pitcher["pitcher_k_rate"]),
                    "pitcher_walk_rate": float(pitcher["pitcher_walk_rate"]),
                    "pitcher_woba": float(pitcher["pitcher_woba"]),
                    "days_rest": days_rest,
                    "mean_projected_out_probability": float(probabilities[:, 0].mean()),
                    "profile_as_of_date": (
                        pd.Timestamp(pitcher_row["as_of_date"]).date().isoformat()
                        if pitcher_row is not None
                        else None
                    ),
                    "uses_league_fallback": pitcher_row is None,
                }
            )

        results: list[dict[str, Any]] = []
        for evidence in candidate_evidence:
            candidate_id = int(evidence["candidate_id"])
            seed = stable_seed(scenario["scenario_id"], candidate_id, simulation_count)
            result = simulate_candidate(
                scenario,
                np.asarray(probability_by_candidate[str(candidate_id)]),
                state_model,
                simulation_count=simulation_count,
                seed=seed,
            )
            results.append(
                {
                    **result,
                    "scenario_id": scenario["scenario_id"],
                    "candidate_id": candidate_id,
                    "candidate_name": evidence["candidate_name"],
                    "reasons": candidate_reasons(evidence, candidate_evidence),
                }
            )

        scenario["display_names"] = {
            key: display_name(value) for key, value in scenario["player_names"].items()
        }
        scenario["candidate_evidence"] = candidate_evidence
        scenario["matchup_probabilities"] = probability_by_candidate
        scenario["default_ranking"] = rank_candidates(
            results, int(scenario["actual_choice_id"])
        )
        scenario["profile_cutoff_rule"] = "latest snapshot strictly before game_date"
        output.append(scenario)
    return output
