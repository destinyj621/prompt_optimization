"""Builds final prompts from task, strategy template, and input."""

from __future__ import annotations

from typing import Any, Dict, List


class PromptBuilder:
    def build_prompt(
        self,
        task: Dict[str, Any],
        strategy: Dict[str, Any],
        input_text: str,
        examples: List[Dict[str, Any]] | None = None,
    ) -> str:
        template = (strategy.get("strategy_template") or "").strip()
        strategy_name = strategy.get("strategy_name", "")
        strategy_type = strategy.get("strategy_type", "")
        examples = examples or []

        examples_text = ""
        if examples:
            rows = ["Examples:"]
            for idx, example in enumerate(examples, start=1):
                rows.append(f"Example {idx} Input: {example['example_input']}")
                rows.append(f"Example {idx} Output: {example['example_output']}")
            examples_text = "\n".join(rows)

        if template:
            return template.format(
                task_name=task.get("task_name", ""),
                task_description=task.get("task_description", ""),
                strategy_name=strategy_name,
                strategy_type=strategy_type,
                strategy_description=strategy.get("description", ""),
                input_text=input_text,
                examples=examples_text,
                expected_output=task.get("expected_output", ""),
            )

        parts = [
            f"Task: {task.get('task_name', '')}",
            f"Task Description: {task.get('task_description', '')}",
            f"Strategy: {strategy_name} ({strategy_type})",
        ]
        if examples_text:
            parts.append(examples_text)
        parts.append(f"Input: {input_text}")
        parts.append("Output:")
        return "\n".join(parts)