# Architecture

This document describes the architecture and key design decisions of `trysac-schema-drift`.

## Core Design

The library operates in three phases:

1. **Profiling**: `profile()` consumes an iterable of records (dict-like objects) and produces a frozen `Profile` containing per-column statistics.
2. **Baseline storage**: `Profile.to_json()` serializes the profile to a versioned JSON document; `Profile.from_json()` parses it back.
3. **Comparison**: `compare()` takes a baseline and a current `Profile`, applies explicit drift rules, and returns a sorted list of `Drift` objects.

## Key Decisions

- **Materialize records for profiling**: To compute column statistics accurately (including missing keys counted as nulls), `profile()` collects the input records into a list after validating each record. This is memory-bound by the input size.
- **Fraction for null-rate comparison**: Null rates are compared using `fractions.Fraction` to avoid floating-point precision issues when deciding whether the increase exceeds `null_rate_delta`. The check is strictly greater than the threshold.
- **Categories as a capped summary**: Only string-only columns with at most `max_categories` (default 50) distinct values and no string longer than 200 characters get a `categories` tuple. Otherwise `categories` is `None`, and the column will never produce `new_categories` drift.
- **Type widening exception**: Adding `float` to an `int`-only column is reported as low-severity `type_widened`, not high-severity `type_changed`. If other new types appear alongside `float`, both `type_widened` (for the float) and `type_changed` (for the other types) are emitted.
- **NaN handling**: NaN values in float columns are counted as `float` in types but are excluded from minimum and maximum computation.
- **Error model**: `DriftError` carries a stable `code` from `DriftErrorCode` (`too_many_columns`, `invalid_record`, `input_too_large`, `invalid_json`, `unsupported_version`, `too_many_records`). `profile()` also raises `ValueError` for negative `max_categories` or `max_columns`. `Profile.from_json()` raises `DriftError` for invalid JSON or an unsupported version; it otherwise indexes the required profile keys.
- **JSONL loading**: `load_jsonl()` splits the input text into lines, enforces `max_line_bytes` per line, rejects blank lines and invalid JSON, requires each decoded value to be a dict, and enforces `max_records`.

## Security Considerations

Input size limits are enforced: maximum columns per record and total columns, maximum line bytes in JSONL, and maximum records. These prevent resource exhaustion from large inputs. `profile()` itself materializes the input iterable and has no record-count limit. See `docs/SECURITY.md` for details.
