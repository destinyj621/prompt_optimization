"""Prompt construction logic by task + strategy + input."""

from typing import Any, Dict, List


class PromptBuilder:
    """Builds prompts for predefined prompt engineering strategies."""

    def build_prompt(
        self,
        task: Dict[str, Any],
        strategy: Dict[str, Any],
        input_text: str,
        examples: List[Dict[str, Any]],
    ) -> str:
        strategy_type = (strategy.get("strategy_type") or "").strip().lower()
        strategy_description = strategy.get("description") or "Follow the strategy instructions."

        parts = [
            f"Task: {task['task_name']}",
            f"Task Description: {task['task_description']}",
            f"Strategy Instructions: {strategy_description}",
        ]

        included_examples = False

        if strategy_type in {"baseline", "zero-shot"}:
            parts.append("Instruction: Provide the best direct answer.")
        elif strategy_type == "few-shot":
            parts.append("Instruction: Learn from the examples and follow the same pattern.")
            if examples:
                included_examples = True
        elif strategy_type in {"chain-of-thought", "cot", "reasoning"}:
            parts.append("Instruction: Think through the problem step-by-step, then provide the final answer.")
        elif strategy_type in {"role", "role prompting", "role-prompting"}:
            parts.append("Instruction: Answer as a domain expert relevant to this task.")
        elif strategy_type in {"format", "format constrained", "format-constrained", "structured"}:
            parts.append("Instruction: Return the answer in a strict structured format.")
            if examples:
                included_examples = True

        if examples and included_examples:
            parts.append("Examples:")
            for idx, example in enumerate(examples, start=1):
                parts.append(f"Example {idx} Input: {example['example_input']}")
                parts.append(f"Example {idx} Output: {example['example_output']}")
        elif examples and not included_examples:
            parts.append("Reference Examples:")
            for idx, example in enumerate(examples, start=1):
                parts.append(f"Example {idx} Input: {example['example_input']}")
                parts.append(f"Example {idx} Output: {example['example_output']}")

        parts.append(f"Input: {input_text}")
        parts.append("Output:")
        return "\n".join(parts)
