CREATE DATABASE IF NOT EXISTS prompt_benchmark;
USE prompt_benchmark;

CREATE TABLE IF NOT EXISTS tasks (
    task_id INT AUTO_INCREMENT PRIMARY KEY,
    task_name VARCHAR(255) NOT NULL,
    task_description TEXT NOT NULL,
    expected_output TEXT NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS prompt_strategies (
    strategy_id INT AUTO_INCREMENT PRIMARY KEY,
    strategy_name VARCHAR(255) NOT NULL,
    strategy_type VARCHAR(100) NOT NULL,
    description TEXT
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS models (
    model_id INT AUTO_INCREMENT PRIMARY KEY,
    model_name VARCHAR(255) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS dataset_inputs (
    input_id INT AUTO_INCREMENT PRIMARY KEY,
    task_id INT NOT NULL,
    input_text TEXT NOT NULL,
    CONSTRAINT fk_dataset_inputs_task
        FOREIGN KEY (task_id) REFERENCES tasks(task_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS experiment_runs (
    run_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    task_id INT NOT NULL,
    strategy_id INT NOT NULL,
    model_id INT NOT NULL,
    input_id INT NOT NULL,

    model_name VARCHAR(255) NULL,
    temperature DECIMAL(6,4) NULL,
    top_p DECIMAL(6,4) NULL,
    max_tokens INT NULL,
    hardware_environment VARCHAR(500) NULL,

    run_date DATE NOT NULL,
    run_time TIME NOT NULL,

    prompt_tokens INT NOT NULL,
    completion_tokens INT NOT NULL,
    total_tokens INT NOT NULL,

    estimated_cost DECIMAL(12,6) DEFAULT 0,
    latency_ms DECIMAL(12,3) NOT NULL,
    quality_score DECIMAL(8,4) DEFAULT 0,
    energy_kwh DECIMAL(14,10) DEFAULT 0,

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
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE INDEX idx_dataset_inputs_task_id ON dataset_inputs(task_id);
CREATE INDEX idx_experiment_runs_task_id ON experiment_runs(task_id);
CREATE INDEX idx_experiment_runs_strategy_id ON experiment_runs(strategy_id);
CREATE INDEX idx_experiment_runs_model_id ON experiment_runs(model_id);
CREATE INDEX idx_experiment_runs_input_id ON experiment_runs(input_id);
CREATE INDEX idx_experiment_runs_run_date ON experiment_runs(run_date);

INSERT INTO models (model_name) VALUES
    ('llama3.1:8b'),
    ('mistral'),
    ('mixtral'),
    ('gemma'),
    ('phi3')
ON DUPLICATE KEY UPDATE model_name = VALUES(model_name);
