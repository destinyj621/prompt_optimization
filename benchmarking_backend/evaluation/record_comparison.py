"""Record-level comparison helpers."""

from __future__ import annotations

import json
from typing import Any, Dict, Tuple


def _try_parse_json(text: str) -> Any:
    try:
        return json.loads(text)
    except Exception:
        return None


def compare_records(expected_output: str, model_output: str) -> Tuple[float, bool]:
    expected_obj = _try_parse_json(expected_output)
    output_obj = _try_parse_json(model_output)

    if isinstance(expected_obj, dict) and isinstance(output_obj, dict):
        expected_keys = set(expected_obj.keys())
        if not expected_keys:
            return 100.0, True
        matched = 0
        for key in expected_keys:
            if key in output_obj and str(output_obj[key]).strip().lower() == str(expected_obj[key]).strip().lower():
                matched += 1
        field_accuracy = (matched / len(expected_keys)) * 100
        exact_match = expected_obj == output_obj
        return field_accuracy, exact_match

    exact_match = expected_output.strip().lower() == model_output.strip().lower()
    return (100.0 if exact_match else 0.0), exact_match
