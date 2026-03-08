# Prompt Benchmarking System

End-to-end Streamlit + Python backend system for benchmarking prompt strategies on local LLMs (Ollama) with experiment metrics stored in MySQL.

## What It Does

You can run experiments by selecting:

- Task
- Prompt strategy
- Model
- Dataset input (existing) or raw input text
- Number of runs (`>= 1`)

For each run, the system:

1. Builds the final prompt from the strategy template + input
2. Executes the selected model with Ollama
3. Measures latency and token usage
4. Computes throughput, energy, and evaluation metrics
5. Stores a full run record in MySQL
6. Displays run-level results and summary in the UI

## Required Services

## 1) MySQL must be running and reachable

The app reads/writes from MySQL on every page load and run.

Connection settings are in:

- `benchmarking_backend/config/settings.json` under `database`

Default values:

- host: `localhost`
- port: `3306`
- user: `root`
- password: ``
- database: `prompt_benchmark`

If MySQL is not running or credentials are wrong, UI pages will show connection errors.

## 2) Ollama must be running with required models available

Configured model list (auto-synced into `models` table):

- `llama3.1:8b`
- `mistral`
- `gemma:7b`
- `phi3`
- `llama3.1:3b`

Make sure they exist locally:

```powershell
ollama list
ollama pull llama3.1:8b
ollama pull mistral
ollama pull gemma:7b
ollama pull phi3
ollama pull llama3.1:3b
```

## Install

From repo root:

```powershell
python -m pip install -r requirements.txt
```

## Configure

All runtime configuration is in:

- `benchmarking_backend/config/settings.json`

Includes:

- DB connection
- energy/hardware assumptions
- benchmark defaults
- model defaults and token limits
- available model names

## Database Schema

Schema file:

- `create_prompt_benchmark_schema.sql`

The backend initializes schema at runtime and uses these main tables:

- `tasks`
- `prompt_strategies`
- `dataset_inputs`
- `models`
- `run_times`
- `experiment_runs`

## Run the App

From repo root:

```powershell
streamlit run UI/app.py
```

Then open the Streamlit URL (usually `http://localhost:8501`).

## UI Flow

1. Open **Experiment Setup**
2. Select task, strategy, and model
3. Choose existing dataset input or enter raw input
4. Set **Number of Runs** (`>= 1`)
5. Click **Run Experiment**
6. Review detailed metrics in **Results & Comparison**
7. View historical runs in **Recent Runs**

## Metrics Stored per Run

Stored in `experiment_runs`:

- `task_id`, `strategy_id`, `model_id`, `input_id`, `time_id`
- `input_prompt`, `output_text`
- `prompt_tokens`, `completion_tokens`, `total_tokens`
- `latency_ms`
- `throughput_tokens_per_sec`, `throughput_requests_per_sec`
- `energy_kwh`, `energy_cost`, `hardware_cost`
- `accuracy_percent`, `field_accuracy_percent`, `exact_record_match`, `schema_compliance_percent`, `quality_score`

## Troubleshooting

- **Backend connection failed** in UI:
  - Verify MySQL service is running
  - Verify `settings.json` DB credentials
  - Verify user has permission to create/use `prompt_benchmark`
- **Model execution failed**:
  - Verify Ollama is running
  - Verify model name exists in `ollama list`
- **No tasks/strategies in dropdowns**:
  - Re-run schema SQL manually if needed, or check DB table contents
