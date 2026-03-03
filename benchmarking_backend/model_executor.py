# Model execution module for running prompts against Ollama models and capturing metrics
import subprocess
import time
from typing import Tuple


class ModelExecutor:
    """Executes prompts against an Ollama model and captures runtime stats."""

    def execute_model(self, prompt_text: str, model_name: str) -> Tuple[str, float, int, int]:
        """Runs `ollama run <model_name>` and returns output + metrics.

        Returns:
            output_text, latency_ms, prompt_tokens, completion_tokens
        """
        start_time = time.time()
        process = subprocess.run(
            ["ollama", "run", model_name],
            input=prompt_text,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )
        end_time = time.time()

        latency_seconds = end_time - start_time
        latency_ms = latency_seconds * 1000

        if process.returncode != 0:
            error_text = process.stderr.strip() if process.stderr else "Unknown Ollama error"
            raise RuntimeError(f"Ollama execution failed for model '{model_name}': {error_text}")

        output_text = process.stdout.strip()
        prompt_tokens = len(prompt_text.split())
        completion_tokens = len(output_text.split())

        return output_text, latency_ms, prompt_tokens, completion_tokens
