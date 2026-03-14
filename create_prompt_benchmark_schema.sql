CREATE DATABASE IF NOT EXISTS prompt_benchmark;
USE prompt_benchmark;

CREATE TABLE IF NOT EXISTS tasks (
    task_id INT AUTO_INCREMENT PRIMARY KEY,
    task_name VARCHAR(255) NOT NULL,
    task_description TEXT,
    expected_output TEXT,
    UNIQUE KEY uq_tasks_name (task_name)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS prompt_strategies (
    strategy_id INT AUTO_INCREMENT PRIMARY KEY,
    strategy_name VARCHAR(255) NOT NULL,
    strategy_type VARCHAR(100) NOT NULL,
    strategy_template TEXT NOT NULL,
    description TEXT,
    UNIQUE KEY uq_prompt_strategies_name (strategy_name),
    KEY idx_prompt_strategies_type (strategy_type)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS dataset_inputs (
    input_id INT AUTO_INCREMENT PRIMARY KEY,
    input_text MEDIUMTEXT NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS models (
    model_id INT AUTO_INCREMENT PRIMARY KEY,
    model_name VARCHAR(255) NOT NULL,
    UNIQUE KEY uq_models_name (model_name)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS run_times (
    time_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    run_date DATE NOT NULL,
    run_time TIME NOT NULL,
    UNIQUE KEY uq_run_times_datetime (run_date, run_time),
    KEY idx_run_times_date (run_date)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS experiment_runs (
    run_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    task_id INT NOT NULL,
    strategy_id INT NOT NULL,
    model_id INT NOT NULL,
    input_id INT NOT NULL,
    time_id BIGINT NOT NULL,
    experiment_run_id VARCHAR(36) NULL, 

    input_prompt MEDIUMTEXT NOT NULL,

    prompt_tokens INT NOT NULL,
    completion_tokens INT NOT NULL,
    total_tokens INT NOT NULL,

    latency_ms DECIMAL(12,3) NOT NULL,
    throughput_tokens_per_sec DECIMAL(14,6) NOT NULL,
    throughput_requests_per_sec DECIMAL(14,6) NOT NULL,

    energy_kwh DECIMAL(14,10) NOT NULL,
    energy_cost DECIMAL(12,6) NOT NULL,
    hardware_cost DECIMAL(12,6) NOT NULL,

    accuracy_percent DECIMAL(8,4) NOT NULL,
    field_accuracy_percent DECIMAL(8,4) NOT NULL,
    exact_record_match TINYINT(1) NOT NULL,
    schema_compliance_percent DECIMAL(8,4) NOT NULL,

    quality_score DECIMAL(8,4) NOT NULL,
    output_text MEDIUMTEXT,

    CONSTRAINT fk_experiment_runs_task
        FOREIGN KEY (task_id) REFERENCES tasks(task_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_experiment_runs_strategy
        FOREIGN KEY (strategy_id) REFERENCES prompt_strategies(strategy_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_experiment_runs_model
        FOREIGN KEY (model_id) REFERENCES models(model_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_experiment_runs_input
        FOREIGN KEY (input_id) REFERENCES dataset_inputs(input_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_experiment_runs_time
        FOREIGN KEY (time_id) REFERENCES run_times(time_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE INDEX idx_experiment_runs_task_id ON experiment_runs(task_id);
CREATE INDEX idx_experiment_runs_strategy_id ON experiment_runs(strategy_id);
CREATE INDEX idx_experiment_runs_model_id ON experiment_runs(model_id);
CREATE INDEX idx_experiment_runs_input_id ON experiment_runs(input_id);
CREATE INDEX idx_experiment_runs_time_id ON experiment_runs(time_id);
CREATE INDEX idx_experiment_runs_quality_score ON experiment_runs(quality_score);
CREATE INDEX idx_experiment_runs_accuracy_percent ON experiment_runs(accuracy_percent);
CREATE INDEX idx_experiment_runs_experiment_run_id ON experiment_runs(experiment_run_id);

INSERT INTO tasks (task_name, task_description, expected_output) VALUES
    ('Summarization', 'Summarize the given text.', NULL),
    ('Question Answering', 'Answer the user question.', NULL),
    ('Classification', 'Classify the input into a category.', NULL),
    ('Structured Extraction', 'Extract structured fields from unstructured text.', NULL),
    ('Reasoning', 'Solve the task with explicit reasoning.', NULL)
ON DUPLICATE KEY UPDATE task_name = VALUES(task_name);

INSERT INTO prompt_strategies (strategy_name, strategy_type, strategy_template, description) VALUES
    (
        'Zero-Shot Baseline',
        'zero-shot',
        'Task: {task_name}\nTask Description: {task_description}\nInput: {input_text}\nOutput:',
        'Direct zero-shot instruction without examples.'
    ),
    (
        'Few-Shot Prompting',
        'few-shot',
        'Task: {task_name}\nTask Description: {task_description}\n{examples}\nInput: {input_text}\nOutput:',
        'Prompt with examples before answering.'
    ),
    (
        'Chain-of-Thought',
        'reasoning',
        'Task: {task_name}\nTask Description: {task_description}\nInput: {input_text}\nThink step by step and then answer.\nOutput:',
        'Encourage stepwise reasoning.'
    )
ON DUPLICATE KEY UPDATE strategy_name = VALUES(strategy_name);

INSERT INTO models (model_name) VALUES
    ('llama3.1:8b'),
    ('mistral'),
    ('gemma:7b'),
    ('phi3'),
    ('llama3.1:3b')
ON DUPLICATE KEY UPDATE model_name = VALUES(model_name);
