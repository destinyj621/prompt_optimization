"""Evaluation metrics for output accuracy and quality."""

from __future__ import annotations

from dataclasses import dataclass

from .record_comparison import compare_records
from .schema_validation import schema_compliance_score


@dataclass
class AccuracyEvaluator:
    quality_accuracy_weight: float = 0.6
    quality_schema_weight: float = 0.4

    def evaluate(self, expected_output: str, model_output: str) -> dict[str, float | int]:
        field_accuracy, exact_match = compare_records(expected_output, model_output)
        schema_score = schema_compliance_score(expected_output, model_output)
        accuracy_percent = 100.0 if exact_match else field_accuracy
        quality_score = (
            self.quality_accuracy_weight * accuracy_percent
            + self.quality_schema_weight * schema_score
        )

        return {
            "accuracy_percent": accuracy_percent,
            "field_accuracy_percent": field_accuracy,
            "exact_record_match": int(exact_match),
            "schema_compliance_percent": schema_score,
            "quality_score": quality_score,
        }