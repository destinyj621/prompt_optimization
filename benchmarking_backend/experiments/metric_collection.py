"""Collects run-level metrics from execution results."""

from __future__ import annotations

from dataclasses import dataclass

from benchmarking_backend.config import CONFIG


@dataclass
class MetricCollector:
    gpu_power_watts: float = CONFIG.energy.gpu_power_watts
    energy_cost_per_kwh: float = CONFIG.energy.energy_cost_per_kwh
    hardware_hourly_cost: float = CONFIG.energy.hardware_hourly_cost
    carbon_kg_per_kwh: float = CONFIG.energy.carbon_kg_per_kwh

    def collect(
        self,
        latency_ms: float,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> dict[str, float | int]:
        total_tokens = prompt_tokens + completion_tokens
        latency_seconds = latency_ms / 1000.0

        throughput_tokens_per_sec = (
            total_tokens / latency_seconds if latency_seconds > 0 else 0.0
        )
        throughput_requests_per_sec = (1.0 / latency_seconds) if latency_seconds > 0 else 0.0

        energy_kwh = (self.gpu_power_watts * latency_seconds) / (1000.0 * 3600.0)
        energy_cost = energy_kwh * self.energy_cost_per_kwh
        hardware_cost = (latency_seconds / 3600.0) * self.hardware_hourly_cost
        carbon_kg = energy_kwh * self.carbon_kg_per_kwh

        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "latency_ms": latency_ms,
            "throughput_tokens_per_sec": throughput_tokens_per_sec,
            "throughput_requests_per_sec": throughput_requests_per_sec,
            "energy_kwh": energy_kwh,
            "energy_cost": energy_cost,
            "hardware_cost": hardware_cost,
            "carbon_kg": carbon_kg,
        }