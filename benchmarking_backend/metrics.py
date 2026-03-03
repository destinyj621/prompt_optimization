# Metrics calculation module for benchmarking results
import statistics
from typing import Dict, List


class MetricsCalculator:
    @staticmethod
    def calculate_accuracy(correct_predictions: int, total_samples: int) -> float:
        if total_samples == 0:
            return 0.0
        return (correct_predictions / total_samples) * 100

    @staticmethod
    def calculate_token_usage(prompt_tokens: int, completion_tokens: int) -> int:
        return prompt_tokens + completion_tokens

    @staticmethod
    def calculate_latency(latency_values_seconds: List[float]) -> float:
        if not latency_values_seconds:
            return 0.0
        return sum(latency_values_seconds) / len(latency_values_seconds)

    @staticmethod
    def calculate_variance(values: List[float]) -> float:
        if len(values) <= 1:
            return 0.0
        return statistics.variance(values)

    @staticmethod
    def calculate_energy(gpu_watts: float, latency_seconds: float) -> float:
        return (gpu_watts * latency_seconds) / (1000 * 3600)

    @staticmethod
    def calculate_efficiency_scores(accuracy: float, total_tokens: int, mean_latency: float) -> Dict[str, float]:
        efficiency_score = (accuracy / total_tokens) if total_tokens > 0 else 0.0
        latency_efficiency = (accuracy / mean_latency) if mean_latency > 0 else 0.0
        return {
            "efficiency_score": efficiency_score,
            "latency_efficiency": latency_efficiency,
        }
