"""Vectorized three-batter simulation and candidate ranking."""

from __future__ import annotations

from hashlib import sha256
from typing import Any

import numpy as np
import pandas as pd

from src.models.win_expectancy import STATE_FEATURES, prepare_state_features


OUTCOME_CLASSES = ["OUT", "FREE_PASS", "SINGLE", "EXTRA_BASE"]
XBH_SUBTYPES = np.array(["DOUBLE", "TRIPLE", "HOME_RUN"])
XBH_PROBABILITIES = np.array([0.58, 0.03, 0.39])


def stable_seed(scenario_id: str, candidate_id: int, simulation_count: int) -> int:
    material = f"{scenario_id}|{candidate_id}|{simulation_count}".encode("utf-8")
    return int.from_bytes(sha256(material).digest()[:4], "big")


def _draw_outcomes(
    rng: np.random.Generator,
    probabilities: np.ndarray,
    count: int,
) -> np.ndarray:
    cumulative = np.cumsum(probabilities)
    draws = rng.random(count)
    return np.searchsorted(cumulative, draws, side="right")


def simulate_candidate(
    scenario: dict[str, Any],
    matchup_probabilities: np.ndarray,
    state_model: Any,
    *,
    simulation_count: int = 2_000,
    seed: int | None = None,
) -> dict[str, float | int]:
    """Simulate at most three hitters and estimate original fielding-team WP."""

    probabilities = np.asarray(matchup_probabilities, dtype=float)
    if probabilities.shape != (3, 4):
        raise ValueError("matchup_probabilities must have shape (3, 4)")
    if not np.allclose(probabilities.sum(axis=1), 1.0, atol=1e-6):
        raise ValueError("Every matchup probability row must sum to one")
    if simulation_count < 1:
        raise ValueError("simulation_count must be positive")

    rng = np.random.default_rng(seed)
    n = simulation_count
    outs = np.full(n, int(scenario["outs"]), dtype=np.int8)
    first = np.full(n, bool(scenario["bases"]["first"]), dtype=bool)
    second = np.full(n, bool(scenario["bases"]["second"]), dtype=bool)
    third = np.full(n, bool(scenario["bases"]["third"]), dtype=bool)
    runs = np.zeros(n, dtype=np.int16)
    inning_ended = np.zeros(n, dtype=bool)

    for batter_index in range(3):
        active = ~inning_ended
        active_count = int(active.sum())
        if active_count == 0:
            break
        outcome = _draw_outcomes(rng, probabilities[batter_index], active_count)
        active_indices = np.flatnonzero(active)

        out_mask = outcome == 0
        outs[active_indices[out_mask]] += 1

        walk_indices = active_indices[outcome == 1]
        if len(walk_indices):
            forced_run = first[walk_indices] & second[walk_indices] & third[walk_indices]
            runs[walk_indices] += forced_run.astype(np.int16)
            old_first = first[walk_indices].copy()
            old_second = second[walk_indices].copy()
            old_third = third[walk_indices].copy()
            first[walk_indices] = True
            second[walk_indices] = old_second | old_first
            third[walk_indices] = old_third | (old_second & old_first)

        single_indices = active_indices[outcome == 2]
        if len(single_indices):
            runs[single_indices] += (
                second[single_indices].astype(np.int16)
                + third[single_indices].astype(np.int16)
            )
            old_first = first[single_indices].copy()
            first[single_indices] = True
            second[single_indices] = old_first
            third[single_indices] = False

        xbh_indices = active_indices[outcome == 3]
        if len(xbh_indices):
            subtypes = rng.choice(XBH_SUBTYPES, size=len(xbh_indices), p=XBH_PROBABILITIES)
            double_indices = xbh_indices[subtypes == "DOUBLE"]
            if len(double_indices):
                runs[double_indices] += (
                    second[double_indices].astype(np.int16)
                    + third[double_indices].astype(np.int16)
                )
                old_first = first[double_indices].copy()
                first[double_indices] = False
                second[double_indices] = True
                third[double_indices] = old_first
            triple_indices = xbh_indices[subtypes == "TRIPLE"]
            if len(triple_indices):
                runs[triple_indices] += (
                    first[triple_indices].astype(np.int16)
                    + second[triple_indices].astype(np.int16)
                    + third[triple_indices].astype(np.int16)
                )
                first[triple_indices] = False
                second[triple_indices] = False
                third[triple_indices] = True
            homer_indices = xbh_indices[subtypes == "HOME_RUN"]
            if len(homer_indices):
                runs[homer_indices] += (
                    1
                    + first[homer_indices].astype(np.int16)
                    + second[homer_indices].astype(np.int16)
                    + third[homer_indices].astype(np.int16)
                )
                first[homer_indices] = False
                second[homer_indices] = False
                third[homer_indices] = False

        inning_ended |= outs >= 3

    inning = np.full(n, int(scenario["inning"]), dtype=np.int16)
    initial_half = str(scenario["inning_half"]).upper()
    half_top = np.full(n, initial_half == "TOP", dtype=bool)
    ended_top = inning_ended & half_top
    ended_bottom = inning_ended & ~half_top
    # Advance terminal half-innings to a valid 0-out state.
    half_top[ended_top] = False
    half_top[ended_bottom] = True
    inning[ended_bottom] += 1
    outs[inning_ended] = 0
    first[inning_ended] = False
    second[inning_ended] = False
    third[inning_ended] = False

    home_score = np.full(n, int(scenario["home_score"]), dtype=np.int16)
    away_score = np.full(n, int(scenario["away_score"]), dtype=np.int16)
    if initial_half == "TOP":
        away_score += runs
    else:
        home_score += runs

    current_fielding_is_home = half_top
    score_diff = np.where(
        current_fielding_is_home,
        home_score - away_score,
        away_score - home_score,
    )
    state_rows = pd.DataFrame(
        {
            "inning": inning,
            "outs_before": outs,
            "on_1b_before": first,
            "on_2b_before": second,
            "on_3b_before": third,
            "fielding_team_is_home": current_fielding_is_home,
            "fielding_score_diff": score_diff,
        }
    )
    state_rows = prepare_state_features(state_rows)
    current_fielding_wp = state_model.predict_proba(state_rows[STATE_FEATURES])[:, 1]
    original_fielding_is_home = initial_half == "TOP"
    original_wp = np.where(
        current_fielding_is_home == original_fielding_is_home,
        current_fielding_wp,
        1.0 - current_fielding_wp,
    )
    return {
        "estimated_win_probability": float(original_wp.mean()),
        "expected_runs_allowed": float(runs.mean()),
        "simulation_count": simulation_count,
        "seed": int(seed) if seed is not None else -1,
    }


def rank_candidates(results: list[dict[str, Any]], actual_choice_id: int) -> list[dict[str, Any]]:
    actual = next(
        result for result in results if int(result["candidate_id"]) == int(actual_choice_id)
    )
    actual_wp = float(actual["estimated_win_probability"])
    ranked = sorted(
        results,
        key=lambda value: (
            -float(value["estimated_win_probability"]),
            float(value["expected_runs_allowed"]),
            int(value["candidate_id"]),
        ),
    )
    best_wp = float(ranked[0]["estimated_win_probability"])
    for index, result in enumerate(ranked, start=1):
        result["rank"] = index
        result["delta_vs_actual"] = float(result["estimated_win_probability"]) - actual_wp
        result["is_actual_choice"] = int(result["candidate_id"]) == int(actual_choice_id)
        result["is_recommended"] = index == 1
        result["effectively_tied"] = (best_wp - float(result["estimated_win_probability"])) < 0.005
    return ranked
