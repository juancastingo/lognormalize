from __future__ import annotations

from typing import Iterable, Iterator, Optional, TextIO
from .models import NormalizedLog
from .registry import DEFAULT_REGISTRY, ParserRegistry


def normalize_stream(
    lines: Iterable[str],
    format: Optional[str] = None,
    registry: Optional[ParserRegistry] = None,
    skip_empty: bool = True,
) -> Iterator[NormalizedLog]:
    """Streamingly normalize lines from any iterable (file, generator, stdin).

    Yields:
        NormalizedLog instances.
    """
    reg = registry or DEFAULT_REGISTRY
    for line in lines:
        if skip_empty and not line.strip():
            continue
        yield reg.normalize(line, specific_parser=format)


def stream_to_jsonl(
    lines: Iterable[str],
    output_stream: TextIO,
    format: Optional[str] = None,
    registry: Optional[ParserRegistry] = None,
    flush: bool = True,
) -> int:
    """Normalize stream and write JSONL formatted records directly to output_stream.

    Returns:
        Total number of processed records.
    """
    count = 0
    for record in normalize_stream(lines, format=format, registry=registry):
        output_stream.write(record.to_json() + "\n")
        if flush:
            output_stream.flush()
        count += 1
    return count
