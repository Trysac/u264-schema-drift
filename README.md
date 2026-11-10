# schema-drift

[![PyPI version](https://img.shields.io/pypi/v/trysac-schema-drift)](https://pypi.org/project/trysac-schema-drift/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-schema-drift)](LICENSE)
[![CI](https://github.com/Trysac/u264-schema-drift/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u264-schema-drift/actions/workflows/ci.yml)

Detect schema drift between data batches: profile records into a stored JSON baseline and report added or removed columns, type changes, null rate jumps, new categories and range breaks

## Problem

Describe in two or three sentences the concrete problem this utility solves, who hits it, and what
they do today without it. Replace this paragraph when the first real feature lands.

## Install

```sh
pip install trysac-schema-drift
# or
uv add trysac-schema-drift
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
import schema_drift

# normalize() trims surrounding whitespace and lower-cases the text.
print(schema_drift.normalize("  Hello World "))  # -> "hello world"

# Blank input is rejected explicitly instead of returning an empty string.
try:
    schema_drift.normalize("   ")
except ValueError as exc:
    print(f"rejected: {exc}")
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) and [decisions](docs/decisions/)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
