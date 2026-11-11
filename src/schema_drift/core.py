"""Core profiling and comparison logic."""

from __future__ import annotations

import json
import logging
import math
from collections.abc import Iterable, Mapping
from fractions import Fraction
from typing import Any, TypedDict

from .error import DriftError
from .model import ColumnProfile, Drift, Profile

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def _value_type(value: object) -> str:
    """Return the schema type name for a JSON-compatible value."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    raise DriftError("invalid_record", f"unsupported value type {type(value).__name__}")


class _ColumnAccumulator(TypedDict):
    nulls: int
    types: set[str]
    all_strings: bool
    categories_set: set[str]
    categories_invalid: bool
    has_numeric: bool
    min_val: int | float | None
    max_val: int | float | None


def profile(
    records: Iterable[Mapping[str, object]],
    *,
    max_categories: int = 50,
    max_columns: int = 1000,
) -> Profile:
    """Profile a batch of records.

    Args:
        records: Iterable of mappings (e.g., list of dicts) representing JSON objects.
        max_categories: Maximum number of distinct string values to track per column.
            If exceeded, categories become None.
        max_columns: Maximum number of columns per record and across all records.

    Returns:
        A Profile with column statistics.

    Raises:
        DriftError: If a record is not a mapping, has too many columns, or contains
            an unsupported value type.
        ValueError: If max_categories or max_columns is negative.
    """
    if max_categories < 0:
        raise ValueError("max_categories must be non-negative")
    if max_columns < 0:
        raise ValueError("max_columns must be non-negative")

    records_list: list[Mapping[str, object]] = []
    column_names: set[str] = set()
    total_records = 0

    for idx, record in enumerate(records):
        if not isinstance(record, Mapping):
            raise DriftError("invalid_record", f"record at index {idx} is not a mapping")
        if len(record) > max_columns:
            raise DriftError(
                "too_many_columns",
                f"record has {len(record)} columns, max is {max_columns}",
            )
        records_list.append(record)
        column_names.update(record.keys())
        total_records += 1

    if len(column_names) > max_columns:
        raise DriftError(
            "too_many_columns",
            f"total distinct columns {len(column_names)} exceeds max {max_columns}",
        )

    # Initialize accumulators
    columns_acc: dict[str, _ColumnAccumulator] = {}
    for name in column_names:
        columns_acc[name] = _ColumnAccumulator(
            nulls=0,
            types=set(),
            all_strings=True,
            categories_set=set(),
            categories_invalid=False,
            has_numeric=False,
            min_val=None,
            max_val=None,
        )

    for record in records_list:
        for name in column_names:
            value = record.get(name)
            acc = columns_acc[name]
            if value is None:
                acc["nulls"] += 1
                continue

            typ = _value_type(value)
            acc["types"].add(typ)

            if isinstance(value, str):
                if len(value) > 200:
                    acc["categories_invalid"] = True
                else:
                    if acc["all_strings"] and not acc["categories_invalid"]:
                        if value in acc["categories_set"]:
                            pass
                        elif len(acc["categories_set"]) < max_categories:
                            acc["categories_set"].add(value)
                        else:
                            acc["categories_invalid"] = True
            else:
                acc["all_strings"] = False
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    if isinstance(value, float) and math.isnan(value):
                        # NaN is counted as float but excluded from min/max
                        continue
                    acc["has_numeric"] = True
                    current_min = acc["min_val"]
                    current_max = acc["max_val"]
                    if current_min is None or value < current_min:
                        acc["min_val"] = value
                    if current_max is None or value > current_max:
                        acc["max_val"] = value

    columns = {}
    for name, acc in columns_acc.items():
        cats: tuple[str, ...] | None = None
        if acc["all_strings"] and not acc["categories_invalid"]:
            cats = tuple(sorted(acc["categories_set"]))
        columns[name] = ColumnProfile(
            rows=total_records,
            nulls=acc["nulls"],
            types=tuple(sorted(acc["types"])),
            categories=cats,
            minimum=acc["min_val"] if acc["has_numeric"] else None,
            maximum=acc["max_val"] if acc["has_numeric"] else None,
        )

    return Profile(columns=columns, rows=total_records)


def compare(
    baseline: Profile,
    current: Profile,
    *,
    null_rate_delta: float = 0.1,
) -> list[Drift]:
    """Compare two profiles and return drift events.

    Drifts are sorted by column name, then code.

    Args:
        baseline: The baseline profile.
        current: The current profile.
        null_rate_delta: Threshold for null rate increase (strictly greater).

    Returns:
        A list of Drift objects.
    """
    drifts: list[Drift] = []
    bcols = baseline.columns
    ccols = current.columns

    # Column added
    for col in ccols:
        if col not in bcols:
            types = ", ".join(ccols[col].types)
            drifts.append(Drift("column_added", col, "low", f"types: {types}"))

    # Column removed
    for col in bcols:
        if col not in ccols:
            types = ", ".join(bcols[col].types)
            drifts.append(Drift("column_removed", col, "high", f"was {types}"))

    # Per-column comparison for common columns
    for col in bcols:
        if col not in ccols:
            continue
        bcol = bcols[col]
        ccol = ccols[col]

        # Type changes
        btypes = set(bcol.types)
        ctypes = set(ccol.types)
        new_types = ctypes - btypes
        if new_types:
            if btypes == {"int"} and new_types == {"float"}:
                drifts.append(Drift("type_widened", col, "low", "int -> float"))
            elif btypes == {"int"} and "float" in new_types and len(new_types) > 1:
                other_types = new_types - {"float"}
                drifts.append(Drift("type_widened", col, "low", "int -> float"))
                drifts.append(
                    Drift(
                        "type_changed",
                        col,
                        "high",
                        f"added types: {', '.join(sorted(other_types))}",
                    )
                )
            else:
                drifts.append(
                    Drift(
                        "type_changed",
                        col,
                        "high",
                        f"added types: {', '.join(sorted(new_types))}",
                    )
                )

        # Null rate increase
        if bcol.rows > 0 and ccol.rows > 0:
            old_rate = Fraction(bcol.nulls, bcol.rows)
            new_rate = Fraction(ccol.nulls, ccol.rows)
            if new_rate > old_rate + Fraction(null_rate_delta):
                old_float = float(old_rate)
                new_float = float(new_rate)
                drifts.append(
                    Drift(
                        "null_rate",
                        col,
                        "medium",
                        f"{old_float:.3f} -> {new_float:.3f}",
                    )
                )

        # New categories
        if bcol.categories is not None and ccol.categories is not None:
            baseline_cats = set(bcol.categories)
            current_cats = set(ccol.categories)
            new_cats = sorted(current_cats - baseline_cats)
            if new_cats:
                detail = ", ".join(new_cats[:5])
                drifts.append(Drift("new_categories", col, "medium", detail))

        # Out of range
        if (
            bcol.minimum is not None
            and bcol.maximum is not None
            and ccol.minimum is not None
            and ccol.maximum is not None
        ):
            parts = []
            if ccol.minimum < bcol.minimum:
                parts.append(f"min {bcol.minimum!r} -> {ccol.minimum!r}")
            if ccol.maximum > bcol.maximum:
                parts.append(f"max {bcol.maximum!r} -> {ccol.maximum!r}")
            if parts:
                drifts.append(Drift("out_of_range", col, "medium", "; ".join(parts)))

    drifts.sort(key=lambda d: (d.column, d.code))
    return drifts


def load_jsonl(
    text: str,
    *,
    max_line_bytes: int = 1_048_576,
    max_records: int = 1_000_000,
) -> list[dict[str, Any]]:
    """Parse newline-delimited JSON text into a list of dicts.

    Args:
        text: The JSONL content.
        max_line_bytes: Maximum length (in bytes) of a single line.
        max_records: Maximum number of records to read.

    Returns:
        List of parsed JSON objects (dicts).

    Raises:
        DriftError: On input too large, invalid JSON, non-object record, or too many records.
    """
    records: list[dict[str, Any]] = []
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        if len(line.encode("utf-8")) > max_line_bytes:
            raise DriftError("input_too_large", f"line {idx} exceeds max_line_bytes")
        if not line.strip():
            raise DriftError("invalid_json", f"empty line at index {idx}")
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise DriftError("invalid_json", f"invalid JSON on line {idx}") from exc
        if not isinstance(obj, dict):
            raise DriftError("invalid_record", f"record at index {idx} is not an object")
        records.append(obj)
        if len(records) > max_records:
            raise DriftError("too_many_records", f"exceeded max_records={max_records}")
    return records
