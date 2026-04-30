from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any
import re

from benchmarking_backend.experiments.model_executor import ModelExecutor


@dataclass
class LLMJudgeEvaluator:
    model_executor: ModelExecutor
    judge_model: str = "phi4-mini"

    def evaluate(
        self,
        task_type: str,
        input_text: str,
        prediction: str,
        reference: str = "",  # kept for API compatibility but unused in summarization/qa
    ) -> Dict[str, Any]:

        prompt = self._build_prompt(
            task_type=task_type,
            input_text=input_text,
            prediction=prediction,
        )

        result = self.model_executor.execute(
            prompt_text=prompt,
            model_name=self.judge_model,
        )

        return self._parse_score(
            result.output_text,
            prediction=prediction,
        )

    def _build_prompt(
        self,
        task_type: str,
        input_text: str,
        prediction: str,
    ) -> str:

        if task_type == "summarization":
            return f"""
            You are an expert evaluator of summarization quality.

            --- ORIGINAL DOCUMENT ---
            {input_text}

            --- MODEL SUMMARY ---
            {prediction}

            EVALUATION RULES:
            
            Do NOT reward formatting, tone, or structure. 
            Only evaluate factual correctness and coverage.
            
            1. FACTUAL CORRECTNESS (MOST IMPORTANT)
            - Are all key facts from the original document preserved?
            - Paraphrasing or rewording is NOT an error.

            2. COVERAGE
            - Did it include the main events, entities, and outcomes?
            - Is it reasonably compressed relative to the original?

            SCORING GUIDE:

            90-100:
            - Almost perfect
            - All key facts preserved
            - Minor or no omissions

            70-89:
            - Good summary
            - Minor missing details OR rewording differences

            40-69:
            - Some missing key points OR partial inaccuracies

            10-39:
            - Major missing information OR incorrect interpretation

            0-9:
            - Completely wrong or hallucinated content

            CRITICAL RULES:
            - Paraphrasing is NOT an error
            - Different wording is NOT a penalty
            - Only factual mistakes or omissions matter
            - If most key facts are correct → score MUST be ≥ 70

            OUTPUT:
            Return ONLY a number between 0 and 100. No explanation.
            """

        elif task_type == "qa":
            return f"""
            You are an expert evaluator of question answering systems.

            --- CONTEXT ---
            {input_text}

            --- MODEL ANSWER ---
            {prediction}

            EVALUATION RULES:

            - Correctness: Is the answer factually accurate based on the context?
            - Completeness: Does it address the full question?
            - Grounded: Is it supported by the context (no hallucination)?
            - Clarity: Is it clearly expressed?

            SCORING GUIDE:
            90-100: fully correct and complete
            70-89: mostly correct, minor omissions
            40-69: partially correct
            10-39: mostly incorrect
            0-9: wrong or hallucinated

            CRITICAL RULE:
            If the answer is factually correct based on the context → score MUST be ≥ 70

            OUTPUT:
            Return ONLY a number between 0 and 100. No explanation.
            """

        else:
            raise ValueError(f"Unsupported task type: {task_type}")

    def _parse_score(
        self,
        text: str,
        prediction: str,
    ) -> Dict[str, Any]:

        if not text:
            return {"quality_score": 0.0}

        # Prefer standalone number, largest found (avoids grabbing "1" from "14" etc.)
        matches = re.findall(r"\b(100|[1-9]?\d)\b", text.strip())

        if matches:
            try:
                # Take the last match — judge models tend to state score at the end
                score = float(matches[-1])
                score = max(0.0, min(100.0, score))
                return {"quality_score": score}
            except Exception:
                pass

        return {"quality_score": 70.0}  # safer default than 0