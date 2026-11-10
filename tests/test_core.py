"""Tests for core profiling and comparison logic."""

from __future__ import annotations

import json

import pytest

from schema_drift import (
    ColumnProfile,
    Drift,
    DriftError,
    Profile,
    compare,
    load_jsonl,
    profile,
)


def test_profile_acceptance() -> None:
    records = [
        {"id": 1, "name": "a"},
        {"id": 2, "name": None},
        {"id": 3},
    ]
    prof = profile(records)
    assert prof.rows == 3
    assert set(prof.columns.keys()) == {"id", "name"}

    id_col = prof.columns["id"]
    assert id_col == ColumnProfile(
        rows=3, nulls=0, types=("int",), categories=None, minimum=1, maximum=3
    )

    name_col = prof.columns["name"]
    assert name_col == ColumnProfile(
        rows=3,
        nulls=2,
        types=("str",),
        categories=("a",),
        minimum=None,
        maximum=None,
    )


def test_compare_acceptance() -> None:
    baseline = profile([{"id": 1, "price": 1.5}, {"id": 2, "price": 3.0}])
    current = profile([{"id": "x", "price": 4.0, "tag": "n"}])
    drifts = compare(baseline, current)
    expected = [
        Drift("type_changed", "id", "high", "added types: str"),
        Drift("out_of_range", "price", "medium", "max 3.0 -> 4.0"),
        Drift("column_added", "tag", "low", "types: str"),
    ]
    assert drifts == expected


def test_null_rate_fraction_threshold() -> None:
    baseline_records = [{"name": "a"} for _ in range(10)]
    # 2 nulls out of 10 = 0.2
    current_records = [{"name": None if i < 2 else "b"} for i in range(10)]
    baseline = profile(baseline_records)
    current = profile(current_records)
    drifts = compare(baseline, current)
    assert Drift("null_rate", "name", "medium", "0.000 -> 0.200") in drifts

    # exactly +0.1 (1 null) -> no drift
    current_records_1_null = [{"name": None if i == 0 else "b"} for i in range(10)]
    current1 = profile(current_records_1_null)
    drifts1 = compare(baseline, current1, null_rate_delta=0.1)
    assert not any(d.code == "null_rate" for d in drifts1)


def test_type_widened_vs_changed() -> None:
    baseline = profile([{"v": 1}, {"v": 3}])
    current_float = profile([{"v": 2.5}])
    drifts_float = compare(baseline, current_float)
    assert drifts_float == [Drift("type_widened", "v", "low", "int -> float")]

    current_bool = profile([{"v": True}])
    drifts_bool = compare(baseline, current_bool)
    assert drifts_bool == [Drift("type_changed", "v", "high", "added types: bool")]


def test_new_categories_and_limits() -> None:
    baseline = profile([{"name": "a"}, {"name": "b"}])
    current = profile([{"name": "a"}, {"name": "c"}])
    drifts = compare(baseline, current)
    assert Drift("new_categories", "name", "medium", "c") in drifts

    # More than max_categories distinct strings -> categories None, no drift
    many_names = [{"name": f"val{i}"} for i in range(51)]
    baseline_many = profile(many_names, max_categories=50)
    current_many = profile([*many_names, {"name": "new"}], max_categories=50)
    drifts_many = compare(baseline_many, current_many)
    assert not any(d.code == "new_categories" for d in drifts_many)

    # String over 200 chars -> categories None
    long_name = "x" * 201
    baseline_long = profile([{"name": "a"}])
    current_long = profile([{"name": long_name}])
    assert current_long.columns["name"].categories is None
    drifts_long = compare(baseline_long, current_long)
    assert not any(d.code == "new_categories" for d in drifts_long)


def test_categories_exactly_max_categories_with_repeat() -> None:
    records = [{"name": f"v{i}"} for i in range(50)]
    records.append({"name": "v0"})
    prof = profile(records, max_categories=50)
    assert prof.columns["name"].categories == tuple(sorted(f"v{i}" for i in range(50)))

    # a genuinely new value beyond the limit invalidates categories
    records_extra = [*records, {"name": "v50"}]
    prof_extra = profile(records_extra, max_categories=50)
    assert prof_extra.columns["name"].categories is None


def test_column_removed_empty_batch() -> None:
    baseline = profile([{"id": 1, "name": "a"}])
    current = profile([])
    drifts = compare(baseline, current)
    expected = [
        Drift("column_removed", "id", "high", "was int"),
        Drift("column_removed", "name", "high", "was str"),
    ]
    assert drifts == expected


def test_nan_handling() -> None:
    baseline = profile([{"v": 1.0}, {"v": 2.0}])
    current = profile([{"v": float("nan")}])
    # current profile: types should include float, min/max None because only NaN
    assert current.columns["v"].types == ("float",)
    assert current.columns["v"].minimum is None
    assert current.columns["v"].maximum is None
    # compare: no out_of_range because current has no numeric min/max
    drifts = compare(baseline, current)
    assert not any(d.code == "out_of_range" for d in drifts)


def test_nested_objects() -> None:
    baseline = profile([{"data": {"a": 1}}])
    assert baseline.columns["data"].types == ("object",)
    assert baseline.columns["data"].categories is None


def test_profile_errors() -> None:
    # non-dict record
    with pytest.raises(DriftError, match="record at index 0 is not a mapping"):
        profile([1, 2, 3])  # type: ignore[list-item]

    # too many columns per record
    record = {str(i): i for i in range(1001)}
    with pytest.raises(DriftError, match="record has 1001 columns") as excinfo:
        profile([record])
    assert excinfo.value.code == "too_many_columns"

    # too many distinct columns across records
    rec1 = {f"col{i}": i for i in range(600)}
    rec2 = {f"other{i}": i for i in range(600)}
    with pytest.raises(DriftError, match="total distinct columns"):
        profile([rec1, rec2])

    # unsupported value type (e.g., set)
    with pytest.raises(DriftError, match="unsupported value type"):
        profile([{"bad": {1, 2}}])

    # negative max_categories
    with pytest.raises(ValueError):
        profile([], max_categories=-1)

    # negative max_columns
    with pytest.raises(ValueError):
        profile([], max_columns=-1)


def test_load_jsonl() -> None:
    text = '{"a": 1}\n{"b": 2}\n'
    records = load_jsonl(text)
    assert records == [{"a": 1}, {"b": 2}]

    # input too large
    with pytest.raises(DriftError, match="line 0 exceeds max_line_bytes") as excinfo:
        load_jsonl("x" * 1_048_577, max_line_bytes=1_048_576)
    assert excinfo.value.code == "input_too_large"

    # invalid JSON
    with pytest.raises(DriftError, match="invalid JSON on line 0"):
        load_jsonl("not json")

    # non-object record
    with pytest.raises(DriftError, match="record at index 0 is not an object"):
        load_jsonl("[1,2,3]")

    # empty line
    with pytest.raises(DriftError, match="empty line at index 0"):
        load_jsonl("\n")

    # max records exceeded
    with pytest.raises(DriftError, match="exceeded max_records"):
        load_jsonl('{"a":1}\n{"b":2}\n', max_records=1)


def test_profile_json_roundtrip() -> None:
    records = [{"id": 1, "name": "a"}, {"id": 2, "name": None}]
    prof = profile(records)
    json_text = prof.to_json()
    # check sorted keys and version
    assert '"version": 1' in json_text
    parsed = json.loads(json_text)
    assert list(parsed.keys()) == ["columns", "rows", "version"]
    # roundtrip
    prof2 = Profile.from_json(json_text)
    assert prof == prof2

    # unsupported version
    bad_json = json_text.replace('"version": 1', '"version": 2')
    with pytest.raises(DriftError, match="unsupported profile version"):
        Profile.from_json(bad_json)

    # invalid JSON for from_json
    with pytest.raises(DriftError, match="profile JSON is invalid"):
        Profile.from_json("not json")


def test_out_of_range_details() -> None:
    baseline = profile([{"v": 1}, {"v": 3}])
    current = profile([{"v": 0.5}, {"v": 4}])
    drifts = compare(baseline, current)
    assert Drift("out_of_range", "v", "medium", "min 1 -> 0.5; max 3 -> 4") in drifts

    # only min drift
    current_min = profile([{"v": 0.5}, {"v": 3}])
    drifts_min = compare(baseline, current_min)
    assert Drift("out_of_range", "v", "medium", "min 1 -> 0.5") in drifts_min

    # only max drift
    current_max = profile([{"v": 1}, {"v": 5}])
    drifts_max = compare(baseline, current_max)
    assert Drift("out_of_range", "v", "medium", "max 3 -> 5") in drifts_max


def test_zero_rows_baseline() -> None:
    baseline = Profile(columns={}, rows=0)
    current = profile([{"id": 1}])
    drifts = compare(baseline, current)
    assert Drift("column_added", "id", "low", "types: int") in drifts


def test_load_jsonl_record_index() -> None:
    text = '{"a": 1}\n[1,2]\n'
    with pytest.raises(DriftError, match="record at index 1 is not an object"):
        load_jsonl(text)
