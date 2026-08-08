"""Statcast schema checks and canonical terminal-event mapping."""

from __future__ import annotations

from collections import Counter
from typing import Final

import pandas as pd

from src.config import OUTCOME_MAPPING_VERSION


REQUIRED_PROBE_COLUMNS: Final[tuple[str, ...]] = (
    "game_pk",
    "game_date",
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
    "pitcher",
    "batter",
    "p_throws",
    "stand",
    "pitch_type",
    "events",
    "at_bat_number",
    "pitcher_days_since_prev_game",
)

OUTCOME_EVENT_MAP: Final[dict[str, str]] = {
    # OUT
    "field_out": "OUT",
    "force_out": "OUT",
    "grounded_into_double_play": "OUT",
    "double_play": "OUT",
    "triple_play": "OUT",
    "fielders_choice_out": "OUT",
    "sac_fly": "OUT",
    "sac_bunt": "OUT",
    "sac_fly_double_play": "OUT",
    "strikeout": "OUT",
    "strikeout_double_play": "OUT",
    "other_out": "OUT",
    # FREE_PASS
    "walk": "FREE_PASS",
    "intent_walk": "FREE_PASS",
    "hit_by_pitch": "FREE_PASS",
    # SINGLE
    "single": "SINGLE",
    # EXTRA_BASE
    "double": "EXTRA_BASE",
    "triple": "EXTRA_BASE",
    "home_run": "EXTRA_BASE",
}

# These events either do not describe batter quality cleanly or do not fit the
# four-outcome transition model. They are retained in audit counts and excluded
# from model rows rather than being silently coerced.
DOCUMENTED_EXCLUSIONS: Final[frozenset[str]] = frozenset(
    {
        "catcher_interf",
        "field_error",
        "fielders_choice",
        "runner_double_play",
        # Statcast uses this for a plate appearance that ended without a
        # modelable baseball result (for example, a mid-PA interruption).
        "truncated_pa",
    }
)


def map_outcome(event: object) -> str | None:
    """Map a Statcast terminal event into the canonical four-class outcome."""

    if not isinstance(event, str):
        return None
    return OUTCOME_EVENT_MAP.get(event)


def terminal_plate_appearances(frame: pd.DataFrame) -> pd.DataFrame:
    """Return rows whose `events` field identifies a terminal PA result."""

    if "events" not in frame.columns:
        raise ValueError("Statcast frame is missing the `events` column")
    return frame.loc[frame["events"].notna()].copy()


def validate_probe_dataframe(frame: pd.DataFrame) -> dict[str, object]:
    """Build machine-readable Phase 1 schema and mapping evidence."""

    missing_columns = sorted(set(REQUIRED_PROBE_COLUMNS) - set(frame.columns))
    terminal = terminal_plate_appearances(frame) if "events" in frame.columns else frame.iloc[0:0]
    event_counts = Counter(str(value) for value in terminal.get("events", pd.Series(dtype=str)))

    mapped_count = sum(
        count for event, count in event_counts.items() if event in OUTCOME_EVENT_MAP
    )
    documented_exclusion_count = sum(
        count for event, count in event_counts.items() if event in DOCUMENTED_EXCLUSIONS
    )
    unknown_events = {
        event: count
        for event, count in sorted(event_counts.items())
        if event not in OUTCOME_EVENT_MAP and event not in DOCUMENTED_EXCLUSIONS
    }
    terminal_count = int(len(terminal))
    accounted_count = mapped_count + documented_exclusion_count

    required_groups = {
        "terminal_event": {"events"},
        "score": {"home_score", "away_score", "post_home_score", "post_away_score"},
        "inning_and_outs": {"inning", "inning_topbot", "outs_when_up"},
        "base_state": {"on_1b", "on_2b", "on_3b"},
        "handedness": {"p_throws", "stand"},
        "players": {"pitcher", "batter"},
        "pitch_profile": {"pitch_type"},
        "workload": {
            "game_date",
            "game_pk",
            "pitcher",
            "at_bat_number",
            "pitcher_days_since_prev_game",
        },
    }
    group_status = {
        group: sorted(columns) if columns.issubset(frame.columns) else []
        for group, columns in required_groups.items()
    }

    approved_mapping_rate = mapped_count / terminal_count if terminal_count else 0.0
    accounted_rate = accounted_count / terminal_count if terminal_count else 0.0
    schema_pass = not missing_columns and all(group_status.values())
    mapping_pass = terminal_count > 0 and accounted_rate >= 0.95 and not unknown_events

    outcome_counts: Counter[str] = Counter()
    for event, count in event_counts.items():
        outcome = OUTCOME_EVENT_MAP.get(event)
        if outcome is not None:
            outcome_counts[outcome] += count

    return {
        "outcome_mapping_version": OUTCOME_MAPPING_VERSION,
        "row_count": int(len(frame)),
        "column_count": int(len(frame.columns)),
        "required_columns_present": sorted(set(REQUIRED_PROBE_COLUMNS) & set(frame.columns)),
        "missing_required_columns": missing_columns,
        "required_group_status": group_status,
        "terminal_event_count": terminal_count,
        "mapped_event_count": mapped_count,
        "documented_exclusion_count": documented_exclusion_count,
        "approved_mapping_rate": approved_mapping_rate,
        "accounted_rate": accounted_rate,
        "outcome_counts": dict(outcome_counts),
        "event_counts": dict(sorted(event_counts.items())),
        "documented_exclusion_events": sorted(DOCUMENTED_EXCLUSIONS),
        "unknown_events": unknown_events,
        "schema_pass": schema_pass,
        "mapping_pass": mapping_pass,
        "phase1_probe_pass": schema_pass and mapping_pass,
    }
