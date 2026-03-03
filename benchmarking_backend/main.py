# Main entry point for the Prompt Optimization and Sustainability Benchmarking
from typing import Any, Dict, List

from config.config import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
    EXAMPLE_LIBRARY,
    EXAMPLE_REQUIRED_STRATEGY_TYPES,
    EXAMPLE_REQUIRED_TASK_KEYWORDS,
    GPU_POWER_WATTS,
)
from database_manager import DatabaseManager
from experiment_runner import ExperimentRunner
from metrics import MetricsCalculator
from model_executor import ModelExecutor
from prompt_builder import PromptBuilder
from stability import ExperimentalControls


def _prompt_int(label: str) -> int:
    """Reads a positive integer from stdin."""
    while True:
        raw_value = input(label).strip()
        try:
            value = int(raw_value)
            if value <= 0:
                raise ValueError
            return value
        except ValueError:
            print("Please enter a valid positive integer.")


def _prompt_non_empty(label: str) -> str:
    while True:
        value = input(label).strip()
        if value:
            return value
        print("Please enter a non-empty prompt.")


def _prompt_trials_min_3(label: str) -> int:
    while True:
        value = _prompt_int(label)
        if value >= 3:
            return value
        print("Please enter a value of at least 3.")


def _requires_examples(task_name: str, strategy_type: str) -> bool:
    normalized_task_name = (task_name or "").strip().lower()
    normalized_strategy_type = (strategy_type or "").strip().lower()

    strategy_requires = normalized_strategy_type in EXAMPLE_REQUIRED_STRATEGY_TYPES
    task_requires = any(keyword in normalized_task_name for keyword in EXAMPLE_REQUIRED_TASK_KEYWORDS)
    return strategy_requires or task_requires


def _prompt_required_examples(task_name: str, strategy_type: str) -> List[Dict[str, Any]]:
    """Collects examples from CLI when the selected task/strategy requires it."""
    if not _requires_examples(task_name=task_name, strategy_type=strategy_type):
        return []

    normalized_task_name = (task_name or "").strip().lower()
    normalized_strategy_type = (strategy_type or "").strip().lower()

    # Prefer config-defined examples first.
    if normalized_strategy_type in EXAMPLE_LIBRARY:
        print(f"Using configured examples for strategy_type='{normalized_strategy_type}'.")
        return EXAMPLE_LIBRARY[normalized_strategy_type]

    for keyword in EXAMPLE_REQUIRED_TASK_KEYWORDS:
        if keyword in normalized_task_name and keyword in EXAMPLE_LIBRARY:
            print(f"Using configured examples for task keyword='{keyword}'.")
            return EXAMPLE_LIBRARY[keyword]

    # Fallback to manual entry if no configured examples are available.
    example_count = _prompt_int("Enter number of examples required for this task/strategy: ")
    while example_count < 1:
        print("Please enter at least 1 example.")
        example_count = _prompt_int("Enter number of examples required for this task/strategy: ")

    examples: List[Dict[str, Any]] = []
    for idx in range(1, example_count + 1):
        example_input = _prompt_non_empty(f"Example {idx} input: ")
        example_output = _prompt_non_empty(f"Example {idx} output: ")
        examples.append(
            {
                "example_input": example_input,
                "example_output": example_output,
                "example_order": idx,
            }
        )
    return examples


def _print_available_options(db_manager: DatabaseManager) -> None:
    """Displays available tasks, strategies, and models."""
    tasks = db_manager.list_tasks()
    strategies = db_manager.list_strategies()
    models = db_manager.list_models()

    print("\nAvailable Tasks")
    for task in tasks:
        print(f"{task['task_id']} - {task['task_name']}")

    print("\nAvailable Prompt Strategies")
    for strategy in strategies:
        print(f"{strategy['strategy_id']} - {strategy['strategy_name']}")

    print("\nAvailable Models")
    for model in models:
        print(f"{model['model_id']} - {model['model_name']}")


def _print_summary(summary: dict) -> None:
    rows = [
        ("Task", summary["task_name"]),
        ("Strategy", summary["strategy_name"]),
        ("Model", summary["model_name"]),
        ("Total Runs", summary["total_runs"]),
        ("Mean Latency (s)", f"{summary['mean_latency']:.6f}"),
        ("Latency Variance", f"{summary['latency_variance']:.6f}"),
        ("Mean Token Usage", f"{summary['mean_token_usage']:.2f}"),
        ("Accuracy (%)", f"{summary['accuracy']:.2f}"),
        ("Energy (kWh total)", f"{summary['energy_kwh_total']:.10f}"),
        ("Energy Proxy", f"{summary['energy_proxy']:.6f}"),
        ("Efficiency Score", f"{summary['efficiency_score']:.10f}"),
        ("Latency Efficiency", f"{summary['latency_efficiency']:.6f}"),
        ("Temperature", summary["temperature"]),
        ("Top-p", summary["top_p"]),
        ("Max Tokens", summary["max_tokens"]),
        ("Hardware", summary["hardware_environment"]),
    ]

    print("\nBenchmark Summary")
    print("-" * 90)
    for metric, value in rows:
        print(f"{metric:<22} | {value}")
    print("-" * 90)


def main() -> None:
    db_manager = DatabaseManager()
    db_manager.connect_to_mysql()

    model_executor = ModelExecutor()
    metrics_calculator = MetricsCalculator()
    prompt_builder = PromptBuilder()

    controls = ExperimentalControls(
        temperature=DEFAULT_TEMPERATURE,
        top_p=DEFAULT_TOP_P,
        max_tokens=DEFAULT_MAX_TOKENS,
        gpu_watts=GPU_POWER_WATTS,
    )

    runner = ExperimentRunner(
        db_manager=db_manager,
        model_executor=model_executor,
        metrics_calculator=metrics_calculator,
        controls=controls,
        prompt_builder=prompt_builder,
    )

    try:
        print("Prompt Optimization and Sustainability Benchmarking")
        _print_available_options(db_manager)

        task_id = _prompt_int("\nEnter task_id: ")
        strategy_id = _prompt_int("Enter strategy_id: ")
        model_id = _prompt_int("Enter model_id: ")
        input_prompt = _prompt_non_empty("Enter input prompt: ")
        trials_per_input = _prompt_trials_min_3("Enter number of trials (minimum 3): ")

        task = db_manager.get_task(task_id)
        if not task:
            raise ValueError(f"Task ID {task_id} not found.")

        strategy = db_manager.get_strategy(strategy_id)
        if not strategy:
            raise ValueError(f"Strategy ID {strategy_id} not found.")

        runtime_examples = _prompt_required_examples(
            task_name=task.get("task_name", ""),
            strategy_type=strategy.get("strategy_type", ""),
        )
        input_id = db_manager.insert_dataset_input(task_id=task_id, input_text=input_prompt)
        print(f"Inserted dataset input with input_id={input_id}")

        result = runner.run_experiment(
            task_id=task_id,
            strategy_id=strategy_id,
            model_id=model_id,
            trials_per_input=trials_per_input,
            input_id=input_id,
            runtime_examples=runtime_examples,
        )

        summary = result["summary"]
        _print_summary(summary)
        print(f"Inserted run rows: {len(result['run_records'])}")

    finally:
        db_manager.close()


if __name__ == "__main__":
    main()
