"""Evaluation metrics for output accuracy and quality."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re

from .record_comparison import compare_records
from .schema_validation import schema_compliance_score


ALLOWED_LABELS = ("positive", "negative", "neutral")

LABELED_VALUE_PATTERN = re.compile(
    r"\b(?:label|sentiment|classification|class|answer|output|result|predicted sentiment)\b\s*[:=-]?\s*(positive|negative|neutral)\b",
    re.IGNORECASE,
)

STANDALONE_LABEL_PATTERN = re.compile(
    r"(?:\b|\()(positive|negative|neutral)(?:\b|\))",
    re.IGNORECASE
)


def _extract_label_from_json(text: str) -> str | None:
    try:
        parsed = json.loads(text)
    except Exception:
        return None

    if isinstance(parsed, str):
        value = parsed.strip().lower()
        if value in ALLOWED_LABELS:
            return value

    if isinstance(parsed, dict):
        for key in ("label", "sentiment", "classification", "class", "answer", "output", "result"):
            value = parsed.get(key)
            if isinstance(value, str):
                normalized = value.strip().lower()
                if normalized in ALLOWED_LABELS:
                    return normalized

    return None


def normalize_label(text: str) -> str:
    if not text:
        return "unknown"

    candidate = text.strip()
    if not candidate:
        return "unknown"

    from_json = _extract_label_from_json(candidate)
    if from_json:
        return from_json

    simplified = candidate.strip("\"'`").lower()
    if simplified in ALLOWED_LABELS:
        return simplified

    labeled_match = LABELED_VALUE_PATTERN.search(candidate)
    if labeled_match:
        return labeled_match.group(1).lower()

    standalone_matches = {
        match.lower()
        for match in STANDALONE_LABEL_PATTERN.findall(candidate)
    }

    if len(standalone_matches) == 1:
        return next(iter(standalone_matches))

    return "unknown"


@dataclass
class AccuracyEvaluator:
    quality_accuracy_weight: float = 1.0
    quality_schema_weight: float = 0.0 # set to zero for now since schema compliance is not a strong signal of quality for classification tasks, mostly useful for structured output tasks

    def evaluate(self, expected_output: str, model_output: str) -> dict[str, float | int]:

        expected = normalize_label(expected_output)
        predicted = normalize_label(model_output)

        accuracy_percent = 0.0
        field_accuracy_percent = 0.0
        schema_compliance_percent = 0.0
        exact_match = 0

        try:

            # ---- Classification tasks ----
            if expected != "unknown":
                if expected == predicted:
                    exact_match = 1
                    accuracy_percent = 100.0
                    field_accuracy_percent = 100.0
                    schema_compliance_percent = 100.0
                else:
                    exact_match = 0
                    accuracy_percent = 0.0
                    field_accuracy_percent = 0.0
                    schema_compliance_percent = 100.0 if predicted in ALLOWED_LABELS else 0.0

            # ---- Structured output tasks ----
            else:

                field_accuracy_percent, exact_match = compare_records(
                    expected_output,
                    model_output
                )

                accuracy_percent = float(exact_match * 100.0)

                schema_compliance_percent = schema_compliance_score(
                    expected_output,
                    model_output
                )

        except Exception:
            accuracy_percent = 0.0
            field_accuracy_percent = 0.0
            schema_compliance_percent = 0.0
            exact_match = 0

        quality_score = (
            accuracy_percent * self.quality_accuracy_weight
            + schema_compliance_percent * self.quality_schema_weight
        )

        if expected != "unknown" and predicted == expected:
            quality_score = 100.0

        return {
            "accuracy_percent": float(accuracy_percent),
            "field_accuracy_percent": float(field_accuracy_percent),
            "exact_record_match": int(exact_match),
            "schema_compliance_percent": float(schema_compliance_percent),
            "quality_score": float(quality_score),
        }
