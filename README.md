# trysac-schema-drift

Detect schema drift between data batches. Profile records into a stored JSON baseline and report added or removed columns, type changes, null rate jumps, new categories and range breaks.

Upstream teams add a column, start sending an ID as text or let a field go null, and the pipeline either breaks hours later or silently loads bad data. Schema files do not catch it because the data changed, not the declared schema. This library profiles each batch, stores the profile as a baseline and compares the next batch with explicit, thresholded drift rules.

## Installation

```bash
pip install trysac-schema-drift
```

## Usage

```python
from schema_drift import profile, compare

day1 = [{"id": 1, "name": "a"}]
day2 = [{"id": "x", "name": None, "tag": "n"}]
baseline = profile(day1)
current = profile(day2)
for drift in compare(baseline, current):
    print(drift)
```

The example prints:

```
Drift(code='type_changed', column='id', severity='high', detail='added types: str')
Drift(code='null_rate', column='name', severity='medium', detail='0.000 -> 1.000')
Drift(code='column_added', column='tag', severity='low', detail='types: str')
```

### Command-line interface

```bash
python -m schema_drift baseline day1.jsonl --out baseline.json
python -m schema_drift check baseline.json day2.jsonl --null-rate-delta 0.1
```

The `check` command prints one line per drift as `<severity> <code> <column>: <detail>`. It exits with `0` when no drift has severity `high` or `medium`, `1` when any such drift exists, and `2` on usage or input errors.

## Public API

All dataclasses are frozen. The runtime uses only the Python standard library.

- `profile(records, *, max_categories=50, max_columns=1000) -> Profile` profiles an iterable of mappings. A missing key counts as a null. `None` counts in `nulls` and never in `types`. Types are `null`, `bool`, `int`, `float`, `str`, `array` (list) and `object` (dict; not recursed). Strings longer than 200 characters, or more than `max_categories` distinct strings, make `categories` `None`. `minimum` and `maximum` cover `int` and `float` values and exclude `bool`; NaN is counted as `float` but excluded from min/max. Raises `DriftError` with code `invalid_record` for a non-mapping record or unsupported value, and `too_many_columns` for a record or batch over `max_columns`. Raises `ValueError` for a negative option.
- `compare(baseline, current, *, null_rate_delta=0.1) -> list[Drift]` returns drifts sorted by column, then code. Rules: `column_added` (`low`), `column_removed` (`high`), `type_changed` (`high`), `type_widened` (`low`, `int -> float`), `null_rate` (`medium`, strict increase greater than `null_rate_delta`, compared with `Fraction`), `new_categories` (`medium`, at most five values in the detail), and `out_of_range` (`medium`).
- `load_jsonl(text, *, max_line_bytes=1_048_576, max_records=1_000_000) -> list[dict]` parses newline-delimited JSON. A blank line or invalid JSON raises `DriftError("invalid_json")`; a non-object record raises `DriftError("invalid_record")`; a line over `max_line_bytes` raises `DriftError("input_too_large")`; more than `max_records` raises `DriftError("too_many_records")`.
- `Profile.to_json() -> str` and `Profile.from_json(text) -> Profile` use `version: 1` and sorted keys. `from_json` raises `DriftError("invalid_json")` on invalid JSON and `DriftError("unsupported_version")` for a version other than `1`.
- `DriftError(code, message="")` has `code` from `DriftErrorCode`: `too_many_columns`, `invalid_record`, `input_too_large`, `invalid_json`, `unsupported_version`, `too_many_records`.
- `ColumnProfile` fields: `rows`, `nulls`, `types`, `categories`, `minimum`, `maximum`. `Profile` fields: `columns`, `rows`. `Drift` fields: `code`, `column`, `severity`, `detail`.

Security limits and the threat model are in [docs/SECURITY.md](docs/SECURITY.md).

## Why not comparing declared schemas or inferring one

A declared-schema check sees only the schema file, and an inferred schema from one batch has no stored threshold history. `schema_drift` watches the data itself between batches, with stored baselines and explicit thresholds.

## Development

Run the tests with `pytest`. The actual test files and their coverage are described in [docs/TESTING.md](docs/TESTING.md).

## License

MIT
