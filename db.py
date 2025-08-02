"""
db.py

Handles all database operations for the StoryKeeper application.
"""

import sqlite3
from typing import List, Tuple, Dict, Any


class DictionaryDB:
    """Encapsulates database interactions for dictionary and context management."""

    def __init__(self, db_file: str = "storykeeper_dictionary.db") -> None:
        """
        Initialize the database connection and create required tables.

        Args:
            db_file (str): Path to the SQLite database file.
        """
        self.conn = sqlite3.connect(db_file)
        self._create_tables()
        self._migrate_schema()
        self._prepopulate_contexts()

    def _create_tables(self) -> None:
        """Create the necessary tables if they don't exist."""
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS dictionary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT,
                    category TEXT,
                    part_of_speech TEXT,
                    definition TEXT,
                    context_hint TEXT,
                    sense_number INTEGER DEFAULT 1,
                    UNIQUE(word, category, part_of_speech, sense_number)
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS contexts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

    def _migrate_schema(self) -> None:
        """Add missing columns if they don't already exist."""
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(dictionary)")
        existing_cols = {col[1] for col in cursor.fetchall()}
        required_cols = {
            "category": "TEXT DEFAULT 'General'",
            "context_hint": "TEXT DEFAULT ''",
            "sense_number": "INTEGER DEFAULT 1"
        }
        for col, definition in required_cols.items():
            if col not in existing_cols:
                self.conn.execute(f"ALTER TABLE dictionary ADD COLUMN {col} {definition}")
        self.conn.commit()

    def _prepopulate_contexts(self) -> None:
        """Populate default context values if they don't exist."""
        defaults = [
            "Species", "Planet", "Language", "Culture", "Artifact",
            "Event", "Location", "Organization", "Concept", "Adjective (race-like)"
        ]
        with self.conn:
            for ctx in defaults:
                self.conn.execute("INSERT OR IGNORE INTO contexts (name) VALUES (?)", (ctx,))

    # ---------------- CRUD Methods ---------------- #

    def add_entry(self, word: str, category: str, pos: str, definition: str,
                  context: str, sense_number: int = 1) -> None:
        """Add or update a single dictionary entry with a specific meaning."""
        with self.conn:
            self.conn.execute("""
                INSERT OR REPLACE INTO dictionary
                (word, category, part_of_speech, definition, context_hint, sense_number)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (word.lower(), category, pos, definition, context, sense_number))

    def add_multiple_entries(self, word: str, category: str,
                             entries: List[Tuple[str, str, str, int]]) -> None:
        """Add multiple meanings for a word."""
        with self.conn:
            for pos, definition, context, sense_number in entries:
                self.conn.execute("""
                    INSERT OR REPLACE INTO dictionary
                    (word, category, part_of_speech, definition, context_hint, sense_number)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (word.lower(), category, pos, definition, context, sense_number))

    def delete_entry(self, word: str, sense_number: int = None) -> None:
        """Delete a word or a specific meaning from the dictionary."""
        with self.conn:
            if sense_number is not None:
                self.conn.execute("DELETE FROM dictionary WHERE word = ? AND sense_number = ?",
                                  (word.lower(), sense_number))
            else:
                self.conn.execute("DELETE FROM dictionary WHERE word = ?", (word.lower(),))

    def get_all_entries(self) -> List[Tuple[str, str, str, str, str, int]]:
        """Fetch all dictionary entries with meanings."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT word, category, part_of_speech, definition, context_hint, sense_number
            FROM dictionary
            ORDER BY word, sense_number
        """)
        return cursor.fetchall()

    def get_words_list(self) -> List[str]:
        """Get a list of all distinct words."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT word FROM dictionary")
        return [row[0] for row in cursor.fetchall()]

    def get_contexts(self) -> List[str]:
        """Get all contexts."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM contexts ORDER BY name")
        return [row[0] for row in cursor.fetchall()]

    def add_context(self, name: str) -> None:
        """Add a new context."""
        with self.conn:
            self.conn.execute("INSERT OR IGNORE INTO contexts (name) VALUES (?)", (name,))

    def delete_context(self, name: str) -> None:
        """Delete a context."""
        with self.conn:
            self.conn.execute("DELETE FROM contexts WHERE name = ?", (name,))

    def rename_context(self, old_name: str, new_name: str) -> None:
        """Rename a context."""
        with self.conn:
            self.conn.execute("UPDATE contexts SET name = ? WHERE name = ?", (new_name, old_name))

    def get_setting(self, key: str, default: str = "false") -> str:
        """Retrieve a setting value."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else default

    def set_setting(self, key: str, value: str) -> None:
        """Update or insert a setting."""
        with self.conn:
            self.conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))

    # ---------------- Export / Import ---------------- #

    def export_dictionary(self) -> List[Dict[str, Any]]:
        """Export the dictionary as a list of dicts."""
        data = []
        for row in self.get_all_entries():
            data.append({
                "word": row[0],
                "category": row[1],
                "part_of_speech": row[2],
                "definition": row[3],
                "context_hint": row[4],
                "sense_number": row[5]
            })
        return data

    def export_contexts(self) -> List[Dict[str, str]]:
        """Export contexts."""
        return [{"name": ctx} for ctx in self.get_contexts()]

    def import_dictionary(self, data: List[Dict[str, Any]], mode: str = "merge") -> None:
        """Import dictionary data."""
        with self.conn:
            if mode == "replace":
                self.conn.execute("DELETE FROM dictionary")
            for entry in data:
                self.conn.execute("""
                    INSERT OR REPLACE INTO dictionary
                    (word, category, part_of_speech, definition, context_hint, sense_number)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (entry["word"], entry["category"], entry["part_of_speech"],
                     entry["definition"], entry["context_hint"], entry.get("sense_number", 1))
                )

    def import_contexts(self, data: List[Dict[str, str]], mode: str = "merge") -> None:
        """Import contexts data."""
        with self.conn:
            if mode == "replace":
                self.conn.execute("DELETE FROM contexts")
            for entry in data:
                self.conn.execute("INSERT OR IGNORE INTO contexts (name) VALUES (?)", (entry["name"],))
