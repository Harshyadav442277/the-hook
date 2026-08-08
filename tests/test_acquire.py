from pathlib import Path

import pandas as pd

from src.data.acquire import (
    acquire_statcast_range,
    load_cached_statcast_range,
    split_date_range,
)


def _sample_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "game_pk": [1],
            "game_date": ["2026-07-01"],
            "inning": [7],
            "inning_topbot": ["Top"],
            "outs_when_up": [1],
            "on_1b": [100],
            "on_2b": [pd.NA],
            "on_3b": [pd.NA],
            "home_score": [2],
            "away_score": [2],
            "post_home_score": [2],
            "post_away_score": [2],
            "pitcher": [10],
            "batter": [20],
            "p_throws": ["R"],
            "stand": ["L"],
            "pitch_type": ["FF"],
            "events": ["field_out"],
            "at_bat_number": [50],
            "pitcher_days_since_prev_game": [2],
        }
    )


def test_split_date_range_is_inclusive_and_bounded() -> None:
    assert split_date_range("2026-07-01", "2026-07-05", 2) == [
        ("2026-07-01", "2026-07-02"),
        ("2026-07-03", "2026-07-04"),
        ("2026-07-05", "2026-07-05"),
    ]


def test_valid_cache_prevents_second_fetch(tmp_path: Path) -> None:
    calls: list[tuple[str, str]] = []

    def fake_fetcher(start_date: str, end_date: str) -> pd.DataFrame:
        calls.append((start_date, end_date))
        return _sample_frame()

    first = acquire_statcast_range(
        "2026-07-01",
        "2026-07-02",
        chunk_days=1,
        cache_dir=tmp_path,
        fetcher=fake_fetcher,
    )
    second = acquire_statcast_range(
        "2026-07-01",
        "2026-07-02",
        chunk_days=1,
        cache_dir=tmp_path,
        fetcher=fake_fetcher,
    )

    assert len(calls) == 2  # one call for each of the two chunks, only once
    assert first.cache_misses == 2
    assert first.cache_hits == 0
    assert second.cache_hits == 2
    assert second.cache_misses == 0
    assert len(second.data) == 2


def test_transient_fetch_failure_is_retried(tmp_path: Path) -> None:
    calls = 0

    def flaky_fetcher(start_date: str, end_date: str) -> pd.DataFrame:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise OSError("temporary source failure")
        return _sample_frame()

    result = acquire_statcast_range(
        "2026-07-01",
        "2026-07-01",
        chunk_days=1,
        cache_dir=tmp_path,
        fetcher=flaky_fetcher,
        retry_delay_seconds=0,
    )

    assert calls == 2
    assert result.cache_misses == 1
    assert len(result.data) == 1


def test_empty_offseason_chunk_is_cached_and_skipped_on_load(tmp_path: Path) -> None:
    calls = 0

    def empty_fetcher(start_date: str, end_date: str) -> pd.DataFrame:
        nonlocal calls
        calls += 1
        return pd.DataFrame()

    first = acquire_statcast_range(
        "2025-11-06",
        "2025-11-12",
        chunk_days=7,
        cache_dir=tmp_path,
        fetcher=empty_fetcher,
    )
    second = acquire_statcast_range(
        "2025-11-06",
        "2025-11-12",
        chunk_days=7,
        cache_dir=tmp_path,
        fetcher=empty_fetcher,
    )
    loaded = load_cached_statcast_range(
        "2025-11-06",
        "2025-11-12",
        chunk_days=7,
        cache_dir=tmp_path,
        columns=["game_pk"],
    )

    assert calls == 1
    assert first.cache_misses == 1
    assert second.cache_hits == 1
    assert first.data.empty and second.data.empty and loaded.empty
