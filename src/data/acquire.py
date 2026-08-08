"""Bounded, restartable Statcast acquisition with local Parquet caching."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
from importlib.metadata import PackageNotFoundError, version
import json
from pathlib import Path
import sys
import time
from typing import Callable

import pandas as pd
import pyarrow.parquet as parquet

from src.config import RAW_DATA_DIR


StatcastFetcher = Callable[[str, str], pd.DataFrame]


@dataclass(frozen=True)
class ChunkResult:
    """Metadata for one requested date chunk."""

    start_date: str
    end_date: str
    cache_path: Path
    manifest_path: Path
    row_count: int
    cache_hit: bool


@dataclass(frozen=True)
class AcquisitionResult:
    """Combined frame and cache evidence for a bounded acquisition."""

    data: pd.DataFrame
    chunks: tuple[ChunkResult, ...]

    @property
    def cache_hits(self) -> int:
        return sum(chunk.cache_hit for chunk in self.chunks)

    @property
    def cache_misses(self) -> int:
        return len(self.chunks) - self.cache_hits


def _parse_iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"Expected an ISO date (YYYY-MM-DD), got {value!r}") from exc


def split_date_range(start_date: str, end_date: str, chunk_days: int) -> list[tuple[str, str]]:
    """Split an inclusive date range into inclusive bounded chunks."""

    start = _parse_iso_date(start_date)
    end = _parse_iso_date(end_date)
    if end < start:
        raise ValueError("end_date must not precede start_date")
    if chunk_days < 1 or chunk_days > 14:
        raise ValueError("chunk_days must be between 1 and 14")

    chunks: list[tuple[str, str]] = []
    cursor = start
    while cursor <= end:
        chunk_end = min(cursor + timedelta(days=chunk_days - 1), end)
        chunks.append((cursor.isoformat(), chunk_end.isoformat()))
        cursor = chunk_end + timedelta(days=1)
    return chunks


def _cache_paths(cache_dir: Path, start_date: str, end_date: str) -> tuple[Path, Path]:
    stem = f"statcast_{start_date}_{end_date}"
    return cache_dir / f"{stem}.parquet", cache_dir / f"{stem}.manifest.json"


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _package_version(package: str) -> str:
    try:
        return version(package)
    except PackageNotFoundError:
        return "unknown"


def _default_fetcher(start_date: str, end_date: str) -> pd.DataFrame:
    # Kept inside the offline acquisition boundary. Runtime app modules must
    # never import or invoke pybaseball.
    from pybaseball import statcast

    return statcast(start_dt=start_date, end_dt=end_date, verbose=False)


def _read_manifest(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _cache_is_valid(
    cache_path: Path,
    manifest_path: Path,
    start_date: str,
    end_date: str,
) -> bool:
    manifest = _read_manifest(manifest_path)
    if not cache_path.exists() or manifest is None:
        return False
    if manifest.get("start_date") != start_date or manifest.get("end_date") != end_date:
        return False

    try:
        metadata = parquet.ParquetFile(cache_path).metadata
        if metadata.num_rows != manifest.get("row_count"):
            return False
        if _file_sha256(cache_path) != manifest.get("sha256"):
            return False
    except (OSError, ValueError):
        return False
    return True


def _write_cache(
    frame: pd.DataFrame,
    cache_path: Path,
    manifest_path: Path,
    start_date: str,
    end_date: str,
) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = cache_path.with_suffix(".tmp")
    frame.to_parquet(temporary_path, index=False)
    temporary_path.replace(cache_path)

    manifest = {
        "source": "MLB Statcast via pybaseball",
        "start_date": start_date,
        "end_date": end_date,
        "row_count": int(len(frame)),
        "column_count": int(len(frame.columns)),
        "columns": list(frame.columns),
        "acquired_at_utc": datetime.now(timezone.utc).isoformat(),
        "pybaseball_version": _package_version("pybaseball"),
        "pandas_version": _package_version("pandas"),
        "pyarrow_version": _package_version("pyarrow"),
        "cache_file": cache_path.name,
        "sha256": _file_sha256(cache_path),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def acquire_statcast_range(
    start_date: str,
    end_date: str,
    *,
    chunk_days: int,
    cache_dir: Path = RAW_DATA_DIR,
    force: bool = False,
    fetcher: StatcastFetcher | None = None,
    max_attempts: int = 3,
    retry_delay_seconds: float = 1.0,
) -> AcquisitionResult:
    """Acquire an inclusive date range, using valid cached chunks when present."""

    fetch = fetcher or _default_fetcher
    frames: list[pd.DataFrame] = []
    results: list[ChunkResult] = []

    for chunk_start, chunk_end in split_date_range(start_date, end_date, chunk_days):
        cache_path, manifest_path = _cache_paths(cache_dir, chunk_start, chunk_end)
        cache_hit = not force and _cache_is_valid(
            cache_path, manifest_path, chunk_start, chunk_end
        )

        if cache_hit:
            frame = pd.read_parquet(cache_path)
        else:
            if max_attempts < 1:
                raise ValueError("max_attempts must be at least 1")
            for attempt in range(1, max_attempts + 1):
                try:
                    frame = fetch(chunk_start, chunk_end)
                    break
                except Exception as exc:
                    if attempt == max_attempts:
                        raise
                    print(
                        f"Statcast fetch failed for {chunk_start} through {chunk_end} "
                        f"(attempt {attempt}/{max_attempts}): {type(exc).__name__}. Retrying.",
                        file=sys.stderr,
                    )
                    time.sleep(retry_delay_seconds * attempt)
            if not isinstance(frame, pd.DataFrame):
                raise TypeError("Statcast fetcher must return a pandas DataFrame")
            # Off-season intervals legitimately contain no games. Persist the
            # empty response just like any other chunk so repeated builds stay
            # bounded and never re-query a known gap.
            _write_cache(frame, cache_path, manifest_path, chunk_start, chunk_end)

        frames.append(frame)
        results.append(
            ChunkResult(
                start_date=chunk_start,
                end_date=chunk_end,
                cache_path=cache_path,
                manifest_path=manifest_path,
                row_count=len(frame),
                cache_hit=cache_hit,
            )
        )

    combined = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return AcquisitionResult(data=combined, chunks=tuple(results))


def load_cached_statcast_range(
    start_date: str,
    end_date: str,
    *,
    chunk_days: int,
    columns: list[str] | None = None,
    cache_dir: Path = RAW_DATA_DIR,
) -> pd.DataFrame:
    """Load an already-acquired range without any network fallback.

    This is the only supported Phase 2 processing path: a missing or invalid
    cache fails closed instead of silently downloading during transformation.
    """

    frames: list[pd.DataFrame] = []
    for chunk_start, chunk_end in split_date_range(start_date, end_date, chunk_days):
        cache_path, manifest_path = _cache_paths(cache_dir, chunk_start, chunk_end)
        if not _cache_is_valid(cache_path, manifest_path, chunk_start, chunk_end):
            raise FileNotFoundError(
                f"Missing or invalid Statcast cache for {chunk_start} through {chunk_end}"
            )
        manifest = _read_manifest(manifest_path)
        if manifest is not None and manifest.get("row_count") == 0:
            continue
        frames.append(pd.read_parquet(cache_path, columns=columns))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
