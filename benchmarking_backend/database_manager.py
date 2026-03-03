# Database management module for MySQL interactions in the benchmarking workflow
from typing import Any, Dict, List, Optional

import mysql.connector
from mysql.connector import Error
from mysql.connector.connection import MySQLConnection

from config.config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER


def get_connection() -> Optional[MySQLConnection]:
    """Creates and returns a MySQL connection."""
    print("Connecting to MySQL database...")
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
        )
        return conn
    except Error as e:
        print("Database connection failed:", e)
        return None


class DatabaseManager:
    """Handles all MySQL operations used by the benchmarking workflow."""

    def __init__(self) -> None:
        self.connection: Optional[MySQLConnection] = None
        self._experiment_run_columns: Optional[set[str]] = None

    def connect_to_mysql(self) -> None:
        if self.connection and self.connection.is_connected():
            return

        self.connection = get_connection()
        if not self.connection:
            raise ConnectionError("Unable to connect to MySQL. Check local DB credentials/settings.")

    def close(self) -> None:
        if self.connection and self.connection.is_connected():
            self.connection.close()

    def _ensure_connection(self) -> None:
        if not self.connection or not self.connection.is_connected():
            self.connect_to_mysql()

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
            "SELECT strategy_id, strategy_name, strategy_type, description "
            "FROM prompt_strategies ORDER BY strategy_id",
            (),
        )

    def get_strategy(self, strategy_id: int) -> Optional[Dict[str, Any]]:
        return self._fetch_one(
            "SELECT strategy_id, strategy_name, strategy_type, description "
            "FROM prompt_strategies WHERE strategy_id = %s",
            (strategy_id,),
        )

    def list_models(self) -> List[Dict[str, Any]]:
        return self._fetch_all("SELECT model_id, model_name FROM models ORDER BY model_id", ())

    def get_model(self, model_id: int) -> Optional[Dict[str, Any]]:
        return self._fetch_one(
            "SELECT model_id, model_name FROM models WHERE model_id = %s",
            (model_id,),
        )

    def get_inputs_for_task(self, task_id: int) -> List[Dict[str, Any]]:
        return self._fetch_all(
            "SELECT input_id, task_id, input_text FROM dataset_inputs WHERE task_id = %s ORDER BY input_id",
            (task_id,),
        )

    def get_dataset_input(self, input_id: int) -> Optional[Dict[str, Any]]:
        return self._fetch_one(
            "SELECT input_id, task_id, input_text FROM dataset_inputs WHERE input_id = %s",
            (input_id,),
        )

    def insert_dataset_input(self, task_id: int, input_text: str) -> int:
        """Inserts a user-provided input prompt and returns the new input_id."""
        self._ensure_connection()
        assert self.connection is not None

        cursor = self.connection.cursor()
        cursor.execute(
            "INSERT INTO dataset_inputs (task_id, input_text) VALUES (%s, %s)",
            (task_id, input_text),
        )
        self.connection.commit()
        input_id = int(cursor.lastrowid)
        cursor.close()
        return input_id

    def get_strategy_examples(self, strategy_id: int, task_id: int) -> List[Dict[str, Any]]:
        """Returns few-shot examples if strategy_examples table exists; otherwise empty list."""
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

    def _get_experiment_run_columns(self) -> set[str]:
        if self._experiment_run_columns is not None:
            return self._experiment_run_columns

        self._ensure_connection()
        assert self.connection is not None
        cursor = self.connection.cursor()
        cursor.execute("SHOW COLUMNS FROM experiment_runs")
        rows = cursor.fetchall()
        cursor.close()
        self._experiment_run_columns = {row[0] for row in rows}
        return self._experiment_run_columns

    def insert_experiment_run(self, data_dict: Dict[str, Any]) -> None:
        self._ensure_connection()
        assert self.connection is not None

        available_columns = self._get_experiment_run_columns()
        insert_data = {key: value for key, value in data_dict.items() if key in available_columns}

        if not insert_data:
            raise ValueError("No matching columns found for experiment_runs insert.")

        columns = list(insert_data.keys())
        placeholders = ["%s"] * len(columns)
        values = [insert_data[column] for column in columns]

        query = (
            f"INSERT INTO experiment_runs ({', '.join(columns)}) "
            f"VALUES ({', '.join(placeholders)})"
        )

        cursor = self.connection.cursor()
        cursor.execute(query, values)
        self.connection.commit()
        cursor.close()
