"""
dialogs.py

Contains all QDialog-based components for exporting, importing, 
and managing parts of speech with support for multiple meanings.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QComboBox,
    QCheckBox, QWidget, QHBoxLayout, QTextEdit, QFrame, QSpinBox
)
from PyQt6.QtCore import Qt
from typing import List
from db import DictionaryDB


class ExportDialog(QDialog):
    """Dialog for exporting project data."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Export Project")
        self.setGeometry(300, 300, 300, 150)

        layout = QVBoxLayout()
        self.include_dict_cb = QCheckBox("Include Dictionary")
        self.include_dict_cb.setChecked(True)
        layout.addWidget(self.include_dict_cb)

        self.include_ctx_cb = QCheckBox("Include Contexts")
        self.include_ctx_cb.setChecked(True)
        layout.addWidget(self.include_ctx_cb)

        save_btn = QPushButton("Export")
        save_btn.clicked.connect(self.accept)
        layout.addWidget(save_btn)

        self.setLayout(layout)


class ImportDialog(QDialog):
    """Dialog for importing project data."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Import Project")
        self.setGeometry(300, 300, 300, 200)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Dictionary Import Mode:"))
        self.dict_mode = QComboBox()
        self.dict_mode.addItems(["Merge", "Replace", "Skip"])
        layout.addWidget(self.dict_mode)

        layout.addWidget(QLabel("Context Import Mode:"))
        self.ctx_mode = QComboBox()
        self.ctx_mode.addItems(["Merge", "Replace", "Skip"])
        layout.addWidget(self.ctx_mode)

        import_btn = QPushButton("Import")
        import_btn.clicked.connect(self.accept)
        layout.addWidget(import_btn)

        self.setLayout(layout)


class MultiPOSDialog(QDialog):
    """Dialog for adding multiple parts of speech and multiple meanings for a word."""

    POS_OPTIONS = ["Noun", "Verb", "Adjective", "Adverb", "Pronoun", "Other"]

    def __init__(self, word: str, db: DictionaryDB, parent: QWidget = None):
        super().__init__(parent)
        self.setWindowTitle(f"Add '{word}' to Dictionary")
        self.setGeometry(300, 300, 600, 600)
        self.word = word
        self.db = db
        self.entries = []

        main_layout = QVBoxLayout()

        # Category Input
        cat_layout = QHBoxLayout()
        cat_layout.addWidget(QLabel("Category:"))
        self.category_input = QPushButton("General")
        self.category_input.setCheckable(True)
        cat_layout.addWidget(self.category_input)
        main_layout.addLayout(cat_layout)

        # Part of speech checkboxes
        self.checkboxes = []
        main_layout.addWidget(QLabel("Select Parts of Speech:"))
        for pos in self.POS_OPTIONS:
            cb = QCheckBox(pos)
            self.checkboxes.append(cb)
            main_layout.addWidget(cb)

        # Scrollable area for definitions
        self.scroll_area = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_area)
        main_layout.addWidget(self.scroll_area)

        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        save_btn.clicked.connect(self.save_entries)
        cancel_btn.clicked.connect(self.close)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        main_layout.addLayout(button_layout)

        for cb in self.checkboxes:
            cb.stateChanged.connect(self.update_definition_fields)

        self.setLayout(main_layout)

    def update_definition_fields(self):
        """Update input fields dynamically based on selected parts of speech."""
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        self.definition_fields = {}
        self.context_fields = {}
        self.sense_fields = {}
        context_list = self.db.get_contexts()

        for cb in self.checkboxes:
            if cb.isChecked():
                frame = QFrame()
                vbox = QVBoxLayout(frame)

                # Definition
                vbox.addWidget(QLabel(f"{cb.text()} Definition:"))
                def_input = QTextEdit()
                vbox.addWidget(def_input)

                # Context
                vbox.addWidget(QLabel(f"{cb.text()} Context Hint:"))
                ctx_combo = QComboBox()
                ctx_combo.addItems(context_list)
                ctx_combo.setEditable(True)
                vbox.addWidget(ctx_combo)

                # Sense number
                vbox.addWidget(QLabel("Meaning Number:"))
                sense_spin = QSpinBox()
                sense_spin.setMinimum(1)
                sense_spin.setMaximum(50)
                vbox.addWidget(sense_spin)

                self.scroll_layout.addWidget(frame)
                self.definition_fields[cb.text()] = def_input
                self.context_fields[cb.text()] = ctx_combo
                self.sense_fields[cb.text()] = sense_spin

    def save_entries(self):
        """Save all selected entries to be added to the dictionary."""
        category = self.category_input.text().strip() or "General"
        for pos, def_input in self.definition_fields.items():
            definition = def_input.toPlainText().strip()
            context = self.context_fields[pos].currentText().strip()
            sense_number = self.sense_fields[pos].value()
            if definition:
                self.entries.append((pos, definition, context, sense_number))
                if self.db.get_setting("auto_learn_contexts") == "true" and context:
                    self.db.add_context(context)
        if self.entries:
            self.accept()
