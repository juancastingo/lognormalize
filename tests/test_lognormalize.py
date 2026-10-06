import io
import json
import pytest
from lognormalize import (
    NormalizedLog,
    normalize_line,
    normalize_stream,
    stream_to_jsonl,
    register_parser,
    RegexLogParser,
    ParserRegistry,
)
from lognormalize.cli import main as cli_main


def test_json_log_parser():
    raw = '{"time": "2026-10-06T12:00:00Z", "level": "warn", "msg": "Database slow query", "duration_ms": 420, "query": "SELECT * FROM users", "host": "srv-db1", "pid": 9812}'
    log = normalize_line(raw)

    assert log.parser == "json"
    assert log.timestamp == "2026-10-06T12:00:00Z"
    assert log.level == "WARNING"
    assert log.message == "Database slow query"
    assert log.host == "srv-db1"
    assert log.pid == 9812
    assert log.fields == {"duration_ms": 420, "query": "SELECT * FROM users"}

    d = log.to_dict()
    assert d["level"] == "WARNING"
    assert d["pid"] == 9812
    assert "fields" in d


def test_combined_web_access_log():
    raw = '192.168.1.100 - admin [06/Oct/2026:15:32:10 +0000] "GET /api/v1/health HTTP/1.1" 200 145 "-" "Mozilla/5.0"'
    log = normalize_line(raw)

    assert log.parser == "web_access"
    assert log.ip == "192.168.1.100"
    assert log.level == "INFO"
    assert log.message == "GET /api/v1/health HTTP 200"
    assert log.fields["status"] == 200
    assert log.fields["bytes"] == 145
    assert log.fields["user"] == "admin"


def test_combined_web_access_error_code():
    raw = '10.0.0.5 - - [06/Oct/2026:15:35:00 +0000] "POST /api/login HTTP/1.1" 502 0 "-" "curl/7.81.0"'
    log = normalize_line(raw)

    assert log.parser == "web_access"
    assert log.level == "ERROR"
    assert log.fields["status"] == 502


def test_syslog_rfc3164():
    raw = "Oct  6 04:12:30 prod-worker worker-daemon[4510]: Job #881 completed successfully"
    log = normalize_line(raw)

    assert log.parser == "syslog"
    assert log.host == "prod-worker"
    assert log.process == "worker-daemon"
    assert log.pid == 4510
    assert log.message == "Job #881 completed successfully"


def test_logfmt():
    raw = 'ts=2026-10-06T10:00:00Z level=error msg="connection timeout" host=node-4 service=payments latency=5.2s'
    log = normalize_line(raw)

    assert log.parser == "logfmt"
    assert log.level == "ERROR"
    assert log.message == "connection timeout"
    assert log.host == "node-4"
    assert log.process == "payments"
    assert log.fields["latency"] == "5.2s"


def test_standard_app_log():
    raw = "[2026-10-06 14:00:00] [INFO] [auth-service] User logged in: alice@example.com"
    log = normalize_line(raw)

    assert log.parser == "standard_app"
    assert log.level == "INFO"
    assert log.process == "auth-service"
    assert log.message == "User logged in: alice@example.com"
    assert log.timestamp == "2026-10-06 14:00:00"


def test_custom_regex_parser():
    pattern = r"^CRIT-(?P<service>[a-z]+): (?P<message>.*)$"
    custom = RegexLogParser("critical_prefix", pattern)
    registry = ParserRegistry(load_defaults=False)
    registry.register(custom)

    res = registry.normalize("CRIT-auth: token expired unexpectedly")
    assert res.parser == "critical_prefix"
    assert res.process == "auth"
    assert res.message == "token expired unexpectedly"


def test_streaming_generator_and_jsonl():
    lines = [
        '{"level": "info", "msg": "Starting server"}',
        '{"level": "error", "msg": "Port already in use"}',
    ]

    out = io.StringIO()
    count = stream_to_jsonl(lines, out)
    assert count == 2

    out.seek(0)
    lines_written = out.getvalue().strip().split("\n")
    assert len(lines_written) == 2

    item1 = json.loads(lines_written[0])
    assert item1["level"] == "INFO"
    assert item1["message"] == "Starting server"


def test_cli_execution_with_filter(monkeypatch, capsys):
    sample = (
        '{"level": "debug", "msg": "debug details"}\n'
        '{"level": "error", "msg": "fatal failure"}\n'
    )
    monkeypatch.setattr("sys.stdin", io.StringIO(sample))

    exit_code = cli_main(["--min-level", "ERROR"])
    assert exit_code == 0

    captured = capsys.readouterr()
    lines = [json.loads(l) for l in captured.out.strip().split("\n") if l]
    assert len(lines) == 1
    assert lines[0]["level"] == "ERROR"
    assert lines[0]["message"] == "fatal failure"
