from __future__ import annotations

import os
import sys
from typing import Any, Dict, List

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from benchmarking_backend.api.endpoints import (  # noqa: E402
    get_dataset_inputs_endpoint,
    get_models_endpoint,
    get_recent_runs_endpoint,
    get_strategies_endpoint,
    get_tasks_endpoint,
    run_experiment_endpoint,
)


def get_tasks() -> List[Dict[str, Any]]:
    return get_tasks_endpoint()["tasks"]


def get_strategies() -> List[Dict[str, Any]]:
    return get_strategies_endpoint()["strategies"]


def get_models() -> List[Dict[str, Any]]:
    return get_models_endpoint()["models"]


def get_dataset_inputs(limit: int | None = 200) -> List[Dict[str, Any]]:
    return get_dataset_inputs_endpoint(limit=limit)["dataset_inputs"]


def get_recent_runs(limit: int | None = 100) -> List[Dict[str, Any]]:
    return get_recent_runs_endpoint(limit=limit)["recent_runs"]


def run_experiment(request_payload: Dict[str, Any]) -> Dict[str, Any]:
    return run_experiment_endpoint(request_payload)
