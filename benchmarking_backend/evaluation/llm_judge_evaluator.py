from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any
import re

from benchmarking_backend.experiments.model_executor import ModelExecutor


@dataclass
class LLMJudgeEvaluator:
    model_executor: ModelExecutor
    judge_model: str = "smallthinker" 


    def evaluate(
        self,
        task_type: str,
        input_text: str,
        reference: str,
        prediction: str,
    ) -> Dict[str, Any]:

        prompt = self._build_prompt(
            task_type=task_type,
            input_text=input_text,
            reference=reference,
            prediction=prediction,
        )

        result = self.model_executor.execute(
            prompt_text=prompt,
            model_name=self.judge_model,
        )

        return self._parse_score(result.output_text)

    def _build_prompt(
        self,
        task_type: str,
        input_text: str,
        reference: str,
        prediction: str,
    ) -> str:

        if task_type == "summarization":
            return f"""
You are an expert evaluator of summarization quality.

TASK: Evaluate a machine-generated summary.

DOCUMENT:
{input_text}

REFERENCE SUMMARY:
{reference}

MODEL SUMMARY:
{prediction}

Evaluate based on:
- factual correctness
- coverage of key points
- conciseness
- clarity

IMPORTANT RULES:
- Output ONLY a number between 0 and 100
- No words
- No explanation
- No punctuation
"""

        elif task_type == "qa":
            return f"""
You are an expert evaluator of question answering systems.

TASK: Evaluate an AI-generated answer.

CONTEXT:
{input_text}

REFERENCE ANSWER:
{reference}

MODEL ANSWER:
{prediction}

Evaluate based on:
- correctness
- completeness
- grounding in context
- clarity

IMPORTANT RULES:
- Output ONLY a number between 0 and 100
- No words
- No explanation
- No punctuation
"""

        else:
            raise ValueError(f"Unsupported task type: {task_type}")

    def _parse_score(self, text: str) -> Dict[str, Any]:
        """
        Extract first valid numeric score from model output.
        """
        if not text:
            return {"quality_score": 0.0}
        match = re.search(r"\d+(\.\d+)?", text)
        if match:
            try:
                score = float(match.group())
                score = max(0.0, min(100.0, score))
                return {
                    "quality_score": score,
                }
            except Exception:
                pass
        return {"quality_score": 0.0}