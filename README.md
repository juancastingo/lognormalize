# lognormalize

[![CI](https://github.com/juancastingo/lognormalize/actions/workflows/ci.yml/badge.svg)](https://github.com/juancastingo/lognormalize/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/lognormalize.svg)](https://pypi.org/project/lognormalize/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

**lognormalize** is a fast, versatile Python library and CLI tool that parses and standardizes heterogeneous, semi-structured logs into a unified data structure and JSONL stream.

Whether parsing web access logs (Nginx/Apache), Syslog (RFC 3164), JSON, Logfmt (`key=value`), or custom application logs, `lognormalize` extracts common fields (`timestamp`, `level`, `message`, `host`, `ip`, `process`, `pid`) into clean Python dataclasses with zero external runtime dependencies.

---

## Features

- 🔄 **Multi-Format Auto Detection**:
  - **JSON / JSONL**: Automatically maps disparate keys (`ts`/`time`, `msg`/`message`, `lvl`/`level`).
  - **Web Access Logs**: Nginx and Apache Combined Log Format with HTTP status code level mapping.
  - **Syslog**: RFC 3164 BSD syslog format.
  - **Logfmt**: Key-value pairs (`ts=... level=info msg="..."`).
  - **Standard App Logs**: Bracketed and ISO timestamped lines (`[2026-10-06] [INFO] message`).
- 🧩 **Pluggable Architecture**: Easily register custom regex patterns or parser classes.
- ⚡ **Streaming & Low Memory**: Process gigabyte-scale logs through lazy generators or stream directly to JSONL.
- 🛡️ **Zero Runtime Dependencies**: Built entirely on standard Python 3.9+ libraries.
- 🖥️ **Command Line Tool**: Filter, convert, and pipe logs directly from the terminal.

---

## Installation

```bash
pip install lognormalize
```

---

## Python API Usage

### Quick Line Normalization

```python
from lognormalize import normalize_line

# Parse an Nginx access log line
record = normalize_line('192.168.1.50 - - [06/Oct/2026:14:20:00 +0000] "GET /api/v1/metrics HTTP/1.1" 200 412 "-" "curl/7.88"')

print(record.ip)        # 192.168.1.50
print(record.level)     # INFO
print(record.message)   # GET /api/v1/metrics HTTP 200
print(record.fields)    # {'status': 200, 'method': 'GET', 'path': '/api/v1/metrics', 'bytes': 412}

# Parse a logfmt line
logfmt_record = normalize_line('ts=2026-10-06T12:00:00Z level=error msg="database ping timeout" host=db-primary')
print(logfmt_record.level)    # ERROR
print(logfmt_record.message)  # database ping timeout
print(logfmt_record.host)     # db-primary
```

### Streaming Files or Large Iterables

```python
from lognormalize import normalize_stream

with open("app.log") as f:
    for record in normalize_stream(f):
        if record.level in ("ERROR", "CRITICAL"):
            print(f"[{record.timestamp}] {record.process or 'app'}: {record.message}")
```

### Custom Parser Extension

```python
from lognormalize import register_parser, RegexLogParser

# Register custom format: "[SERVICE-ID] MSG"
custom_parser = RegexLogParser(
    name="service_tag",
    pattern=r"^\[(?P<process>[A-Z0-9_\-]+)\]\s+(?P<message>.*)$"
)

register_parser(custom_parser, prepend=True)
```

---

## CLI Usage

### Convert Logs to JSONL Stream

```bash
# Read from file or standard input
lognormalize /var/log/nginx/access.log

# Pipe directly from live logs
tail -f /var/log/syslog | lognormalize --min-level WARNING
```

### Options

| Flag | Description |
| :--- | :--- |
| `-f, --format` | Force specific parser (`auto`, `json`, `web_access`, `syslog`, `logfmt`, `standard_app`) |
| `--min-level` | Filter records below specified severity (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) |
| `-o, --output` | Write output to file instead of stdout |
| `-v, --version` | Display version |

---

## License

MIT License © 2026 Juan Castin
