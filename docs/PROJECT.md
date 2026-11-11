# Project record

## Objective

Detect schema drift between data batches: profile records into a stored JSON baseline and report added or removed columns, type changes, null rate jumps, new categories and range breaks.

## Scope

In scope:

- The `schema_drift` package with `ColumnProfile`, `Profile.to_json()`, `Profile.from_json()`, `Drift`, `DriftError`, `profile()`, `compare()` and `load_jsonl()`.
- The CLI in `schema_drift.__main__` with `baseline JSONL --out PATH` and `check PROFILE JSONL [--null-rate-delta X]`.
- Standard-library-only runtime (`allowed_dependencies` is empty) and the `py.typed` marker.
- Drift rules: `column_added`, `column_removed`, `type_changed`, `type_widened`, `null_rate`, `new_categories`, `out_of_range`.

Out of scope:

- Nested field drift.
- Statistical distribution tests such as KS or PSI.
- JSON Schema export.

## Timeline

| Date | Event |
|---|---|
| 2026 | Initial `schema_drift` package, data model, core profiling/comparison, JSONL loader and CLI. |

## Effort metrics

| Metric | Value |
|---|---|
| Tokens (input / output) | 1077301 / 73870 |
| Hours (human) | pending measurement |
| Cost (USD) | 0.1088 |

## Factory run u264 (measured from API usage)

| Date (UTC) | Phase | Model | Batch | Input | Output | Cache write | Cache read | Cost (USD) |
|---|---|---|---|---|---|---|---|---|
| 2026-11-10 | generation | deepseek-v4-pro | yes | 1937 | 23650 | 0 | 3200 | 0.0482 |
| 2026-11-10 | fix-1 | deepseek-flash | no | 30599 | 12438 | 0 | 311296 | 0.0130 |
| 2026-11-10 | fix-2 | deepseek-flash | no | 8545 | 1915 | 0 | 27520 | 0.0025 |
| 2026-11-10 | audit | deepseek-flash | no | 38259 | 20433 | 0 | 486144 | 0.0195 |
| 2026-11-10 | fix-3 | deepseek-flash | no | 10128 | 803 | 0 | 61312 | 0.0022 |
| 2026-11-10 | docs | deepseek-flash | no | 98105 | 14631 | 0 | 256 | 0.0235 |

Total: $0.1088. Prices: deepseek line, as measured by its adapter. Providers serve the current version of each model id, so the date tells which version answered; versions, launch stages and price sources per line are in the factory's model register (docs/MODELS.md).
