import pytest
from managers import ContextManager, DictionaryManager
from db import DictionaryDB
from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def db():
    return DictionaryDB(":memory:")


def test_context_manager_add_edit_delete(app, qtbot, db):
    cm = ContextManager(db)
    qtbot.addWidget(cm)

    db.add_context("Original")
    cm.refresh_list()
    assert "Original" in db.get_contexts()

    db.rename_context("Original", "Updated")
    cm.refresh_list()
    assert "Updated" in db.get_contexts()

    db.delete_context("Updated")
    cm.refresh_list()
    assert "Updated" not in db.get_contexts()

    cm.close()


def test_dictionary_manager_display_entries(app, qtbot, db):
    entries = [
        ("Noun", "Meaning A", "Ctx A", 1),
        ("Noun", "Meaning B", "Ctx B", 2),
    ]
    db.add_multiple_entries("kaneran", "Species", entries)

    dm = DictionaryManager(db)
    qtbot.addWidget(dm)
    dm.refresh_word_list()

    items = [dm.word_list.item(i).text() for i in range(dm.word_list.count())]
    assert any("Meaning A" in item for item in items)
    assert any("Meaning B" in item for item in items)

    dm.close()
