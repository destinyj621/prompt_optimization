"""Model execution for local Ollama models."""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass

from benchmarking_backend.config import CONFIG


@dataclass
class ModelExecutionResult:
    output_text: str
    latency_ms: float
    prompt_tokens: int
    completion_tokens: int


class ModelExecutor:
    def __init__(self, command: str | None = None) -> None:
        self.command = command or CONFIG.models.ollama.command

    def execute(self, prompt_text: str, model_name: str) -> ModelExecutionResult:
        start = time.perf_counter()
        process = subprocess.run(
            [self.command, "run", model_name],
            input=prompt_text,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )
        end = time.perf_counter()

        if process.returncode != 0:
            error_text = process.stderr.strip() if process.stderr else "Unknown Ollama error"
            raise RuntimeError(f"Ollama execution failed for model '{model_name}': {error_text}")

        output_text = process.stdout.strip()
        latency_ms = (end - start) * 1000

        return ModelExecutionResult(
            output_text=output_text,
            latency_ms=latency_ms,
            prompt_tokens=len(prompt_text.split()),
            completion_tokens=len(output_text.split()),
        )