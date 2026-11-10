# Testing

## Running

From the repository root:

```sh
pytest
```

The tests are `tests/test_core.py` and `tests/test_cli.py`.

## Policy

- Tests call the public API (`schema_drift`) and the CLI entry point `schema_drift.__main__.main`.
- Tests assert observable values: `Profile`/`ColumnProfile` equality, `Drift` fields, `DriftError.code`, CLI output and exit codes.
- No network access or external services are used by the test files.

## Tiers

The repository has one pytest tier: both test modules run directly under pytest. There is no separate conformance marker or external tool installation in the test files.

## Layout

`tests/test_core.py` covers core profiling and comparison, including the `null_rate` Fraction threshold. Known test names include `test_profile_acceptance`, `test_compare_acceptance`, and `test_null_rate_fraction_threshold`.

`tests/test_cli.py` covers the CLI baseline/check flow, output formatting, exit codes and input errors. Known test names include `test_baseline_and_check`, `test_check_no_drift_exit_zero`, `test_check_low_drift_exit_zero`, and `test_input_error_returns_2`.
