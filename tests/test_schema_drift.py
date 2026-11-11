"""Behavior tests for the public API of schema_drift."""

from __future__ import annotations

import pytest

import schema_drift
from schema_drift import ColumnProfile, Drift, DriftError, Profile, compare, profile


def test_public_api_is_exported() -> None:
    for name in (
        "ColumnProfile",
        "Drift",
        "DriftError",
        "Profile",
        "compare",
        "load_jsonl",
        "profile",
    ):
        assert hasattr(schema_drift, name)


def test_drift_error_carries_code() -> None:
    error = DriftError("invalid_record", "record at index 0 is not an object")
    assert error.code == "invalid_record"
    assert "index 0" in str(error)
    assert isinstance(error, Exception)


def test_models_are_frozen() -> None:
    column = ColumnProfile(rows=1, nulls=0, types=("int",), categories=None, minimum=1, maximum=1)
    with pytest.raises(AttributeError):
        column.rows = 2  # type: ignore[misc]
    drift = Drift("column_added", "x", "low", "types: int")
    with pytest.raises(AttributeError):
        drift.code = "column_removed"  # type: ignore[misc]


def test_empty_batch_removes_every_column() -> None:
    baseline = profile([{"id": 1, "name": "a"}])
    current = profile([])
    assert current.rows == 0
    assert current.columns == {}
    drifts = compare(baseline, current)
    assert all(d.code == "column_removed" for d in drifts)
    assert [d.column for d in drifts] == ["id", "name"]


def test_profile_json_roundtrip_via_public_api() -> None:
    prof = profile([{"id": 1, "price": 1.5}, {"id": 2, "price": 3.0}])
    assert Profile.from_json(prof.to_json()) == prof


def test_from_json_rejects_unsupported_version() -> None:
    prof = profile([{"id": 1}])
    bad = prof.to_json().replace('"version": 1', '"version": 2')
    with pytest.raises(DriftError) as excinfo:
        Profile.from_json(bad)
    assert excinfo.value.code == "unsupported_version"
