#!/usr/bin/env python3
"""Initialize the database schema."""

import mysql.connector
from mysql.connector import Error

def init_database():
    try:
        # Read the SQL file
        with open("create_prompt_benchmark_schema.sql", "r") as f:
            sql_content = f.read()
        
        # Connect to MySQL
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""
        )
        
        cursor = conn.cursor()
        
        # Split by semicolon and execute each statement
        statements = sql_content.split(";")
        for statement in statements:
            statement = statement.strip()
            if statement:
                print(f"Executing: {statement[:60]}...")
                try:
                    cursor.execute(statement)
                except Error as e:
                    # Ignore duplicate index errors (1061) as they're expected on re-runs
                    if e.errno == 1061:
                        print(f"  (Index already exists, skipping)")
                    else:
                        raise
        
        conn.commit()
        print("✓ Database initialized successfully!")
        
        cursor.close()
        conn.close()
        
    except Error as err:
        print(f"Error: {err}")
        return False
    
    return True

if __name__ == "__main__":
    init_database()
