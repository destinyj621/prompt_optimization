CREATE DATABASE IF NOT EXISTS prompt_benchmark;
USE prompt_benchmark;

CREATE TABLE IF NOT EXISTS tasks (
    task_id INT AUTO_INCREMENT PRIMARY KEY,
    task_name VARCHAR(255) NOT NULL,
    task_description TEXT,
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
    dataset_name VARCHAR(255) NOT NULL DEFAULT 'default_dataset',
    input_text MEDIUMTEXT NOT NULL,
    expected_label VARCHAR(50) NOT NULL DEFAULT '',
    UNIQUE KEY uq_dataset_entry (dataset_name, input_text(255))
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

    predicted_label VARCHAR(50) NULL,
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

INSERT IGNORE INTO tasks (task_name, task_description) VALUES
('Sentiment Classification', 'Classify text sentiment as positive, negative, or neutral.');

INSERT IGNORE INTO prompt_strategies (strategy_name, strategy_type, strategy_template, description) VALUES
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
);

INSERT IGNORE INTO models (model_name) VALUES
('llama3.1:8b'),
('mistral'),
('gemma:7b'),
('phi3'),
('llama3.1:3b');

INSERT IGNORE INTO dataset_inputs (dataset_name, input_text, expected_label) VALUES
('sentiment_test','I absolutely love this product.', 'positive'),
('sentiment_test','This is the worst purchase I have made.', 'negative'),
('sentiment_test','The movie was okay, nothing special.', 'neutral'),
('sentiment_test','Customer service was excellent.', 'positive'),
('sentiment_test','The app crashes constantly.', 'negative');