from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime

from .models import NormalizedLog, normalize_log_level


class BaseParser(ABC):
    """Abstract base class for all log parsers."""

    name: str = "base"

    @abstractmethod
    def parse(self, line: str) -> Optional[NormalizedLog]:
        """Attempt to parse a log line. Returns NormalizedLog if successful, else None."""
        pass


class JsonLogParser(BaseParser):
    """Parser for JSON and JSONL structured log lines."""

    name: str = "json"

    def parse(self, line: str) -> Optional[NormalizedLog]:
        line_clean = line.strip()
        if not (line_clean.startswith("{") and line_clean.endswith("}")):
            return None

        try:
            data = json.loads(line_clean)
        except Exception:
            return None

        if not isinstance(data, dict):
            return None

        # Extract message
        message = ""
        for msg_key in ("message", "msg", "log", "text", "body"):
            if msg_key in data and isinstance(data[msg_key], str):
                message = data.pop(msg_key)
                break
        if not message:
            message = line_clean

        # Extract timestamp
        timestamp = None
        for ts_key in ("timestamp", "time", "ts", "@timestamp", "datetime", "date"):
            if ts_key in data:
                timestamp = str(data.pop(ts_key))
                break

        # Extract level
        level = "INFO"
        for lvl_key in ("level", "lvl", "severity", "log_level", "loglevel"):
            if lvl_key in data:
                level = normalize_log_level(str(data.pop(lvl_key)))
                break

        # Extract host / ip
        host = None
        ip = None
        for h_key in ("host", "hostname", "server"):
            if h_key in data:
                host = str(data.pop(h_key))
                break
        for ip_key in ("ip", "client_ip", "remote_addr"):
            if ip_key in data:
                ip = str(data.pop(ip_key))
                break

        # Extract process / pid
        process = None
        pid = None
        for p_key in ("process", "proc", "service", "app"):
            if p_key in data:
                process = str(data.pop(p_key))
                break
        for pid_key in ("pid", "process_id"):
            if pid_key in data:
                try:
                    pid = int(data.pop(pid_key))
                except (ValueError, TypeError):
                    pass
                break

        return NormalizedLog(
            message=message,
            raw=line,
            timestamp=timestamp,
            level=level,
            host=host,
            ip=ip,
            process=process,
            pid=pid,
            parser=self.name,
            fields=data,
        )


class CombinedLogParser(BaseParser):
    """Parser for Common Log Format (CLF) and Nginx/Apache Combined Access Logs."""

    name: str = "web_access"

    _REGEX = re.compile(
        r'^(?P<ip>\S+)\s+\S+\s+(?P<user>\S+)\s+\[(?P<timestamp>[^\]]+)\]\s+"(?P<method>[A-Z]+)\s+(?P<path>\S+)(?:\s+(?P<protocol>[^"]+))?"\s+(?P<status>\d{3})\s+(?P<bytes>\S+)(?:\s+"(?P<referer>[^"]*)"\s+"(?P<user_agent>[^"]*)")?'
    )

    def parse(self, line: str) -> Optional[NormalizedLog]:
        match = self._REGEX.match(line.strip())
        if not match:
            return None

        groups = match.groupdict()
        status = int(groups["status"])
        method = groups["method"]
        path = groups["path"]
        ip = groups["ip"]
        raw_ts = groups["timestamp"]

        # Infer level based on HTTP response status code
        level = "INFO"
        if status >= 500:
            level = "ERROR"
        elif status >= 400:
            level = "WARNING"

        fields: Dict[str, Any] = {
            "status": status,
            "method": method,
            "path": path,
        }
        if groups.get("bytes") and groups["bytes"] != "-":
            try:
                fields["bytes"] = int(groups["bytes"])
            except ValueError:
                pass
        if groups.get("user") and groups["user"] != "-":
            fields["user"] = groups["user"]
        if groups.get("referer") and groups["referer"] != "-":
            fields["referer"] = groups["referer"]
        if groups.get("user_agent") and groups["user_agent"] != "-":
            fields["user_agent"] = groups["user_agent"]

        message = f"{method} {path} HTTP {status}"

        return NormalizedLog(
            message=message,
            raw=line,
            timestamp=raw_ts,
            level=level,
            ip=ip,
            parser=self.name,
            fields=fields,
        )


class SyslogParser(BaseParser):
    """Parser for Syslog RFC 3164 and RFC 5424 formats."""

    name: str = "syslog"

    # RFC 3164: "Oct 11 22:14:15 myhost myproc[123]: message"
    _RFC3164 = re.compile(
        r"^(?:<(?P<pri>\d{1,3})>)?(?P<timestamp>[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(?P<host>\S+)\s+(?P<proc>[a-zA-Z0-9_\-\.\/]+)(?:\[(?P<pid>\d+)\])?:\s+(?P<msg>.*)$"
    )

    def parse(self, line: str) -> Optional[NormalizedLog]:
        match = self._RFC3164.match(line.strip())
        if not match:
            return None

        groups = match.groupdict()
        pid = int(groups["pid"]) if groups.get("pid") else None
        pri = int(groups["pri"]) if groups.get("pri") else None

        level = "INFO"
        if pri is not None:
            severity = pri % 8
            if severity <= 3:
                level = "ERROR"
            elif severity == 4:
                level = "WARNING"
            elif severity == 7:
                level = "DEBUG"

        fields: Dict[str, Any] = {}
        if pri is not None:
            fields["pri"] = pri

        return NormalizedLog(
            message=groups["msg"],
            raw=line,
            timestamp=groups["timestamp"],
            level=level,
            host=groups["host"],
            process=groups["proc"],
            pid=pid,
            parser=self.name,
            fields=fields,
        )


class LogfmtParser(BaseParser):
    """Parser for Heroku/Go style key=value logfmt lines."""

    name: str = "logfmt"

    _KV_PATTERN = re.compile(r'([a-zA-Z0-9_\.\-]+)=(?:"([^"]*)"|(\S+))')

    def parse(self, line: str) -> Optional[NormalizedLog]:
        stripped = line.strip()
        matches = self._KV_PATTERN.findall(stripped)
        if len(matches) < 2:  # Must have at least 2 key-value pairs to qualify as logfmt
            return None

        fields: Dict[str, Any] = {}
        for key, quoted_val, unquoted_val in matches:
            val = quoted_val if quoted_val != "" else unquoted_val
            fields[key] = val

        message = fields.pop("msg", None) or fields.pop("message", None) or stripped
        raw_level = fields.pop("level", None) or fields.pop("lvl", None)
        timestamp = fields.pop("ts", None) or fields.pop("time", None) or fields.pop("timestamp", None)
        host = fields.pop("host", None)
        ip = fields.pop("ip", None) or fields.pop("remote_addr", None)
        process = fields.pop("app", None) or fields.pop("service", None)

        return NormalizedLog(
            message=message,
            raw=line,
            timestamp=str(timestamp) if timestamp else None,
            level=normalize_log_level(raw_level),
            host=str(host) if host else None,
            ip=str(ip) if ip else None,
            process=str(process) if process else None,
            parser=self.name,
            fields=fields,
        )


class StandardAppLogParser(BaseParser):
    """Parser for standard brackets or spaced application logs like:
    [2026-10-06 12:00:00] [INFO] [auth] User logged in
    2026-10-06T12:00:00.000Z INFO user logged in
    """

    name: str = "standard_app"

    _PATTERN = re.compile(
        r"^(?:\[(?P<ts_b>[^\]]+)\]|(?P<ts_plain>\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?))\s+"
        r"(?:\[(?P<lvl_b>[A-Za-z]+)\]|(?P<lvl_plain>[A-Za-z]+))\s+"
        r"(?:\[(?P<proc_b>[^\]]+)\]\s+)?(?P<msg>.*)$"
    )

    def parse(self, line: str) -> Optional[NormalizedLog]:
        match = self._PATTERN.match(line.strip())
        if not match:
            return None

        groups = match.groupdict()
        timestamp = groups["ts_b"] or groups["ts_plain"]
        level_str = groups["lvl_b"] or groups["lvl_plain"]
        proc = groups.get("proc_b")
        msg = groups["msg"]

        return NormalizedLog(
            message=msg,
            raw=line,
            timestamp=timestamp,
            level=normalize_log_level(level_str),
            process=proc,
            parser=self.name,
        )


class RegexLogParser(BaseParser):
    """Custom pluggable regex parser with named capture groups."""

    def __init__(self, name: str, pattern: str | re.Pattern):
        self.name = name
        self.regex = re.compile(pattern) if isinstance(pattern, str) else pattern

    def parse(self, line: str) -> Optional[NormalizedLog]:
        match = self.regex.match(line.strip())
        if not match:
            return None

        data = match.groupdict()
        msg = data.pop("message", None) or data.pop("msg", None) or line.strip()
        ts = data.pop("timestamp", None) or data.pop("time", None)
        lvl = data.pop("level", None) or data.pop("severity", None)
        host = data.pop("host", None)
        ip = data.pop("ip", None)
        proc = data.pop("process", None) or data.pop("service", None)
        pid_raw = data.pop("pid", None)
        pid = int(pid_raw) if pid_raw and str(pid_raw).isdigit() else None

        return NormalizedLog(
            message=msg,
            raw=line,
            timestamp=str(ts) if ts else None,
            level=normalize_log_level(lvl),
            host=str(host) if host else None,
            ip=str(ip) if ip else None,
            process=str(proc) if proc else None,
            pid=pid,
            parser=self.name,
            fields=data,
        )
