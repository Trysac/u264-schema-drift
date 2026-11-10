"""Data model for profiles and drift reports."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

from .error import DriftError


@dataclass(frozen=True)
class ColumnProfile:
    """Statistics for a single column across all records."""

    rows: int
    nulls: int
    types: tuple[str, ...]
    categories: tuple[str, ...] | None
    minimum: int | float | None
    maximum: int | float | None


@dataclass(frozen=True)
class Profile:
    """Aggregated column profiles for a batch of records."""

    columns: Mapping[str, ColumnProfile]
    rows: int

    def to_json(self) -> str:
        """Serialize the profile to a JSON string with sorted keys."""
        data = {
            "version": 1,
            "rows": self.rows,
            "columns": {
                name: {
                    "rows": col.rows,
                    "nulls": col.nulls,
                    "types": list(col.types),
                    "categories": (list(col.categories) if col.categories is not None else None),
                    "minimum": col.minimum,
                    "maximum": col.maximum,
                }
                for name, col in self.columns.items()
            },
        }
        return json.dumps(data, sort_keys=True, ensure_ascii=False, allow_nan=False)

    @classmethod
    def from_json(cls, text: str) -> Profile:
        """Deserialize a profile from JSON, validating the version."""
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise DriftError("invalid_json", "profile JSON is invalid") from exc
        if data.get("version") != 1:
            raise DriftError(
                "unsupported_version", f"unsupported profile version: {data.get('version')}"
            )
        rows = data["rows"]
        columns_data = data["columns"]
        columns = {}
        for name, col_data in columns_data.items():
            columns[name] = ColumnProfile(
                rows=col_data["rows"],
                nulls=col_data["nulls"],
                types=tuple(col_data["types"]),
                categories=(
                    tuple(col_data["categories"]) if col_data["categories"] is not None else None
                ),
                minimum=col_data.get("minimum"),
                maximum=col_data.get("maximum"),
            )
        return cls(columns=columns, rows=rows)


@dataclass(frozen=True)
class Drift:
    """One detected drift event."""

    code: str
    column: str
    severity: Literal["high", "medium", "low"]
    detail: str
