"""Tests for the command-line interface."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from schema_drift.__main__ import main


def write_jsonl(path: Path, records: list[dict]) -> None:
    text = "\n".join(json.dumps(r) for r in records) + "\n"
    path.write_text(text, encoding="utf-8")


def test_baseline_and_check(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    day1 = tmp_path / "day1.jsonl"
    write_jsonl(day1, [{"id": 1, "price": 1.5}, {"id": 2, "price": 3.0}])
    profile_path = tmp_path / "profile.json"
    exit_code = main(["baseline", str(day1), "--out", str(profile_path)])
    assert exit_code == 0
    capsys.readouterr()  # swallow output
    assert profile_path.exists()

    day2 = tmp_path / "day2.jsonl"
    write_jsonl(day2, [{"id": "x", "price": 4.0, "tag": "n"}])
    exit_code = main(["check", str(profile_path), str(day2)])
    assert exit_code == 1
    captured = capsys.readouterr()
    lines = captured.out.strip().split("\n")
    assert any("high type_changed id: added types: str" in line for line in lines)
    assert any("medium out_of_range price: max 3.0 -> 4.0" in line for line in lines)
    assert any("low column_added tag: types: str" in line for line in lines)


def test_check_no_drift_exit_zero(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    day1 = tmp_path / "d1.jsonl"
    write_jsonl(day1, [{"id": 1}, {"id": 2}])
    profile_path = tmp_path / "p.json"
    assert main(["baseline", str(day1), "--out", str(profile_path)]) == 0
    capsys.readouterr()

    day2 = tmp_path / "d2.jsonl"
    write_jsonl(day2, [{"id": 1}, {"id": 2}])
    assert main(["check", str(profile_path), str(day2)]) == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == ""  # no drift lines


def test_check_low_drift_exit_zero(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    baseline_data = [{"id": 1}, {"id": 2}]
    baseline_file = tmp_path / "b.jsonl"
    write_jsonl(baseline_file, baseline_data)
    baseline_profile = tmp_path / "b.json"
    assert main(["baseline", str(baseline_file), "--out", str(baseline_profile)]) == 0
    capsys.readouterr()

    current_data = [{"id": 1, "new_col": "x"}]
    current_file = tmp_path / "c.jsonl"
    write_jsonl(current_file, current_data)
    exit_code = main(["check", str(baseline_profile), str(current_file)])
    assert exit_code == 0  # column_added is low, no high/medium
    captured = capsys.readouterr()
    assert "low column_added new_col" in captured.out


def test_input_error_returns_2(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    # missing file
    exit_code = main(
        ["baseline", str(tmp_path / "nonexistent.jsonl"), "--out", str(tmp_path / "out.json")]
    )
    assert exit_code == 2
    capt = capsys.readouterr()
    assert "error" in capt.err
