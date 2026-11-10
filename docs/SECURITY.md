# Security Policy

## Reporting a Vulnerability

Report security issues privately to the maintainers. Do not open a public issue.

## Threat Model

`schema_drift` parses untrusted JSONL and profiles caller-supplied mappings. It does not execute data, open network connections, or write files except through the CLI paths the caller gives.

### Defended

- `load_jsonl` rejects a line whose UTF-8 encoding exceeds `max_line_bytes` (default 1,048,576) with `DriftError("input_too_large")`, rejects blank lines and invalid JSON with `DriftError("invalid_json")`, rejects non-object records with `DriftError("invalid_record")`, and stops after `max_records` (default 1,000,000) with `DriftError("too_many_records")`.
- `profile` rejects a non-mapping record (`invalid_record`), a record with more than `max_columns` keys and a batch with more than `max_columns` distinct keys (`too_many_columns`), and unsupported value types (`invalid_record`).
- Categories are capped at `max_categories` (default 50) distinct strings; strings longer than 200 characters are not retained in categories. This bounds category storage.
- `Profile.from_json` rejects non-JSON with `invalid_json` and any `version` other than `1` with `unsupported_version`.
- `DriftError` exposes a stable code and a short message; the library does not include raw record contents in its error messages.

### Not defended

- `profile()` materializes every record in the input iterable and has no record-count or total-byte limit; callers passing a huge iterable can exhaust memory.
- `load_jsonl()` receives the entire text as a string and calls `splitlines()`; the input text is already in memory. The line and record limits are enforced after that materialization.
- Nested objects are typed only as `object` and are not recursively profiled, so drift inside nested structures is not detected.
- The library does not authenticate, encrypt, or redact data. Values such as strings and numbers appear in profiles and drift details up to the documented limits.
- There is no defense against a malicious `Profile` object or `Mapping` supplied directly to `compare()` or `Profile.to_json()`; those functions trust their inputs.

### Limits

- **Maximum columns**: Each record may have at most `max_columns` (default 1000) keys, and the total number of distinct columns across all records is also limited.
- **Maximum categories**: A string column with more than `max_categories` (default 50) distinct values will not retain a category list, preventing unbounded category growth.
- **Maximum string length**: Strings longer than 200 characters are not stored in categories.
- **Maximum JSONL line size**: `load_jsonl` rejects lines longer than `max_line_bytes` (default 1,048,576 bytes).
- **Maximum records**: `load_jsonl` stops after `max_records` (default 1,000,000).

All input/validation failures raise `DriftError` with a code from `DriftErrorCode`; negative profiling options raise `ValueError`.
