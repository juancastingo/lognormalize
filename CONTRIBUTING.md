# Contributing to lognormalize

Thank you for your interest in contributing to `lognormalize`!

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/juancastingo/lognormalize.git
   cd lognormalize
   ```

2. Install dev dependencies and editable package:
   ```bash
   pip install -e ".[dev]"
   ```

3. Run the tests:
   ```bash
   pytest
   ```

## Adding New Parsers

To add a new built-in log format parser:
1. Inherit from `BaseParser` in `src/lognormalize/parsers.py`.
2. Implement `.parse(self, line: str) -> Optional[NormalizedLog]`.
3. Add unit test cases in `tests/test_lognormalize.py` covering standard and edge-case samples.
4. Ensure 100% test coverage and submit a pull request!
