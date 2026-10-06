"""lognormalize - High-performance log normalization library and CLI."""

from .models import NormalizedLog, normalize_log_level
from .parsers import (
    BaseParser,
    JsonLogParser,
    CombinedLogParser,
    SyslogParser,
    LogfmtParser,
    StandardAppLogParser,
    RegexLogParser,
)
from .registry import (
    ParserRegistry,
    DEFAULT_REGISTRY,
    register_parser,
    normalize_line,
)
from .stream import normalize_stream, stream_to_jsonl

__version__ = "0.1.0"
__all__ = [
    "NormalizedLog",
    "normalize_log_level",
    "BaseParser",
    "JsonLogParser",
    "CombinedLogParser",
    "SyslogParser",
    "LogfmtParser",
    "StandardAppLogParser",
    "RegexLogParser",
    "ParserRegistry",
    "DEFAULT_REGISTRY",
    "register_parser",
    "normalize_line",
    "normalize_stream",
    "stream_to_jsonl",
]
