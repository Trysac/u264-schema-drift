# Stack

## Used

| Tool | Why |
|---|---|
| Python >= 3.10 | Supports the union type syntax and `from __future__ import annotations` used by the package. |
| Python standard library (`json`, `logging`, `math`, `fractions`, `argparse`, `dataclasses`, `typing`, `pathlib`, `collections.abc`) | The package has no runtime dependencies. |
| pytest | The repository contains pytest test modules under `tests/`. |
| `py.typed` | The package ships a `py.typed` marker for its type information. |

## Discarded

| Tool | Why not |
|---|---|
| Third-party runtime dependencies | `allowed_dependencies` is empty; the package is standard-library only. |
| Nested schema inference | Out of scope. |
| Statistical distribution tests (KS, PSI) | Out of scope. |
| JSON Schema export | Out of scope. |
