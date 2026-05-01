# Prompt Optimization Workbench

End-to-end Streamlit + Python backend system for benchmarking prompt strategies on local LLMs (Ollama) with experiment metrics stored in MySQL.

## What It Does

You can run experiments by selecting:

- **Task**: Sentiment Classification, Summarization, or Question Answering
- **Prompt Strategy**: Zero-Shot Baseline or Few-Shot Prompting
- **Model**: Local Ollama models (llama3.1:8b, mistral, gemma:7b, phi3, llama3.1:3b)
- **Dataset Input**: Upload CSV/JSON/PDF files or use existing test data
- **Number of Runs**: Multiple runs for statistical reliability

For each run, the system:

1. Builds the final prompt from strategy template + input + examples (for few-shot)
2. Executes the selected model with Ollama
3. Measures latency, token usage, throughput, and energy consumption
4. Computes evaluation metrics (accuracy for classification, ROUGE scores for summarization, quality scores for QA)
5. Stores complete run records in MySQL with full experiment tracking
6. Displays results with detailed metrics and comparisons

## Features

### Experiment Setup
- **Variant Management**: Create multiple prompt variants with different strategies, models, and prompts
- **Duplicate Variants**: Easily copy existing variants to test slight modifications
- **Few-Shot Support**: Add examples in natural text format that get automatically parsed
- **Custom Prompts**: Configure system prompts, instruction prompts, and context/examples
- **Expected Labels**: Specify ground truth labels for accuracy evaluation (required for Sentiment Classification)
- **Dynamic Field Labels**: Field names adapt based on selected task (e.g., "Text to Summarize" for summarization tasks)
- **Comprehensive Tooltips**: Helpful guidance provided for all input fields
- **Dataset Upload**: Support for CSV, JSON, JSONL, and PDF files
- **Execution Modes**: Mock estimation, limited cloud execution, or local execution

### Results & Comparison
- **Detailed Metrics**: Latency, throughput, energy cost, token usage
- **Task-Specific Evaluation**:
  - Classification: Accuracy percentage
  - Summarization: ROUGE-1, ROUGE-2, ROUGE-L, and quality scores
  - Question Answering: Quality scores based on correctness and grounding
- **Visual Comparisons**: Bar charts and summary cards
- **Export**: Download results as CSV
- **LLM Output Review**: Inspect actual model responses with expected vs predicted

### Recent Runs
- **Database Integration**: View all historical experiments
- **Search & Filter**: Find runs by task, strategy, or model
- **Re-run Analysis**: Load previous experiments for comparison

## Project Structure

```
prompt_optimization_new/
├── README.md                           # This file
├── requirements.txt                    # Python dependencies
├── create_prompt_benchmark_schema.sql  # MySQL database schema
├── test_input.csv                      # Sample test data
├── test_input.xlsx                     # Additional test data
├── .streamlit/                         # Streamlit configuration
│   └── style.css                       # Custom UI styling
├── benchmarking_backend/               # Python backend
│   ├── __init__.py
│   ├── main.py                         # CLI entry point
│   ├── api/                            # REST API endpoints
│   │   ├── __init__.py
│   │   ├── endpoints.py                # API handlers
│   ├── config/                         # Configuration management
│   │   ├── __init__.py
│   │   ├── loader.py                   # Config loading
│   │   └── settings.json               # Runtime configuration
│   ├── database/                       # Database layer
│   │   ├── __init__.py
│   │   ├── connection.py               # DB connection
│   │   ├── repository.py               # Data access layer
│   │   └── schema.py                   # Schema management
│   ├── evaluation/                     # Evaluation metrics
│   │   ├── __init__.py
│   │   ├── accuracy.py                 # Classification accuracy
│   │   ├── llm_judge_evaluator.py      # LLM-as-judge evaluation
│   │   ├── qa_evaluator.py             # Question answering
│   │   ├── record_comparison.py        # Record-level comparison
│   │   ├── schema_validation.py        # Schema validation
│   │   ├── summarization_evaluator.py  # ROUGE scores
│   │   ├── text_quality.py             # Text quality metrics
│   └── experiments/                    # Experiment orchestration
│       ├── __init__.py
│       ├── experiment_runner.py        # Main experiment logic
│       ├── metric_collection.py        # Performance metrics
│       ├── model_executor.py           # Ollama integration
│       └── prompt_builder.py           # Prompt construction
└── UI/                                 # Streamlit frontend
    ├── __init__.py
    ├── app.py                          # Main app entry point
    ├── Navigation.py                   # Navigation utilities
    ├── ollama_exec.py                  # API client
    └── pages/                          # Streamlit pages
        ├── Comparison.py               # Results comparison
        ├── Experiment_setup.py         # Experiment configuration
        └── Recent_runs.py              # Historical runs browser
```

## Required Services

### 1) MySQL Database

The app requires MySQL for storing experiments, results, and metadata.

**Default Connection Settings** (in `benchmarking_backend/config/settings.json`):
- Host: `localhost`
- Port: `3306`
- User: `root`
- Password: ``
- Database: `prompt_benchmark`

**Setup MySQL:**
```bash
# Install MySQL if not already installed
# Start MySQL service
mysql -u root -p < create_prompt_benchmark_schema.sql
```

### 2) Ollama with Models

Requires Ollama running locally with supported models.

**Supported Models:**
- `llama3.1:8b` (recommended for best performance)
- `mistral`
- `gemma:7b`
- `phi3`
- `llama3.1:3b`

**Setup Ollama:**
```bash
# Install Ollama if not already installed
ollama serve &

# Pull required models
ollama pull llama3.1:8b
ollama pull mistral
ollama pull gemma:7b
ollama pull phi3
ollama pull llama3.1:3b

# Verify installation
ollama list
```

## Installation

### Prerequisites
- Python 3.8+
- MySQL 8.0+
- Ollama with required models

### Install Dependencies
```bash
# Clone the repository
git clone <repository-url>
cd prompt_optimization_new

# Install Python packages
pip install -r requirements.txt
```

## Configuration

All runtime configuration is in `benchmarking_backend/config/settings.json`:

### Database Settings
```json
{
  "database": {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",
    "name": "prompt_benchmark"
  }
}
```

### Energy & Hardware Assumptions
```json
{
  "energy": {
    "gpu_power_watts": 250.0,
    "cpu_power_watts": 65.0,
    "energy_cost_per_kwh": 0.12,
    "hardware_hourly_cost": 1.5,
    "carbon_kg_per_kwh": 0.4
  }
}
```

### Benchmark Defaults
```json
{
  "benchmark": {
    "repetition_count": 3,
    "default_batch_size": 1
  }
}
```

## Usage

### Start the Application
```bash
streamlit run UI/app.py
```

This opens the web interface at `http://localhost:8501`

### Basic Workflow

1. **Setup Experiment**:
   - Select a task (Sentiment Classification, Summarization, or Question Answering) - tooltips guide your choice
   - **For Sentiment Classification**: Specify the expected sentiment label (positive/negative/neutral) for accuracy evaluation
   - Choose a prompt strategy (Zero-Shot or Few-Shot) with helpful explanations
   - Pick a model from available Ollama models
   - Configure task-specific prompts (field labels adapt to your selected task)
   - Upload dataset or use existing test data
   - Set number of runs for statistical reliability

2. **Run Experiment**:
   - Click "▷ Run Experiment"
   - Monitor progress in the spinner
   - Results automatically load in the comparison page

3. **Analyze Results**:
   - View summary metrics and charts
   - Compare different prompt variants
   - Review actual LLM outputs
   - Export results as CSV

4. **Browse History**:
   - Use "Recent Runs" to view past experiments
   - Search and filter historical data
   - Re-analyze previous experiments

## Supported Tasks

### 1. Sentiment Classification
- **Input**: Text to classify
- **Output**: positive/negative/neutral
- **Evaluation**: Accuracy percentage

### 2. Summarization
- **Input**: Long text to summarize
- **Output**: Concise summary
- **Evaluation**: ROUGE scores (ROUGE-1, ROUGE-2, ROUGE-L) and quality score

### 3. Question Answering
- **Input**: Context + Question
- **Output**: Answer based only on context
- **Evaluation**: Quality score (correctness, completeness, grounding)

## Metrics Collected

### Performance Metrics
- **Latency**: End-to-end response time (ms)
- **Throughput**: Tokens per second and requests per second
- **Token Usage**: Prompt tokens, completion tokens, total tokens

### Cost Metrics
- **Energy Consumption**: kWh used during inference
- **Energy Cost**: Dollar cost of energy consumption
- **Hardware Cost**: Hourly hardware rental cost

### Quality Metrics (Task-Specific)
- **Accuracy**: For classification tasks
- **ROUGE Scores**: For summarization (ROUGE-1, ROUGE-2, ROUGE-L)
- **Quality Score**: LLM-as-judge evaluation for summarization and QA

## Database Schema

The system uses these main tables:

- **`tasks`**: Available tasks (classification, summarization, QA)
- **`prompt_strategies`**: Strategy templates (zero-shot, few-shot)
- **`dataset_inputs`**: Test inputs with expected outputs
- **`models`**: Available Ollama models
- **`run_times`**: Timestamp tracking
- **`experiment_runs`**: Complete experiment results with all metrics

## Development

### Adding New Tasks
1. Add task definition to `create_prompt_benchmark_schema.sql`
2. Implement evaluation logic in `benchmarking_backend/evaluation/`
3. Update task metrics mapping in `UI/pages/Comparison.py`

### Adding New Models
1. Pull model in Ollama: `ollama pull <model-name>`
2. Add to database: `INSERT INTO models (model_name) VALUES ('<model-name>');`

### Custom Configuration
Modify `benchmarking_backend/config/settings.json` for:
- Energy costs and hardware assumptions
- Default benchmark parameters
- Database connection settings

## Troubleshooting

### Common Issues

**"ModuleNotFoundError"**
```bash
pip install -r requirements.txt
```

**"Connection refused" (Database)**
- Ensure MySQL is running
- Check connection settings in `settings.json`
- Verify database exists: `CREATE DATABASE prompt_benchmark;`

**"Model not found" (Ollama)**
```bash
ollama pull <model-name>
ollama list
```

**"Expected sentiment label is required"**
- For Sentiment Classification tasks, you must specify the expected label (positive/negative/neutral)
- This is required for accuracy evaluation - select the correct ground truth label from the dropdown

**"No context found" (Few-shot)**
- Ensure examples are properly formatted in the Context/Examples field
- Use format: "Example 1: Input: [text] Output: [expected]"

**Streamlit errors**
- Clear cache: `streamlit cache clear`
- Restart: `streamlit run UI/app.py`

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
