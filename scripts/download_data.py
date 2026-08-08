"""Run the bounded Phase 1 Statcast probe and write auditable reports."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (  # noqa: E402
    PROBE_CHUNK_DAYS,
    PROBE_END_DATE,
    PROBE_START_DATE,
    RAW_DATA_DIR,
    REPORTS_DIR,
)
from src.data.acquire import acquire_statcast_range  # noqa: E402
from src.data.schemas import validate_probe_dataframe  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-date", default=PROBE_START_DATE)
    parser.add_argument("--end-date", default=PROBE_END_DATE)
    parser.add_argument("--chunk-days", type=int, default=PROBE_CHUNK_DAYS)
    parser.add_argument("--force", action="store_true", help="Ignore valid local cache")
    return parser.parse_args()


def _markdown_report(report: dict[str, object]) -> str:
    verdict = "PASS" if report["phase1_probe_pass"] else "FAIL"
    lines = [
        "# Phase 1 Statcast Data Probe",
        "",
        f"Status: **{verdict}**  ",
        f"Generated: {report['generated_at_utc']}  ",
        f"Requested range: {report['start_date']} through {report['end_date']}  ",
        f"Python: {report['python_version']}  ",
        "",
        "## Acquisition",
        "",
        f"- Rows: {report['row_count']:,}",
        f"- Columns: {report['column_count']}",
        f"- Chunks: {report['chunk_count']}",
        f"- Cache hits: {report['cache_hits']}",
        f"- Cache misses/downloads: {report['cache_misses']}",
        "- Source: MLB Statcast/Baseball Savant via pybaseball",
        "",
        "## Schema",
        "",
        f"- Schema gate: {'PASS' if report['schema_pass'] else 'FAIL'}",
        f"- Missing required columns: {report['missing_required_columns'] or 'None'}",
        "- Workload support: days of rest is available directly as `pitcher_days_since_prev_game`; recent pitch counts are derivable by pitcher/game/date from pitch rows.",
        "",
        "## Terminal-event mapping",
        "",
        f"- Terminal events: {report['terminal_event_count']:,}",
        f"- Canonically mapped: {report['mapped_event_count']:,} ({report['approved_mapping_rate']:.2%})",
        f"- Documented exclusions: {report['documented_exclusion_count']:,}",
        f"- Accounted for: {report['accounted_rate']:.2%}",
        f"- Unknown events: {report['unknown_events'] or 'None'}",
        "",
        "### Canonical outcome counts",
        "",
    ]
    for outcome, count in sorted(report["outcome_counts"].items()):
        lines.append(f"- `{outcome}`: {count:,}")
    lines.extend(
        [
            "",
            "### Documented exclusions",
            "",
            *[f"- `{event}`" for event in report["documented_exclusion_events"]],
            "",
            "## Phase 2 decision",
            "",
            "Use 2025-03-27 through 2026-08-07 in seven-day cached chunks. Do not add 2024 unless Phase 2 exposes an evidence-based cold-start or sample-coverage problem.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    result = acquire_statcast_range(
        args.start_date,
        args.end_date,
        chunk_days=args.chunk_days,
        cache_dir=RAW_DATA_DIR,
        force=args.force,
    )
    report = validate_probe_dataframe(result.data)
    report.update(
        {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "python_version": platform.python_version(),
            "start_date": args.start_date,
            "end_date": args.end_date,
            "chunk_days": args.chunk_days,
            "chunk_count": len(result.chunks),
            "cache_hits": result.cache_hits,
            "cache_misses": result.cache_misses,
            "chunks": [
                {
                    "start_date": chunk.start_date,
                    "end_date": chunk.end_date,
                    "cache_file": chunk.cache_path.name,
                    "manifest_file": chunk.manifest_path.name,
                    "row_count": chunk.row_count,
                    "cache_hit": chunk.cache_hit,
                }
                for chunk in result.chunks
            ],
        }
    )

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "data_probe.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    (REPORTS_DIR / "data_probe.md").write_text(
        _markdown_report(report), encoding="utf-8"
    )

    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "phase1_probe_pass",
                    "row_count",
                    "column_count",
                    "terminal_event_count",
                    "approved_mapping_rate",
                    "accounted_rate",
                    "cache_hits",
                    "cache_misses",
                    "missing_required_columns",
                    "unknown_events",
                )
            },
            indent=2,
        )
    )
    return 0 if report["phase1_probe_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
