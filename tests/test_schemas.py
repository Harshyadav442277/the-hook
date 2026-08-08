import pandas as pd

from src.data.schemas import (
    DOCUMENTED_EXCLUSIONS,
    OUTCOME_EVENT_MAP,
    map_outcome,
    validate_probe_dataframe,
)


def _complete_frame(events: list[str]) -> pd.DataFrame:
    rows = len(events)
    return pd.DataFrame(
        {
            "game_pk": [1] * rows,
            "game_date": ["2026-07-01"] * rows,
            "inning": [7] * rows,
            "inning_topbot": ["Top"] * rows,
            "outs_when_up": [1] * rows,
            "on_1b": [pd.NA] * rows,
            "on_2b": [pd.NA] * rows,
            "on_3b": [pd.NA] * rows,
            "home_score": [2] * rows,
            "away_score": [2] * rows,
            "post_home_score": [2] * rows,
            "post_away_score": [2] * rows,
            "pitcher": [10] * rows,
            "batter": [20] * rows,
            "p_throws": ["R"] * rows,
            "stand": ["L"] * rows,
            "pitch_type": ["FF"] * rows,
            "events": events,
            "at_bat_number": list(range(1, rows + 1)),
            "pitcher_days_since_prev_game": [2] * rows,
        }
    )


def test_canonical_event_mapping() -> None:
    assert map_outcome("strikeout") == "OUT"
    assert map_outcome("walk") == "FREE_PASS"
    assert map_outcome("single") == "SINGLE"
    assert map_outcome("home_run") == "EXTRA_BASE"
    assert map_outcome("field_error") is None
    assert "field_error" in DOCUMENTED_EXCLUSIONS


def test_mapping_classes_are_exact() -> None:
    assert set(OUTCOME_EVENT_MAP.values()) == {
        "OUT",
        "FREE_PASS",
        "SINGLE",
        "EXTRA_BASE",
    }


def test_complete_accounted_frame_passes_probe() -> None:
    report = validate_probe_dataframe(
        _complete_frame(
            ["field_out", "walk", "single", "double", "field_error", "truncated_pa"]
        )
    )
    assert report["schema_pass"] is True
    assert report["mapping_pass"] is True
    assert report["accounted_rate"] == 1.0
    assert report["unknown_events"] == {}


def test_unknown_terminal_event_fails_mapping_gate() -> None:
    report = validate_probe_dataframe(_complete_frame(["field_out", "mystery_event"]))
    assert report["mapping_pass"] is False
    assert report["unknown_events"] == {"mystery_event": 1}
