"""Exception types for schema_drift."""

from __future__ import annotations

from typing import Literal

DriftErrorCode = Literal[
    "too_many_columns",
    "invalid_record",
    "input_too_large",
    "invalid_json",
    "unsupported_version",
    "too_many_records",
]


class DriftError(Exception):
    """Base error for schema_drift with a stable machine-readable code."""

    def __init__(self, code: DriftErrorCode, message: str = "") -> None:
        self.code = code
        super().__init__(message)
