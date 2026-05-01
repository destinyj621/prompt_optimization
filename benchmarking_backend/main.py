"""CLI entry point for prompt optimization benchmarking backend."""

from __future__ import annotations

from typing import Any, Dict, List

from benchmarking_backend.config import CONFIG
from benchmarking_backend.database import BenchmarkRepository
from benchmarking_backend.database.schema import ensure_schema_compat, initialize_schema
from benchmarking_backend.evaluation import AccuracyEvaluator
from benchmarking_backend.experiments import ExperimentRunner, MetricCollector, ModelExecutor, PromptBuilder


def _prompt_int(label: str, minimum: int = 1) -> int:
    while True:
        value = input(label).strip()
        try:
            parsed = int(value)
        except ValueError:
            print("Please enter a valid integer.")
            continue
        if parsed < minimum:
            print(f"Please enter a value >= {minimum}.")
            continue
        return parsed


def _prompt_non_empty(label: str) -> str:
    while True:
        value = input(label).strip()
        if value:
            return value
        print("Value cannot be empty.")


def _requires_examples(task_name: str, strategy_type: str) -> bool:
    task = task_name.strip().lower()
    strategy = strategy_type.strip().lower()
    strategy_requires = strategy in CONFIG.prompting.example_required_strategy_types
    task_requires = any(keyword in task for keyword in CONFIG.prompting.example_required_task_keywords)
    return strategy_requires or task_requires


def _prompt_required_examples(task_name: str, strategy_type: str) -> List[Dict[str, Any]]:
    if not _requires_examples(task_name=task_name, strategy_type=strategy_type):
        return []

    task = task_name.strip().lower()
    strategy = strategy_type.strip().lower()

    if strategy in CONFIG.prompting.example_library:
        return CONFIG.prompting.example_library[strategy]

    for keyword in CONFIG.prompting.example_required_task_keywords:
        if keyword in task and keyword in CONFIG.prompting.example_library:
            return CONFIG.prompting.example_library[keyword]

    examples: List[Dict[str, Any]] = []
    count = _prompt_int("Enter number of examples: ", minimum=1)
    for idx in range(1, count + 1):
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


def _print_options(repo: BenchmarkRepository) -> None:
    print("\nAvailable Tasks")
    for task in repo.list_tasks():
        print(f"{task['task_id']} - {task['task_name']}")

    print("\nAvailable Strategies")
    for strategy in repo.list_strategies():
        print(f"{strategy['strategy_id']} - {strategy['strategy_name']}")

    print("\nAvailable Models")
    for model in repo.list_models():
        print(f"{model['model_id']} - {model['model_name']}")


def _print_summary(summary: Dict[str, Any]) -> None:
    print("\nBenchmark Summary")
    print("-" * 80)
    print(f"Task: {summary['task_name']}")
    print(f"Strategy: {summary['strategy_name']}")
    print(f"Model: {summary['model_name']}")
    print(f"Total Runs: {summary['total_runs']}")
    print(f"Mean Latency (ms): {summary['mean_latency_ms']:.3f}")
    print(f"Mean Tokens: {summary['mean_total_tokens']:.2f}")
    print(f"Mean Accuracy (%): {summary['mean_accuracy_percent']:.2f}")
    print(f"Mean Quality Score: {summary['mean_quality_score']:.2f}")
    print(f"Total Energy (kWh): {summary['total_energy_kwh']:.10f}")
    print(f"Total Energy Cost: ${summary['total_energy_cost']:.6f}")
    print(f"Total Hardware Cost: ${summary['total_hardware_cost']:.6f}")
    print("-" * 80)


def main() -> None:
    repository = BenchmarkRepository()
    repository.connect()
    assert repository.connection is not None
    initialize_schema(repository.connection)
    ensure_schema_compat(repository.connection)
    repository.ensure_models(CONFIG.models.available_model_names)

    runner = ExperimentRunner(
        repository=repository,
        model_executor=ModelExecutor(),
        metric_collector=MetricCollector(),
        prompt_builder=PromptBuilder(),
        accuracy_evaluator=AccuracyEvaluator(),
    )

    try:
        print("Prompt Optimization Benchmarking")
        _print_options(repository)

        task_id = _prompt_int("\nEnter task_id: ")
        strategy_id = _prompt_int("Enter strategy_id: ")
        model_id = _prompt_int("Enter model_id: ")
        input_text = _prompt_non_empty("Enter input prompt: ")
        trials = _prompt_int(
            f"Enter number of trials (default {CONFIG.benchmark.repetition_count}): ",
            minimum=1,
        )

        task = repository.get_task(task_id)
        if not task:
            raise ValueError(f"Task ID {task_id} not found.")

        strategy = repository.get_strategy(strategy_id)
        if not strategy:
            raise ValueError(f"Strategy ID {strategy_id} not found.")

        runtime_examples = _prompt_required_examples(
            task_name=task.get("task_name") or "",
            strategy_type=strategy.get("strategy_type") or "",
        )

        input_id = repository.insert_dataset_input(input_text=input_text, expected_label="")

        result = runner.run_experiment(
            task_id=task_id,
            strategy_id=strategy_id,
            model_id=model_id,
            trials_per_input=trials,
            input_id=input_id,
            runtime_examples=runtime_examples,
        )

        _print_summary(result["summary"])
        print(f"Inserted run rows: {len(result['run_records'])}")

    finally:
        repository.close()


if __name__ == "__main__":
    main()
