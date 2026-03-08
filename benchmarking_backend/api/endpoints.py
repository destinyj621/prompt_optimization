"""Thin backend endpoints for frontend integration."""

from __future__ import annotations

from typing import Any, Dict, Optional

from benchmarking_backend.config import CONFIG
from benchmarking_backend.database.repository import BenchmarkRepository
from benchmarking_backend.database.schema import ensure_schema_compat, initialize_schema
from benchmarking_backend.evaluation import AccuracyEvaluator
from benchmarking_backend.experiments import ExperimentRunner, MetricCollector, ModelExecutor, PromptBuilder


def _build_repository() -> BenchmarkRepository:
    repository = BenchmarkRepository()
    repository.connect()
    assert repository.connection is not None
    initialize_schema(repository.connection)
    ensure_schema_compat(repository.connection)
    repository.ensure_models(CONFIG.models.available_model_names)
    return repository


def get_tasks_endpoint() -> Dict[str, Any]:
    repository = _build_repository()
    try:
        return {"tasks": repository.list_tasks()}
    finally:
        repository.close()


def get_strategies_endpoint() -> Dict[str, Any]:
    repository = _build_repository()
    try:
        return {"strategies": repository.list_strategies()}
    finally:
        repository.close()


def get_models_endpoint() -> Dict[str, Any]:
    repository = _build_repository()
    try:
        return {"models": repository.list_models()}
    finally:
        repository.close()


def get_dataset_inputs_endpoint(limit: int | None = None) -> Dict[str, Any]:
    repository = _build_repository()
    try:
        safe_limit = None if limit is None else max(1, int(limit))
        return {"dataset_inputs": repository.list_dataset_inputs(limit=safe_limit)}
    finally:
        repository.close()


def get_recent_runs_endpoint(limit: int | None = 50) -> Dict[str, Any]:
    repository = _build_repository()
    try:
        safe_limit = 50 if limit is None else max(1, int(limit))
        return {"recent_runs": repository.list_recent_runs(limit=safe_limit)}
    finally:
        repository.close()


def run_experiment_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    if "task_id" not in payload or "strategy_id" not in payload or "model_id" not in payload:
        raise ValueError("task_id, strategy_id, and model_id are required.")

    task_id = int(payload["task_id"])
    strategy_id = int(payload["strategy_id"])
    model_id = int(payload["model_id"])
    run_count = int(payload.get("run_count", CONFIG.benchmark.repetition_count))
    if run_count < 1:
        raise ValueError("run_count must be at least 1.")

    input_text: Optional[str] = payload.get("input_text")
    if input_text is None:
        input_text = payload.get("raw_input")
    input_id_raw = payload.get("input_id")

    repository = _build_repository()
    try:
        input_id: Optional[int]
        if input_text is not None and str(input_text).strip():
            input_id = repository.insert_dataset_input(input_text=str(input_text).strip())
        elif input_id_raw is not None:
            input_id = int(input_id_raw)
        else:
            input_id = None

        runner = ExperimentRunner(
            repository=repository,
            model_executor=ModelExecutor(),
            metric_collector=MetricCollector(),
            prompt_builder=PromptBuilder(),
            accuracy_evaluator=AccuracyEvaluator(),
        )

        result = runner.run_experiment(
            task_id=task_id,
            strategy_id=strategy_id,
            model_id=model_id,
            trials_per_input=max(1, run_count),
            input_id=input_id,
        )
        return result
    finally:
        repository.close()
