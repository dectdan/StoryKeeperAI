"""
test_db.py

Unit tests for the DictionaryDB class using pytest.
Ensures multi-meaning (sense_number) support works as expected.
"""

import pytest
from db import DictionaryDB


@pytest.fixture
def db() -> DictionaryDB:
    """Fixture to create a temporary in-memory database."""
    return DictionaryDB(":memory:")


def test_create_tables(db: DictionaryDB):
    """Test that required tables exist."""
    cursor = db.conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    assert "dictionary" in tables
    assert "contexts" in tables
    assert "settings" in tables


def test_add_and_get_single_entry(db: DictionaryDB):
    """Test adding and retrieving a single entry."""
    db.add_entry("kaneran", "Species", "Noun", "An alien species.", "Sci-fi context", 1)
    entries = db.get_all_entries()
    assert len(entries) == 1
    word, category, pos, definition, context, sense = entries[0]
    assert word == "kaneran"
    assert category == "Species"
    assert pos == "Noun"
    assert definition == "An alien species."
    assert context == "Sci-fi context"
    assert sense == 1


def test_add_multiple_meanings(db: DictionaryDB):
    """Test adding multiple meanings for the same word and part of speech."""
    entries = [
        ("Noun", "First meaning.", "Context A", 1),
        ("Noun", "Second meaning.", "Context B", 2),
    ]
    db.add_multiple_entries("kaneran", "Species", entries)
    results = db.get_all_entries()
    assert len(results) == 2
    senses = sorted([row[5] for row in results])
    assert senses == [1, 2]


def test_delete_specific_meaning(db: DictionaryDB):
    """Test deleting a specific meaning by sense_number."""
    entries = [
        ("Noun", "First meaning.", "Context A", 1),
        ("Noun", "Second meaning.", "Context B", 2),
    ]
    db.add_multiple_entries("kaneran", "Species", entries)
    db.delete_entry("kaneran", sense_number=1)
    results = db.get_all_entries()
    assert len(results) == 1
    assert results[0][5] == 2  # Remaining sense number


def test_delete_all_meanings(db: DictionaryDB):
    """Test deleting all meanings of a word."""
    entries = [
        ("Noun", "First meaning.", "Context A", 1),
        ("Noun", "Second meaning.", "Context B", 2),
    ]
    db.add_multiple_entries("kaneran", "Species", entries)
    db.delete_entry("kaneran")
    results = db.get_all_entries()
    assert len(results) == 0


def test_contexts_management(db: DictionaryDB):
    """Test adding, renaming, and deleting contexts."""
    db.add_context("Galaxy")
    contexts = db.get_contexts()
    assert "Galaxy" in contexts

    db.rename_context("Galaxy", "Universe")
    contexts = db.get_contexts()
    assert "Universe" in contexts
    assert "Galaxy" not in contexts

    db.delete_context("Universe")
    contexts = db.get_contexts()
    assert "Universe" not in contexts


def test_export_and_import_dictionary(db: DictionaryDB):
    """Test exporting and importing dictionary data."""
    entries = [
        ("Noun", "First meaning.", "Context A", 1),
        ("Noun", "Second meaning.", "Context B", 2),
    ]
    db.add_multiple_entries("kaneran", "Species", entries)
    exported = db.export_dictionary()

    new_db = DictionaryDB(":memory:")
    new_db.import_dictionary(exported, mode="merge")
    results = new_db.get_all_entries()
    assert len(results) == 2
