"""Configuration loader for benchmarking backend."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


@dataclass(frozen=True)
class DatabaseConfig:
    host: str
    port: int
    user: str
    password: str
    name: str


@dataclass(frozen=True)
class EnergyConfig:
    gpu_power_watts: float
    cpu_power_watts: float
    energy_cost_per_kwh: float
    hardware_hourly_cost: float
    carbon_kg_per_kwh: float


@dataclass(frozen=True)
class BenchmarkConfig:
    default_batch_size: int
    repetition_count: int


@dataclass(frozen=True)
class ModelDefaults:
    temperature: float
    top_p: float
    max_tokens: int


@dataclass(frozen=True)
class TokenLimits:
    prompt_max_tokens: int
    completion_max_tokens: int
    total_max_tokens: int


@dataclass(frozen=True)
class OllamaConfig:
    base_url: str
    command: str


@dataclass(frozen=True)
class ModelConfig:
    available_model_names: List[str]
    defaults: ModelDefaults
    token_limits: TokenLimits
    ollama: OllamaConfig


@dataclass(frozen=True)
class PromptingConfig:
    example_required_task_keywords: List[str]
    example_required_strategy_types: List[str]
    example_library: Dict[str, List[Dict[str, Any]]]


@dataclass(frozen=True)
class AppConfig:
    database: DatabaseConfig
    energy: EnergyConfig
    benchmark: BenchmarkConfig
    models: ModelConfig
    prompting: PromptingConfig


def _settings_path() -> Path:
    return Path(__file__).resolve().parent / "settings.json"


def load_config() -> AppConfig:
    with _settings_path().open("r", encoding="utf-8") as config_file:
        raw: Dict[str, Any] = json.load(config_file)

    return AppConfig(
        database=DatabaseConfig(**raw["database"]),
        energy=EnergyConfig(**raw["energy"]),
        benchmark=BenchmarkConfig(**raw["benchmark"]),
        models=ModelConfig(
            available_model_names=raw["models"].get("available_model_names", []),
            defaults=ModelDefaults(**raw["models"]["defaults"]),
            token_limits=TokenLimits(**raw["models"]["token_limits"]),
            ollama=OllamaConfig(**raw["models"]["ollama"]),
        ),
        prompting=PromptingConfig(**raw["prompting"]),
    )


CONFIG = load_config()
