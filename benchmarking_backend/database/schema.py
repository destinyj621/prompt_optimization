"""Schema initialization and compatibility migration utilities."""

from __future__ import annotations

from pathlib import Path

from mysql.connector import Error
from mysql.connector.connection import MySQLConnection


def _split_sql_statements(sql_script: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    in_single = False
    in_double = False
    escape = False

    for char in sql_script:
        if escape:
            current.append(char)
            escape = False
            continue

        if char == "\\":
            current.append(char)
            escape = True
            continue

        if char == "'" and not in_double:
            in_single = not in_single
            current.append(char)
            continue

        if char == '"' and not in_single:
            in_double = not in_double
            current.append(char)
            continue

        if char == ";" and not in_single and not in_double:
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
            continue

        current.append(char)

    trailing = "".join(current).strip()
    if trailing:
        statements.append(trailing)
    return statements


def initialize_schema(connection: MySQLConnection, schema_path: Path | None = None) -> None:
    script_path = schema_path or (Path(__file__).resolve().parents[2] / "create_prompt_benchmark_schema.sql")
    sql_script = script_path.read_text(encoding="utf-8")
    cursor = connection.cursor()

    for statement in _split_sql_statements(sql_script):
        try:
            cursor.execute(statement)
        except Error as exc:
            # CREATE INDEX in MySQL has no IF NOT EXISTS in many environments.
            # Ignore duplicate index errors to keep schema initialization idempotent.
            if getattr(exc, "errno", None) == 1061:
                continue
            raise

    connection.commit()
    cursor.close()


def _column_exists(connection: MySQLConnection, table_name: str, column_name: str) -> bool:
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
          AND table_name = %s
          AND column_name = %s
        LIMIT 1
        """,
        (table_name, column_name),
    )
    exists = cursor.fetchone() is not None
    cursor.close()
    return exists


def _index_exists(connection: MySQLConnection, table_name: str, index_name: str) -> bool:
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT 1
        FROM information_schema.statistics
        WHERE table_schema = DATABASE()
          AND table_name = %s
          AND index_name = %s
        LIMIT 1
        """,
        (table_name, index_name),
    )
    exists = cursor.fetchone() is not None
    cursor.close()
    return exists


def ensure_schema_compat(connection: MySQLConnection) -> None:
    """Upgrades legacy schemas in-place to support the current backend."""
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS run_times (
            time_id BIGINT AUTO_INCREMENT PRIMARY KEY,
            run_date DATE NOT NULL,
            run_time TIME NOT NULL,
            UNIQUE KEY uq_run_times_datetime (run_date, run_time),
            KEY idx_run_times_date (run_date)
        ) ENGINE=InnoDB
        """
    )

    if not _column_exists(connection, "prompt_strategies", "strategy_template"):
        cursor.execute("ALTER TABLE prompt_strategies ADD COLUMN strategy_template TEXT NULL")
        cursor.execute(
            """
            UPDATE prompt_strategies
            SET strategy_template = CONCAT(
                'Task: {task_name}\\n',
                'Task Description: {task_description}\\n',
                'Strategy Instructions: ', COALESCE(description, ''), '\\n',
                '{examples}\\n',
                'Input: {input_text}\\n',
                'Output:'
            )
            WHERE strategy_template IS NULL OR strategy_template = ''
            """
        )

    required_experiment_columns = {
        "time_id": "BIGINT NULL",
        "input_prompt": "MEDIUMTEXT NULL",
        "throughput_tokens_per_sec": "DECIMAL(14,6) NULL",
        "throughput_requests_per_sec": "DECIMAL(14,6) NULL",
        "energy_cost": "DECIMAL(12,6) NULL",
        "hardware_cost": "DECIMAL(12,6) NULL",
        "accuracy_percent": "DECIMAL(8,4) NULL",
        "field_accuracy_percent": "DECIMAL(8,4) NULL",
        "exact_record_match": "TINYINT(1) NULL",
        "schema_compliance_percent": "DECIMAL(8,4) NULL",
    }
    for column_name, column_type in required_experiment_columns.items():
        if not _column_exists(connection, "experiment_runs", column_name):
            cursor.execute(f"ALTER TABLE experiment_runs ADD COLUMN {column_name} {column_type}")

    if _column_exists(connection, "experiment_runs", "run_date") and _column_exists(
        connection, "experiment_runs", "run_time"
    ):
        cursor.execute(
            """
            INSERT IGNORE INTO run_times (run_date, run_time)
            SELECT DISTINCT run_date, run_time
            FROM experiment_runs
            WHERE run_date IS NOT NULL AND run_time IS NOT NULL
            """
        )
        if _column_exists(connection, "experiment_runs", "time_id"):
            cursor.execute(
                """
                UPDATE experiment_runs er
                JOIN run_times rt
                  ON er.run_date = rt.run_date
                 AND er.run_time = rt.run_time
                SET er.time_id = rt.time_id
                WHERE er.time_id IS NULL
                """
            )

    required_indexes = {
        "idx_experiment_runs_time_id": "CREATE INDEX idx_experiment_runs_time_id ON experiment_runs(time_id)",
        "idx_experiment_runs_quality_score": "CREATE INDEX idx_experiment_runs_quality_score ON experiment_runs(quality_score)",
        "idx_experiment_runs_accuracy_percent": "CREATE INDEX idx_experiment_runs_accuracy_percent ON experiment_runs(accuracy_percent)",
    }
    for index_name, create_sql in required_indexes.items():
        if not _index_exists(connection, "experiment_runs", index_name):
            cursor.execute(create_sql)

    connection.commit()
    cursor.close()
