"""Database module for the distributed key-value system.

This module handles persistent storage of table data using JSON files.
It provides thread-safe access to the data.
"""

import json
import os
import threading
from typing import Dict, Tuple

class Database:
    """Manages table data with thread-safe operations.

    Attributes:
        data_file (str): Path to the JSON file.
        lock (threading.Lock): Mutex for thread-safe access.
        tables (Dict): In-memory cache of table data.
    """

    def __init__(self, data_file: str = 'data/tables.json'):
        """Initializes the Database with a file path and loads data.

        Args:
            data_file: Path to the JSON file storing tables.
                Defaults to 'data/tables.json'.
        """
        self.data_file = data_file
        self.lock = threading.Lock()
        self._load_data()

    def _load_data(self) -> None:
        """Loads data from the JSON file into memory.

        Creates an empty file if it does not exist.
        """
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)

        if not os.path.exists(self.data_file):
            self.tables: Dict[str, Dict[str, str]] = {}
            self._save_data()
        else:
            with open(self.data_file, 'r') as f:
                self.tables = json.load(f)

    def _save_data(self) -> None:
        """Saves current table data to the JSON file."""
        with open(self.data_file, 'w') as f:
            json.dump(self.tables, f, indent=4)

    def put(self, table: str, key: str, value: str) -> Tuple[bool, str]:
        """Inserts or updates a key-value pair in a table."""
        with self.lock:
            if table not in self.tables:
                self.tables[table] = {}
            exists = key in self.tables[table]
            self.tables[table][key] = value
            self._save_data()
            return True, "updated" if exists else "inserted"

    def get(self, table: str, key: str) -> Tuple[bool, str]:
        """Retrieves a value for a key in a table."""
        with self.lock:
            if table not in self.tables:
                return False, "Table not found"
            if key not in self.tables[table]:
                return False, "Key not found"
            return True, self.tables[table][key]

    def delete(self, table: str, key: str) -> Tuple[bool, str]:
        """Deletes a key-value pair from a table."""
        with self.lock:
            if table not in self.tables:
                return False, "Table not found"
            if key not in self.tables[table]:
                return False, "Key not found"
            del self.tables[table][key]
            self._save_data()
            return True, "deleted"
