from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from .registry import DEFAULT_REGISTRY, normalize_line
from .stream import stream_to_jsonl, normalize_stream


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lognormalize",
        description="Normalize diverse log formats (syslog, web access, JSON, logfmt, app logs) into structured models and JSONL",
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Input log files to normalize (reads from stdin if omitted or '-')",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["auto", "json", "web_access", "syslog", "logfmt", "standard_app"],
        default="auto",
        help="Specific parser format to enforce (default: auto)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "--min-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Filter records below this log severity level",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="lognormalize 0.1.0",
    )
    return parser


LEVEL_SEVERITY = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
}


def main(args: Optional[List[str]] = None) -> int:
    parser = create_parser()
    parsed = parser.parse_args(args)

    fmt = None if parsed.format == "auto" else parsed.format
    min_sev = LEVEL_SEVERITY.get(parsed.min_level, 0) if parsed.min_level else 0

    out_file = sys.stdout
    if parsed.output:
        out_file = open(parsed.output, "w", encoding="utf-8")

    try:
        def line_generator():
            if not parsed.files or parsed.files == ["-"]:
                for line in sys.stdin:
                    yield line
            else:
                for filename in parsed.files:
                    with open(filename, "r", encoding="utf-8", errors="replace") as f:
                        for line in f:
                            yield line

        for item in normalize_stream(line_generator(), format=fmt):
            item_sev = LEVEL_SEVERITY.get(item.level, 20)
            if item_sev >= min_sev:
                out_file.write(item.to_json() + "\n")
                out_file.flush()

        return 0
    finally:
        if parsed.output and out_file is not sys.stdout:
            out_file.close()


if __name__ == "__main__":
    sys.exit(main())
