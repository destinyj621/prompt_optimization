"""Experimental control settings used to keep benchmark runs stable."""

import platform
from dataclasses import dataclass
from typing import Dict

from config.config import DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE, DEFAULT_TOP_P, GPU_POWER_WATTS


@dataclass
class ExperimentalControls:
    """Parameters that must remain constant across strategy comparisons."""

    temperature: float = DEFAULT_TEMPERATURE
    top_p: float = DEFAULT_TOP_P
    max_tokens: int = DEFAULT_MAX_TOKENS
    gpu_watts: float = GPU_POWER_WATTS
    hardware_environment: str = ""

    def __post_init__(self) -> None:
        if not self.hardware_environment:
            machine = platform.machine()
            processor = platform.processor() or "unknown-cpu"
            system = platform.platform()
            self.hardware_environment = f"{system} | {machine} | {processor}"

    def to_dict(self) -> Dict[str, float | int | str]:
        return {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "hardware_environment": self.hardware_environment,
            "gpu_watts": self.gpu_watts,
        }
