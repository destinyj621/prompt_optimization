# Prompt Optimization and Sustainability Benchmarking

Python backend for benchmarking prompt strategies against local LLMs via Ollama, with run-level metrics stored in MySQL.

## What This Project Does

The system runs controlled experiments where you select:

- `task_id`
- `strategy_id`
- `model_id`
- `trials_per_input` (minimum 3)

Then it:

1. Takes a user prompt from CLI
2. Inserts it into `dataset_inputs`
3. Builds final prompt text using the selected strategy
4. Runs the model through `ollama run <model_name>` for each trial
5. Records per-run metrics into `experiment_runs`

## Tech Stack

- Python 3
- MySQL (`mysql-connector-python`)
- Ollama (local model execution via `subprocess`)

## Project Structure

```text
benchmarking_backend/
  main.py
  database_manager.py
  experiment_runner.py
  metrics.py
  model_executor.py
  prompt_builder.py
  report_generator.py
  stability.py
  config/
    config.py
```

## Database Tables Used

- `tasks`
- `prompt_strategies`
- `models`
- `dataset_inputs`
- `experiment_runs`

Schema file:

- `create_prompt_benchmark_schema.sql`

## Install

From repo root:

```powershell
python -m pip install -r requirements.txt
```

## Configuration

All constants are in:

- `benchmarking_backend/config/config.py`

This includes:

- DB connection constants (`DB_HOST`, `DB_USER`, etc.)
- generation defaults (`DEFAULT_TEMPERATURE`, `DEFAULT_TOP_P`, `DEFAULT_MAX_TOKENS`)
- sustainability constants (`GPU_POWER_WATTS`, etc.)
- example library (`EXAMPLE_LIBRARY`)

## Run

From repo root:

```powershell
cd benchmarking_backend
python main.py
```

CLI flow:

1. Shows available tasks, strategies, models
2. Prompts for:
   - `task_id`
   - `strategy_id`
   - `model_id`
   - `input prompt`
   - `number of trials (minimum 3)`
3. Runs experiment and prints summary
4. Inserts each run into `experiment_runs`

## Prompt Strategy Behavior

Prompt construction is handled in:

- `benchmarking_backend/prompt_builder.py`

Supported strategy patterns:

- baseline / zero-shot
- few-shot
- chain-of-thought / reasoning
- role prompting
- format constrained / structured

Examples are loaded from `EXAMPLE_LIBRARY` in config when required.

## Metrics Collected Per Run

- `prompt_tokens`
- `completion_tokens`
- `total_tokens`
- `latency_ms`
- `estimated_cost` (0 for local runs)
- `energy_kwh`
- `quality_score`
- `output_text`

## Notes

- Models run locally via `ollama run <model_name>`.
- `model_name` must exist in `models` and be available in Ollama.
- Current quality scoring is strict expected-output matching.

## Quick Start Checklist

1. Create DB schema from `create_prompt_benchmark_schema.sql`
2. Insert rows into `tasks`, `prompt_strategies`, `models`
3. Ensure Ollama model exists locally
4. Set DB constants in `config/config.py`
5. Run `python benchmarking_backend/main.py`
