"""Schema drift detection between data batches.

Profiles records into a stored JSON baseline and compares subsequent batches
against it using explicit, thresholded rules.
"""

from __future__ import annotations

from .core import compare, load_jsonl, profile
from .error import DriftError, DriftErrorCode
from .model import ColumnProfile, Drift, Profile

__all__ = [
    "ColumnProfile",
    "Drift",
    "DriftError",
    "DriftErrorCode",
    "Profile",
    "compare",
    "load_jsonl",
    "profile",
]
