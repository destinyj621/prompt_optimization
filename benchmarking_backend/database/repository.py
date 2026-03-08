"""Repository for benchmark database operations."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from mysql.connector import Error
from mysql.connector.connection import MySQLConnection

from .connection import get_connection


class BenchmarkRepository:
    def __init__(self) -> None:
        self.connection: Optional[MySQLConnection] = None

    def connect(self) -> None:
        if self.connection and self.connection.is_connected():
            return
        self.connection = get_connection()
        if not self.connection:
            raise ConnectionError("Unable to connect to MySQL. Check config/settings.json.")

    def close(self) -> None:
        if self.connection and self.connection.is_connected():
            self.connection.close()

    def _ensure_connection(self) -> None:
        if not self.connection or not self.connection.is_connected():
            self.connect()

    def _fetch_one(self, query: str, params: tuple[Any, ...]) -> Optional[Dict[str, Any]]:
        self._ensure_connection()
        assert self.connection is not None
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(query, params)
        row = cursor.fetchone()
        cursor.close()
        return row

    def _fetch_all(self, query: str, params: tuple[Any, ...]) -> List[Dict[str, Any]]:
        self._ensure_connection()
        assert self.connection is not None
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def list_tasks(self) -> List[Dict[str, Any]]:
        return self._fetch_all("SELECT task_id, task_name FROM tasks ORDER BY task_id", ())

    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        return self._fetch_one(
            "SELECT task_id, task_name, task_description, expected_output FROM tasks WHERE task_id = %s",
            (task_id,),
        )

    def list_strategies(self) -> List[Dict[str, Any]]:
        return self._fetch_all(
            "SELECT strategy_id, strategy_name, strategy_type, strategy_template, description "
            "FROM prompt_strategies ORDER BY strategy_id",
            (),
        )

    def get_strategy(self, strategy_id: int) -> Optional[Dict[str, Any]]:
        return self._fetch_one(
            "SELECT strategy_id, strategy_name, strategy_type, strategy_template, description "
            "FROM prompt_strategies WHERE strategy_id = %s",
            (strategy_id,),
        )

    def list_models(self) -> List[Dict[str, Any]]:
        return self._fetch_all("SELECT model_id, model_name FROM models ORDER BY model_id", ())

    def get_model(self, model_id: int) -> Optional[Dict[str, Any]]:
        return self._fetch_one("SELECT model_id, model_name FROM models WHERE model_id = %s", (model_id,))

    def ensure_models(self, model_names: List[str]) -> None:
        self._ensure_connection()
        assert self.connection is not None
        if not model_names:
            return

        cursor = self.connection.cursor()
        cursor.executemany(
            "INSERT INTO models (model_name) VALUES (%s) ON DUPLICATE KEY UPDATE model_name = VALUES(model_name)",
            [(name,) for name in model_names],
        )
        self.connection.commit()
        cursor.close()

    def list_dataset_inputs(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        if limit is None:
            return self._fetch_all("SELECT input_id, input_text FROM dataset_inputs ORDER BY input_id", ())
        return self._fetch_all(
            "SELECT input_id, input_text FROM dataset_inputs ORDER BY input_id LIMIT %s",
            (limit,),
        )

    def get_dataset_input(self, input_id: int) -> Optional[Dict[str, Any]]:
        return self._fetch_one(
            "SELECT input_id, input_text FROM dataset_inputs WHERE input_id = %s",
            (input_id,),
        )

    def insert_dataset_input(self, input_text: str) -> int:
        self._ensure_connection()
        assert self.connection is not None

        cursor = self.connection.cursor()
        cursor.execute("INSERT INTO dataset_inputs (input_text) VALUES (%s)", (input_text,))
        self.connection.commit()
        input_id = int(cursor.lastrowid)
        cursor.close()
        return input_id

    def get_strategy_examples(self, strategy_id: int, task_id: int) -> List[Dict[str, Any]]:
        try:
            return self._fetch_all(
                "SELECT example_input, example_output, example_order "
                "FROM strategy_examples "
                "WHERE strategy_id = %s AND task_id = %s "
                "ORDER BY example_order",
                (strategy_id, task_id),
            )
        except Error:
            return []

    def get_or_create_run_time(self, run_dt: datetime) -> int:
        self._ensure_connection()
        assert self.connection is not None

        run_date = run_dt.date()
        run_time = run_dt.time().replace(microsecond=0)

        existing = self._fetch_one(
            "SELECT time_id FROM run_times WHERE run_date = %s AND run_time = %s",
            (run_date, run_time),
        )
        if existing:
            return int(existing["time_id"])

        cursor = self.connection.cursor()
        cursor.execute(
            "INSERT INTO run_times (run_date, run_time) VALUES (%s, %s)",
            (run_date, run_time),
        )
        self.connection.commit()
        time_id = int(cursor.lastrowid)
        cursor.close()
        return time_id

    def insert_experiment_run(self, run_data: Dict[str, Any]) -> int:
        self._ensure_connection()
        assert self.connection is not None

        columns = [
            "task_id",
            "strategy_id",
            "model_id",
            "input_id",
            "time_id",
            "input_prompt",
            "prompt_tokens",
            "completion_tokens",
            "total_tokens",
            "latency_ms",
            "throughput_tokens_per_sec",
            "throughput_requests_per_sec",
            "energy_kwh",
            "energy_cost",
            "hardware_cost",
            "accuracy_percent",
            "field_accuracy_percent",
            "exact_record_match",
            "schema_compliance_percent",
            "quality_score",
            "output_text",
        ]

        placeholders = ", ".join(["%s"] * len(columns))
        query = (
            f"INSERT INTO experiment_runs ({', '.join(columns)}) "
            f"VALUES ({placeholders})"
        )
        values = [run_data[column] for column in columns]

        cursor = self.connection.cursor()
        cursor.execute(query, values)
        self.connection.commit()
        run_id = int(cursor.lastrowid)
        cursor.close()
        return run_id

    def list_recent_runs(self, limit: int = 50) -> List[Dict[str, Any]]:
        safe_limit = max(1, int(limit))
        return self._fetch_all(
            """
            SELECT
                er.run_id,
                rt.run_date,
                rt.run_time,
                t.task_name,
                ps.strategy_name,
                m.model_name,
                er.latency_ms,
                er.prompt_tokens,
                er.completion_tokens,
                er.total_tokens,
                er.throughput_tokens_per_sec,
                er.throughput_requests_per_sec,
                er.energy_kwh,
                er.energy_cost,
                er.hardware_cost,
                er.accuracy_percent,
                er.field_accuracy_percent,
                er.exact_record_match,
                er.schema_compliance_percent,
                er.quality_score,
                er.input_prompt,
                er.output_text
            FROM experiment_runs er
            JOIN tasks t ON er.task_id = t.task_id
            JOIN prompt_strategies ps ON er.strategy_id = ps.strategy_id
            JOIN models m ON er.model_id = m.model_id
            JOIN run_times rt ON er.time_id = rt.time_id
            ORDER BY rt.run_date DESC, rt.run_time DESC, er.run_id DESC
            LIMIT %s
            """,
            (safe_limit,),
        )
