"""Core experiment orchestration."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from database_manager import DatabaseManager
from metrics import MetricsCalculator
from model_executor import ModelExecutor
from prompt_builder import PromptBuilder
from stability import ExperimentalControls


class ExperimentRunner:
    """Runs trials, stores results, and computes aggregate metrics."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        model_executor: ModelExecutor,
        metrics_calculator: MetricsCalculator,
        controls: ExperimentalControls,
        prompt_builder: PromptBuilder,
    ) -> None:
        self.db_manager = db_manager
        self.model_executor = model_executor
        self.metrics_calculator = metrics_calculator
        self.controls = controls
        self.prompt_builder = prompt_builder

    def enforce_experimental_controls(self) -> Dict[str, Any]:
        return self.controls.to_dict()

    def _estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Cost placeholder for local Ollama runs."""
        _ = prompt_tokens, completion_tokens
        return 0.0

    @staticmethod
    def _is_prediction_correct(output_text: str, expected_output: str) -> bool:
        return output_text.strip().lower() == expected_output.strip().lower()

    def run_multiple_trials(
        self,
        task: Dict[str, Any],
        strategy: Dict[str, Any],
        model: Dict[str, Any],
        dataset_inputs: List[Dict[str, Any]],
        trials_per_input: int,
        runtime_examples: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        controls = self.enforce_experimental_controls()
        run_records: List[Dict[str, Any]] = []

        examples = runtime_examples or self.db_manager.get_strategy_examples(
            strategy_id=strategy["strategy_id"],
            task_id=task["task_id"],
        )

        for input_row in dataset_inputs:
            input_id = input_row["input_id"]
            input_text = input_row["input_text"]

            for _ in range(trials_per_input):
                prompt_text = self.prompt_builder.build_prompt(
                    task=task,
                    strategy=strategy,
                    input_text=input_text,
                    examples=examples,
                )
                output_text, latency_ms, prompt_tokens, completion_tokens = self.model_executor.execute_model(
                    prompt_text=prompt_text,
                    model_name=model["model_name"],
                )

                latency_seconds = latency_ms / 1000
                total_tokens = self.metrics_calculator.calculate_token_usage(prompt_tokens, completion_tokens)
                energy_kwh = self.metrics_calculator.calculate_energy(
                    gpu_watts=float(controls["gpu_watts"]), latency_seconds=latency_seconds
                )
                estimated_cost = self._estimate_cost(prompt_tokens, completion_tokens)

                is_correct = self._is_prediction_correct(output_text, task["expected_output"])
                per_run_accuracy = self.metrics_calculator.calculate_accuracy(1 if is_correct else 0, 1)

                now = datetime.now()
                record = {
                    "task_id": task["task_id"],
                    "strategy_id": strategy["strategy_id"],
                    "model_id": model["model_id"],
                    "input_id": input_id,
                    "model_name": model["model_name"],
                    "temperature": controls["temperature"],
                    "top_p": controls["top_p"],
                    "max_tokens": controls["max_tokens"],
                    "hardware_environment": controls["hardware_environment"],
                    "run_date": now.date(),
                    "run_time": now.time().replace(microsecond=0),
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "estimated_cost": estimated_cost,
                    "latency_ms": latency_ms,
                    "quality_score": per_run_accuracy,
                    "energy_kwh": energy_kwh,
                    "output_text": output_text,
                }

                self.db_manager.insert_experiment_run(record)
                run_records.append(record)

        return run_records

    def compute_aggregated_strategy_metrics(self, run_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not run_records:
            return {
                "mean_latency": 0.0,
                "latency_variance": 0.0,
                "mean_token_usage": 0.0,
                "accuracy": 0.0,
                "energy_kwh_total": 0.0,
                "energy_proxy": 0.0,
                "efficiency_score": 0.0,
                "latency_efficiency": 0.0,
                "total_runs": 0,
            }

        latency_seconds_values = [record["latency_ms"] / 1000 for record in run_records]
        token_values = [record["total_tokens"] for record in run_records]

        correct_predictions = 0
        for record in run_records:
            if record["quality_score"] == 100.0:
                correct_predictions += 1

        mean_latency = self.metrics_calculator.calculate_latency(latency_seconds_values)
        latency_variance = self.metrics_calculator.calculate_variance(latency_seconds_values)
        mean_token_usage = sum(token_values) / len(token_values)
        total_tokens_all_runs = sum(token_values)

        accuracy = self.metrics_calculator.calculate_accuracy(correct_predictions, len(run_records))
        energy_kwh_total = sum(
            self.metrics_calculator.calculate_energy(self.controls.gpu_watts, latency)
            for latency in latency_seconds_values
        )

        energy_proxy = total_tokens_all_runs * mean_latency
        efficiency = self.metrics_calculator.calculate_efficiency_scores(
            accuracy=accuracy,
            total_tokens=total_tokens_all_runs,
            mean_latency=mean_latency,
        )

        return {
            "mean_latency": mean_latency,
            "latency_variance": latency_variance,
            "mean_token_usage": mean_token_usage,
            "accuracy": accuracy,
            "energy_kwh_total": energy_kwh_total,
            "energy_proxy": energy_proxy,
            "efficiency_score": efficiency["efficiency_score"],
            "latency_efficiency": efficiency["latency_efficiency"],
            "total_runs": len(run_records),
        }

    def run_experiment(
        self,
        task_id: int,
        strategy_id: int,
        model_id: int,
        trials_per_input: int,
        input_id: Optional[int] = None,
        runtime_examples: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        task = self.db_manager.get_task(task_id)
        strategy = self.db_manager.get_strategy(strategy_id)
        model = self.db_manager.get_model(model_id)

        if not task:
            raise ValueError(f"Task ID {task_id} not found.")
        if not strategy:
            raise ValueError(f"Strategy ID {strategy_id} not found.")
        if not model:
            raise ValueError(f"Model ID {model_id} not found.")

        if input_id is not None:
            input_row = self.db_manager.get_dataset_input(input_id)
            if not input_row:
                raise ValueError(f"Input ID {input_id} not found.")
            if input_row["task_id"] != task_id:
                raise ValueError(f"Input ID {input_id} does not belong to task ID {task_id}.")
            dataset_inputs = [input_row]
        else:
            dataset_inputs = self.db_manager.get_inputs_for_task(task_id)
            if not dataset_inputs:
                raise ValueError(f"No dataset inputs found for task ID {task_id}.")

        run_records = self.run_multiple_trials(
            task=task,
            strategy=strategy,
            model=model,
            dataset_inputs=dataset_inputs,
            trials_per_input=max(3, trials_per_input),
            runtime_examples=runtime_examples,
        )

        summary = self.compute_aggregated_strategy_metrics(run_records=run_records)
        summary.update(
            {
                "task_id": task["task_id"],
                "task_name": task["task_name"],
                "strategy_id": strategy["strategy_id"],
                "strategy_name": strategy["strategy_name"],
                "model_id": model["model_id"],
                "model_name": model["model_name"],
                "temperature": self.controls.temperature,
                "top_p": self.controls.top_p,
                "max_tokens": self.controls.max_tokens,
                "hardware_environment": self.controls.hardware_environment,
            }
        )

        return {
            "run_records": run_records,
            "summary": summary,
        }
