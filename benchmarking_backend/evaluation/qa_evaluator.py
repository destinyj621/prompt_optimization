from dataclasses import dataclass
import re
from collections import Counter

@dataclass
class QAEvaluator:

    def normalize(self, text: str) -> str:
        return re.sub(r"\s+", " ", text.strip().lower())

    def tokenize(self, text: str):
        return self.normalize(text).split()

    def evaluate(self, reference: str, prediction: str) -> dict[str, float]:

        ref = self.tokenize(reference)
        pred = self.tokenize(prediction)

        if not ref or not pred:
            return {
                "exact_match": 0.0,
                "f1_score": 0.0,
                "quality_score": 0.0,
            }

        ref_counter = Counter(ref)
        pred_counter = Counter(pred)

        overlap = sum((ref_counter & pred_counter).values())

        precision = overlap / len(pred) if pred else 0.0
        recall = overlap / len(ref) if ref else 0.0

        f1 = (
            (2 * precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )

        exact_match = 1.0 if ref == pred else 0.0

        quality_score = (f1 * 100)

        return {
            "exact_match": exact_match,
            "f1_score": f1 * 100,
            "quality_score": quality_score,
        }