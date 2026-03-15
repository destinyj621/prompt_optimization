from __future__ import annotations
from typing import Any, Dict, List, Optional


class PromptBuilder:
    def build_prompt(
        self,
        task: Dict[str, Any],
        strategy: Dict[str, Any],
        input_text: str,
        examples: List[Dict[str, Any]] | None = None,
        prompt_config: Optional[Dict[str, str]] = None,
    ) -> str:

        template = (strategy.get("strategy_template") or "").strip()
        strategy_name = strategy.get("strategy_name", "")
        strategy_type = strategy.get("strategy_type", "")

        examples = examples or []
        prompt_config = prompt_config or {}

        system_prompt = (prompt_config.get("system_prompt") or "").strip()
        instruction_prompt = (prompt_config.get("instruction_prompt") or "").strip()
        context = (prompt_config.get("context") or "").strip()

        # # Only include examples for few-shot strategies
        # examples_text = ""
        # if examples and "few" in strategy_name.lower():
        #     rows = ["Examples:"]
        #     for idx, example in enumerate(examples, start=1):
        #         rows.append(f"Example {idx}:")
        #         rows.append(f"Input: {example['example_input']}")
        #         rows.append(f"Output: {example['example_output']}")
        #         rows.append("")
        #     examples_text = "\n".join(rows)

        prompt_sections: List[str] = []

        if system_prompt:
            prompt_sections.append(f"System: {system_prompt}")

        if instruction_prompt:
            prompt_sections.append(f"Instructions:\n{instruction_prompt}")

        if context:
            prompt_sections.append(f"Additional Context:\n{context}")

        # If a strategy template exists, use it
        if template:
            prompt_sections.append(
                template.format(
                    task_name=task.get("task_name", ""),
                    task_description=task.get("task_description", ""),
                    strategy_name=strategy_name,
                    strategy_type=strategy_type,
                    strategy_description=strategy.get("description", ""),
                    input_text=input_text,
                    # examples=examples_text,
                    expected_output=task.get("expected_output", ""),
                )
            )

            return "\n\n".join(section for section in prompt_sections if section)

        # Default fallback prompt
        parts = [
            f"Task: {task.get('task_name', '')}",
            f"Task Description: {task.get('task_description', '')}",
            f"Strategy: {strategy_name} ({strategy_type})",
        ]

        # if examples_text:
        #     parts.append(examples_text)

        parts.append(f"Text:\n{input_text}")
        parts.append("Answer:")

        prompt_sections.append("\n".join(parts))

        return "\n\n".join(section for section in prompt_sections if section)