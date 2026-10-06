from __future__ import annotations

from typing import Dict, List, Optional
from .models import NormalizedLog
from .parsers import (
    BaseParser,
    JsonLogParser,
    CombinedLogParser,
    SyslogParser,
    LogfmtParser,
    StandardAppLogParser,
)


class ParserRegistry:
    """Registry maintaining available parsers and cascade detection."""

    def __init__(self, load_defaults: bool = True) -> None:
        self._parsers: Dict[str, BaseParser] = {}
        self._order: List[str] = []

        if load_defaults:
            self.register(JsonLogParser())
            self.register(CombinedLogParser())
            self.register(SyslogParser())
            self.register(LogfmtParser())
            self.register(StandardAppLogParser())

    def register(self, parser: BaseParser, prepend: bool = False) -> None:
        """Register a new parser. If prepend is True, prioritize it before existing parsers."""
        self._parsers[parser.name] = parser
        if parser.name in self._order:
            self._order.remove(parser.name)

        if prepend:
            self._order.insert(0, parser.name)
        else:
            self._order.append(parser.name)

    def get(self, name: str) -> Optional[BaseParser]:
        """Fetch parser by name."""
        return self._parsers.get(name)

    def normalize(self, line: str, specific_parser: Optional[str] = None) -> NormalizedLog:
        """Parse line using specified parser or automatic detection cascade.
        Falls back to a generic fallback NormalizedLog if no parser matches.
        """
        line_clean = line.rstrip("\r\n")
        if not line_clean.strip():
            return NormalizedLog(
                message="",
                raw=line_clean,
                level="INFO",
                parser="empty",
            )

        if specific_parser:
            parser = self._parsers.get(specific_parser)
            if not parser:
                raise ValueError(f"Unknown parser: '{specific_parser}'")
            parsed = parser.parse(line_clean)
            if parsed is not None:
                return parsed
        else:
            for name in self._order:
                parsed = self._parsers[name].parse(line_clean)
                if parsed is not None:
                    return parsed

        # Fallback if no specific parser matched
        return NormalizedLog(
            message=line_clean,
            raw=line_clean,
            level="INFO",
            parser="raw_fallback",
        )


# Global default registry instance
DEFAULT_REGISTRY = ParserRegistry()


def register_parser(parser: BaseParser, prepend: bool = True) -> None:
    """Register custom parser with default global registry."""
    DEFAULT_REGISTRY.register(parser, prepend=prepend)


def normalize_line(line: str, format: Optional[str] = None) -> NormalizedLog:
    """Normalize a single log line into a NormalizedLog."""
    return DEFAULT_REGISTRY.normalize(line, specific_parser=format)
