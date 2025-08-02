import pytest
from dialogs import MultiPOSDialog
from db import DictionaryDB
from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def app():
    """Single QApplication instance for all GUI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def db():
    """In-memory DB."""
    return DictionaryDB(":memory:")


def test_multipos_dialog_add_entry(app, qtbot, db):
    """Ensure MultiPOSDialog stores multiple entries properly."""
    dialog = MultiPOSDialog("kaneran", db)
    qtbot.addWidget(dialog)

    # Simulate checking a POS checkbox
    noun_cb = dialog.checkboxes[0]  # Noun
    noun_cb.setChecked(True)
    dialog.update_definition_fields()

    # Fill in definition and context
    def_input = dialog.definition_fields["Noun"]
    def_input.setPlainText("A test definition.")
    ctx_combo = dialog.context_fields["Noun"]
    ctx_combo.setCurrentText("Test Context")

    # Accept dialog programmatically
    dialog.save_entries()

    assert dialog.entries[0] == ("Noun", "A test definition.", "Test Context", 1)
    dialog.close()
