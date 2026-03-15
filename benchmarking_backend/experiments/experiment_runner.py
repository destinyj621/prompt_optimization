"""Experiment orchestration with full reproducibility capture."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from benchmarking_backend.config import CONFIG
from benchmarking_backend.database.repository import BenchmarkRepository
from benchmarking_backend.evaluation import AccuracyEvaluator

from .metric_collection import MetricCollector
from .model_executor import ModelExecutor
from .prompt_builder import PromptBuilder


class ExperimentRunner:
    def __init__(
        self,
        repository: BenchmarkRepository,
        model_executor: ModelExecutor,
        metric_collector: MetricCollector,
        prompt_builder: PromptBuilder,
        accuracy_evaluator: AccuracyEvaluator,
    ) -> None:
        self.repository = repository
        self.model_executor = model_executor
        self.metric_collector = metric_collector
        self.prompt_builder = prompt_builder
        self.accuracy_evaluator = accuracy_evaluator

    def run_experiment(
        self,
        task_id: int,
        strategy_id: int,
        model_id: int,
        trials_per_input: Optional[int] = None,
        input_id: Optional[int] = None,
        runtime_examples: Optional[List[Dict[str, Any]]] = None,
        prompt_config: Optional[Dict[str, str]] = None,
        experiment_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        task = self.repository.get_task(task_id)
        strategy = self.repository.get_strategy(strategy_id)
        model = self.repository.get_model(model_id)

        if not task:
            raise ValueError(f"Task ID {task_id} not found.")
        if not strategy:
            raise ValueError(f"Strategy ID {strategy_id} not found.")
        if not model:
            raise ValueError(f"Model ID {model_id} not found.")

        if input_id is not None:
            input_row = self.repository.get_dataset_input(input_id)
            if not input_row:
                raise ValueError(f"Input ID {input_id} not found.")
            dataset_inputs = [input_row]
        else:
            dataset_inputs = self.repository.list_dataset_inputs(
                limit=CONFIG.benchmark.default_batch_size
            )
            if not dataset_inputs:
                raise ValueError("No dataset inputs found.")

        trials = trials_per_input if trials_per_input is not None else CONFIG.benchmark.repetition_count
        if trials <= 0:
            raise ValueError("trials_per_input must be > 0.")

        examples = runtime_examples or self.repository.get_strategy_examples(
            strategy_id=strategy_id,
            task_id=task_id,
        )

        run_records: List[Dict[str, Any]] = []
        for input_row in dataset_inputs:
            for _ in range(trials):
                input_text = input_row["input_text"]
                prompt_text = self.prompt_builder.build_prompt(
                    task=task,
                    strategy=strategy,
                    input_text=input_text,
                    examples=examples,
                    prompt_config=prompt_config,
                )
                print("BUILT PROMPT START")
                print(prompt_text)
                print("BUILT PROMPT END")

                execution = self.model_executor.execute(
                    prompt_text=prompt_text,
                    model_name=model["model_name"],
                )

                now = datetime.now()
                time_id = self.repository.get_or_create_run_time(now)

                metrics = self.metric_collector.collect(
                    latency_ms=execution.latency_ms,
                    prompt_tokens=execution.prompt_tokens,
                    completion_tokens=execution.completion_tokens,
                ) or {}

                evaluation = self.accuracy_evaluator.evaluate(
                    expected_output=input_row.get("expected_label", ""),
                    model_output=execution.output_text,
                )

                evaluation.setdefault("accuracy_percent", 0.0)
                evaluation.setdefault("field_accuracy_percent", 0.0)
                evaluation.setdefault("exact_record_match", 0)
                evaluation.setdefault("schema_compliance_percent", 0.0)
                evaluation.setdefault("quality_score", 0.0)

                run_data: Dict[str, Any] = {
                    "task_id": task_id,
                    "strategy_id": strategy_id,
                    "model_id": model_id,
                    "input_id": input_row["input_id"],
                    "input_text": input_text,
                    "time_id": time_id,
                    "input_prompt": prompt_text,
                    "output_text": execution.output_text,
                    "experiment_run_id": experiment_run_id,
                    **metrics,
                    **evaluation,
                }

                run_id = self.repository.insert_experiment_run(run_data)
                run_data["run_id"] = run_id
                run_records.append(run_data)

        summary = self._summarize(run_records)
        summary.update(
            {
                "task_id": task_id,
                "task_name": task["task_name"],
                "strategy_id": strategy_id,
                "strategy_name": strategy["strategy_name"],
                "model_id": model_id,
                "model_name": model["model_name"],
            }
        )
        return {"run_records": run_records, "summary": summary}

    @staticmethod
    def _summarize(run_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        total_runs = len(run_records)
        if total_runs == 0:
            return {
                "total_runs": 0,
                "mean_latency_ms": 0.0,
                "mean_total_tokens": 0.0,
                "mean_accuracy_percent": 0.0,
                "mean_quality_score": 0.0,
                "mean_throughput_tokens_per_sec": 0.0,
                "mean_throughput_requests_per_sec": 0.0,
                "total_energy_kwh": 0.0,
                "total_energy_cost": 0.0,
                "total_hardware_cost": 0.0,
                "total_carbon_kg": 0.0,
            }

        return {
            "total_runs": total_runs,
            "mean_latency_ms": sum(r["latency_ms"] for r in run_records) / total_runs,
            "mean_total_tokens": sum(r["total_tokens"] for r in run_records) / total_runs,
            "mean_accuracy_percent": sum(r["accuracy_percent"] for r in run_records) / total_runs,
            "mean_quality_score": sum(r["quality_score"] for r in run_records) / total_runs,
            "mean_throughput_tokens_per_sec": sum(r["throughput_tokens_per_sec"] for r in run_records) / total_runs,
            "mean_throughput_requests_per_sec": sum(
                r["throughput_requests_per_sec"] for r in run_records
            )
            / total_runs,
            "total_energy_kwh": sum(r["energy_kwh"] for r in run_records),
            "total_energy_cost": sum(r["energy_cost"] for r in run_records),
            "total_hardware_cost": sum(r["hardware_cost"] for r in run_records),
            "total_carbon_kg": sum(r.get("carbon_kg", 0.0) for r in run_records),
        }
