"""Global configuration constants for benchmarking backend."""

# Sustainability and environmental assumptions
ELECTRICITY_COST_PER_KWH = 0.12
CARBON_KG_PER_KWH = 0.4

# Hardware power assumptions
GPU_POWER_WATTS = 250.0
CPU_POWER_WATTS = 65.0

# Model generation defaults
DEFAULT_TEMPERATURE = 0.2
DEFAULT_TOP_P = 0.9
DEFAULT_MAX_TOKENS = 256

# Ollama settings
OLLAMA_BASE_URL = "http://localhost:11434"

# MySQL connection defaults
DB_HOST = "localhost"
DB_PORT = 3306
DB_USER = "root"
DB_PASSWORD = ""
DB_NAME = "prompt_benchmark"

# Example requirements for prompting
EXAMPLE_REQUIRED_TASK_KEYWORDS = (
    "structured extraction",
    "classification",
    "reasoning",
)
EXAMPLE_REQUIRED_STRATEGY_TYPES = (
    "few-shot",
    "format constrained",
    "format-constrained",
    "structured",
)

# Central example library used when a task/strategy requires examples.
# Keys are normalized strategy_type values or task keywords.
EXAMPLE_LIBRARY = {
    "few-shot": [
        {
            "example_input": "Text: Climate change is accelerating due to emissions.",
            "example_output": "Summary: Climate change is worsening because of emissions.",
            "example_order": 1,
        },
        {
            "example_input": "Text: Recycling reduces landfill waste and saves energy.",
            "example_output": "Summary: Recycling lowers waste and conserves energy.",
            "example_order": 2,
        },
    ],
    "format constrained": [
        {
            "example_input": "Review: The phone is fast but battery is average.",
            "example_output": '{"sentiment":"neutral","pros":["fast"],"cons":["average battery"]}',
            "example_order": 1,
        }
    ],
    "structured extraction": [
        {
            "example_input": "Patient: John Doe, age 45, diagnosed with hypertension.",
            "example_output": '{"name":"John Doe","age":45,"diagnosis":"hypertension"}',
            "example_order": 1,
        }
    ],
    "classification": [
        {
            "example_input": "Email: You won a free prize! Click now!",
            "example_output": "Label: spam",
            "example_order": 1,
        },
        {
            "example_input": "Email: Team meeting moved to 3 PM.",
            "example_output": "Label: not_spam",
            "example_order": 2,
        },
    ],
    "reasoning": [
        {
            "example_input": "If all A are B and all B are C, are all A C?",
            "example_output": "Yes. Since A subset B and B subset C, A subset C.",
            "example_order": 1,
        }
    ],
}
