"""Schema validation helpers for structured tasks."""

from __future__ import annotations

import json
from typing import Any


def schema_compliance_score(expected_output: str, model_output: str) -> float:
    try:
        expected_obj: Any = json.loads(expected_output)
    except Exception:
        return 100.0 if model_output.strip() else 0.0

    try:
        output_obj: Any = json.loads(model_output)
    except Exception:
        return 0.0

    if isinstance(expected_obj, dict):
        required_keys = set(expected_obj.keys())
        if not required_keys:
            return 100.0
        output_keys = set(output_obj.keys()) if isinstance(output_obj, dict) else set()
        present = len(required_keys & output_keys)
        return (present / len(required_keys)) * 100

    return 100.0