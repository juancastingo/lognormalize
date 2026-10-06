# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-10-06

### Added
- Initial public release of `lognormalize`.
- Standardized `NormalizedLog` dataclass with timestamp, level, message, host, ip, process, pid, parser, and arbitrary fields.
- Built-in parsers for:
  - JSON / JSONL structured logs.
  - Nginx & Apache Combined Access Logs (with HTTP status to log level mapping).
  - Syslog RFC 3164 (BSD syslog).
  - Logfmt (`key=value` formats).
  - Standard application bracketed logs.
- Pluggable `RegexLogParser` and extensible `ParserRegistry`.
- Streaming iterators (`normalize_stream`, `stream_to_jsonl`) for memory-efficient handling of large logs.
- CLI tool `lognormalize` supporting file processing, stdin pipes, format flags, and severity filtering.
