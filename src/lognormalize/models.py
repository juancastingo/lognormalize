from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass
class NormalizedLog:
    """Standardized representation of a parsed log record."""

    message: str
    raw: str
    timestamp: Optional[str] = None
    level: str = "INFO"
    host: Optional[str] = None
    ip: Optional[str] = None
    process: Optional[str] = None
    pid: Optional[int] = None
    parser: str = "unknown"
    fields: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert normalized log entry to a dictionary, omitting None values."""
        res: Dict[str, Any] = {
            "timestamp": self.timestamp,
            "level": self.level,
            "message": self.message,
            "parser": self.parser,
            "raw": self.raw,
        }
        if self.host is not None:
            res["host"] = self.host
        if self.ip is not None:
            res["ip"] = self.ip
        if self.process is not None:
            res["process"] = self.process
        if self.pid is not None:
            res["pid"] = self.pid
        if self.fields:
            res["fields"] = self.fields
        return res

    def to_json(self) -> str:
        """Serialize normalized log entry to a JSON string."""
        return json.dumps(self.to_dict(), default=str, ensure_ascii=False)


def normalize_log_level(raw_level: Optional[str]) -> str:
    """Normalize common log levels into standard UPPERCASE strings."""
    if not raw_level:
        return "INFO"
    lvl = raw_level.strip().upper()
    mapping = {
        "WARN": "WARNING",
        "ERR": "ERROR",
        "FATAL": "CRITICAL",
        "EMERG": "CRITICAL",
        "ALERT": "CRITICAL",
        "CRIT": "CRITICAL",
        "DBG": "DEBUG",
        "TRACE": "DEBUG",
        "INF": "INFO",
        "NOTICE": "INFO",
    }
    return mapping.get(lvl, lvl if lvl in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL") else "INFO")
