import json

import numpy as np

from src.config import ARTIFACTS_DIR


def _scenarios():
    return json.loads((ARTIFACTS_DIR / "runtime_scenarios.json").read_text(encoding="utf-8"))


def test_runtime_scenario_contracts() -> None:
    scenarios = _scenarios()
    assert len(scenarios) == 3
    assert sum(bool(item["is_flagship"]) for item in scenarios) == 1
    for scenario in scenarios:
        assert scenario["manual_reviewed"] is True
        assert 3 <= len(scenario["candidate_reliever_ids"]) <= 5
        assert scenario["actual_choice_id"] in scenario["candidate_reliever_ids"]
        assert len(scenario["upcoming_batter_ids"]) == 3
        assert len(scenario["default_ranking"]) == len(scenario["candidate_reliever_ids"])
        assert scenario["default_ranking"][0]["is_recommended"] is True
        for candidate_id in scenario["candidate_reliever_ids"]:
            probabilities = np.asarray(scenario["matchup_probabilities"][str(candidate_id)])
            assert probabilities.shape == (3, 4)
            assert np.all(probabilities >= 0)
            assert np.allclose(probabilities.sum(axis=1), 1.0)


def test_profiles_are_strictly_before_scenario() -> None:
    for scenario in _scenarios():
        for evidence in scenario["candidate_evidence"]:
            as_of = evidence["profile_as_of_date"]
            assert as_of is None or as_of < scenario["game_date"]
