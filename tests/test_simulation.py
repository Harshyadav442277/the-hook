import numpy as np

from src.simulation.engine import rank_candidates, simulate_candidate


class _StateModel:
    def predict_proba(self, frame):
        score = frame["fielding_score_diff"].to_numpy(dtype=float)
        probability = 1.0 / (1.0 + np.exp(-0.8 * score))
        return np.column_stack([1.0 - probability, probability])


def _scenario():
    return {
        "inning": 7,
        "inning_half": "TOP",
        "outs": 1,
        "bases": {"first": True, "second": False, "third": False},
        "home_score": 3,
        "away_score": 2,
    }


def test_simulation_is_deterministic_and_bounded() -> None:
    probabilities = np.array([[0.75, 0.10, 0.10, 0.05]] * 3)
    first = simulate_candidate(
        _scenario(), probabilities, _StateModel(), simulation_count=500, seed=42
    )
    second = simulate_candidate(
        _scenario(), probabilities, _StateModel(), simulation_count=500, seed=42
    )
    assert first == second
    assert 0.0 <= first["estimated_win_probability"] <= 1.0
    assert first["expected_runs_allowed"] >= 0.0


def test_clearly_superior_pitcher_has_better_result() -> None:
    strong = np.array([[0.90, 0.04, 0.04, 0.02]] * 3)
    weak = np.array([[0.45, 0.15, 0.20, 0.20]] * 3)
    strong_result = simulate_candidate(
        _scenario(), strong, _StateModel(), simulation_count=4_000, seed=7
    )
    weak_result = simulate_candidate(
        _scenario(), weak, _StateModel(), simulation_count=4_000, seed=7
    )
    assert strong_result["estimated_win_probability"] > weak_result["estimated_win_probability"]
    assert strong_result["expected_runs_allowed"] < weak_result["expected_runs_allowed"]


def test_ranking_marks_actual_recommendation_and_tie() -> None:
    ranked = rank_candidates(
        [
            {"candidate_id": 1, "estimated_win_probability": 0.600, "expected_runs_allowed": 0.4},
            {"candidate_id": 2, "estimated_win_probability": 0.603, "expected_runs_allowed": 0.3},
        ],
        actual_choice_id=1,
    )
    assert ranked[0]["candidate_id"] == 2
    assert ranked[0]["is_recommended"] is True
    assert ranked[1]["is_actual_choice"] is True
    assert ranked[1]["effectively_tied"] is True
