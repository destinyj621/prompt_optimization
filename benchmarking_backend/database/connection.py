"""MySQL connection helpers."""

from __future__ import annotations

from typing import Optional

import mysql.connector
from mysql.connector import Error
from mysql.connector.connection import MySQLConnection

from benchmarking_backend.config import CONFIG


def get_connection() -> Optional[MySQLConnection]:
    try:
        return mysql.connector.connect(
            host=CONFIG.database.host,
            port=CONFIG.database.port,
            user=CONFIG.database.user,
            password=CONFIG.database.password,
            database=CONFIG.database.name,
        )
    except Error:
        try:
            bootstrap = mysql.connector.connect(
                host=CONFIG.database.host,
                port=CONFIG.database.port,
                user=CONFIG.database.user,
                password=CONFIG.database.password,
            )
            cursor = bootstrap.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {CONFIG.database.name}")
            bootstrap.commit()
            cursor.close()
            bootstrap.close()
            return mysql.connector.connect(
                host=CONFIG.database.host,
                port=CONFIG.database.port,
                user=CONFIG.database.user,
                password=CONFIG.database.password,
                database=CONFIG.database.name,
            )
        except Error:
            return None
