"""Verify curated scenarios against official MLB game feeds.

This is an offline build/review helper. The Streamlit application never calls
MLB APIs.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCENARIO_PATH = PROJECT_ROOT / "data" / "scenarios" / "scenarios.json"
REPORT_PATH = PROJECT_ROOT / "reports" / "scenario_review.json"


def _normalize_half(value: object) -> str:
    text = str(value).upper()
    return "BOTTOM" if text in {"BOT", "BOTTOM"} else "TOP"


def _base_state_before(
    plays: list[dict[str, object]], target_index: int, inning: int, half: str
) -> dict[str, bool]:
    """Reconstruct occupancy from official runner movements in the half-inning."""

    occupied: dict[str, int] = {}
    for play in plays:
        if int(play["atBatIndex"]) >= target_index:
            break
        if int(play["about"]["inning"]) != inning:
            continue
        if _normalize_half(play["about"]["halfInning"]) != half:
            continue
        runners = play.get("runners", [])
        for runner in runners:
            movement = runner.get("movement", {})
            start = movement.get("start")
            if start in {"1B", "2B", "3B"}:
                occupied.pop(start, None)
        for runner in runners:
            movement = runner.get("movement", {})
            end = movement.get("end")
            if end in {"1B", "2B", "3B"} and not movement.get("isOut", False):
                occupied[end] = int(runner["details"]["runner"]["id"])
    return {
        "first": "1B" in occupied,
        "second": "2B" in occupied,
        "third": "3B" in occupied,
    }


def verify_scenario(scenario: dict[str, object]) -> dict[str, object]:
    game_pk = int(scenario["game_pk"])
    response = requests.get(
        f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live", timeout=30
    )
    response.raise_for_status()
    plays = response.json()["liveData"]["plays"]["allPlays"]
    target_index = int(scenario["at_bat_number"]) - 1
    play = next(item for item in plays if int(item["atBatIndex"]) == target_index)
    previous = next(
        (item for item in reversed(plays) if int(item["atBatIndex"]) < target_index),
        None,
    )
    batting_half = _normalize_half(scenario["inning_half"])
    same_batting_team = [
        item
        for item in plays
        if int(item["atBatIndex"]) >= target_index
        and _normalize_half(item["about"]["halfInning"]) == batting_half
    ]
    official_batters = [
        int(item["matchup"]["batter"]["id"]) for item in same_batting_team[:3]
    ]
    official_actual = int(play["matchup"]["pitcher"]["id"])
    official_previous = (
        int(previous["matchup"]["pitcher"]["id"]) if previous is not None else None
    )
    official_outs = int(previous["count"]["outs"]) if previous is not None else 0
    previous_result = previous["result"] if previous is not None else {}
    official_home = int(previous_result.get("homeScore", 0))
    official_away = int(previous_result.get("awayScore", 0))
    official_bases = _base_state_before(
        plays, target_index, int(scenario["inning"]), batting_half
    )

    checks = {
        "actual_pitcher": official_actual == int(scenario["actual_choice_id"]),
        "previous_pitcher": official_previous == int(scenario["current_pitcher_id"]),
        "upcoming_batters": official_batters == scenario["upcoming_batter_ids"],
        "inning": int(play["about"]["inning"]) == int(scenario["inning"]),
        "half": _normalize_half(play["about"]["halfInning"]) == batting_half,
        "outs": official_outs == int(scenario["outs"]),
        "score": official_home == int(scenario["home_score"])
        and official_away == int(scenario["away_score"]),
        "bases": official_bases == scenario["bases"],
        "actual_in_candidates": int(scenario["actual_choice_id"])
        in scenario["candidate_reliever_ids"],
        "candidate_count": 3 <= len(scenario["candidate_reliever_ids"]) <= 5,
    }
    return {
        "scenario_id": scenario["scenario_id"],
        "source_url": f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live",
        "official": {
            "actual_pitcher_id": official_actual,
            "previous_pitcher_id": official_previous,
            "upcoming_batter_ids": official_batters,
            "inning": int(play["about"]["inning"]),
            "inning_half": _normalize_half(play["about"]["halfInning"]),
            "outs": official_outs,
            "home_score": official_home,
            "away_score": official_away,
            "bases": official_bases,
        },
        "checks": checks,
        "passed": all(checks.values()),
    }


def main() -> int:
    scenarios = json.loads(SCENARIO_PATH.read_text(encoding="utf-8"))
    reviews = [verify_scenario(scenario) for scenario in scenarios]
    report = {"all_passed": all(item["passed"] for item in reviews), "reviews": reviews}
    if report["all_passed"]:
        review_by_id = {item["scenario_id"]: item for item in reviews}
        for scenario in scenarios:
            review = review_by_id[scenario["scenario_id"]]
            scenario["manual_reviewed"] = True
            scenario["reviewed_against"] = review["source_url"]
            if review["source_url"] not in scenario["source_urls"]:
                scenario["source_urls"].append(review["source_url"])
        SCENARIO_PATH.write_text(json.dumps(scenarios, indent=2), encoding="utf-8")

        build_report_path = PROJECT_ROOT / "reports" / "phase2_build.json"
        if build_report_path.exists():
            build_report = json.loads(build_report_path.read_text(encoding="utf-8"))
            build_report["manual_review_complete"] = True
            build_report["scenario_review_report"] = str(REPORT_PATH.relative_to(PROJECT_ROOT))
            build_report_path.write_text(
                json.dumps(build_report, indent=2), encoding="utf-8"
            )
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
