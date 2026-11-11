# Watch data batches directly instead of declared schemas

Status: accepted (generated, pending human review)

## Context

Schema drift is caused by changes in actual data, not by changes in schema files. Declared schemas may lag behind reality, and inferring a schema from data introduces uncertainty. The pipeline needs early detection of changes such as new columns, type shifts, null-rate increases, and range breaks.

## Decision

Implement a profiling-and-compare library: profile each batch into a JSON baseline (with version 1), store it, and compare the next batch using explicit rules. Use frozen dataclasses for column profiles and drift reports. Compare null rates with Fraction to avoid floating-point issues. Provide a CLI for batch workflows.

## Consequences

The library is lightweight and transparent; it tracks exactly what is defined. It does not cover nested field drift, statistical distribution tests, or JSON Schema export, keeping scope focused. Users must manage baseline storage and scheduling themselves.
