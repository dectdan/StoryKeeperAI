"""
managers.py

Contains QDialog classes for managing contexts and dictionary entries,
including support for multiple meanings (sense numbers).
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QListWidget, QHBoxLayout, QPushButton,
    QCheckBox, QInputDialog, QMessageBox, QMenu
)
from PyQt6.QtCore import Qt
from db import DictionaryDB


class ContextManager(QDialog):
    """Dialog for managing contexts."""

    def __init__(self, db: DictionaryDB):
        super().__init__()
        self.setWindowTitle("Context Manager")
        self.setGeometry(250, 250, 400, 300)
        self.db = db

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Manage Contexts:"))

        self.context_list = QListWidget()
        self.refresh_list()
        layout.addWidget(self.context_list)

        # Buttons
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add")
        edit_btn = QPushButton("Edit")
        delete_btn = QPushButton("Delete")
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        layout.addLayout(btn_layout)

        add_btn.clicked.connect(self.add_context)
        edit_btn.clicked.connect(self.edit_context)
        delete_btn.clicked.connect(self.delete_context)

        self.auto_checkbox = QCheckBox("Auto-learn new contexts")
        self.auto_checkbox.setChecked(self.db.get_setting("auto_learn_contexts") == "true")
        self.auto_checkbox.stateChanged.connect(self.toggle_auto_learn)
        layout.addWidget(self.auto_checkbox)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

        self.setLayout(layout)

    def refresh_list(self):
        """Refresh the context list."""
        self.context_list.clear()
        for ctx in self.db.get_contexts():
            self.context_list.addItem(ctx)

    def add_context(self):
        """Add a new context."""
        name, ok = QInputDialog.getText(self, "Add Context", "Context name:")
        if ok and name.strip():
            self.db.add_context(name.strip())
            self.refresh_list()

    def edit_context(self):
        """Edit the selected context."""
        selected = self.context_list.currentItem()
        if selected:
            new_name, ok = QInputDialog.getText(self, "Edit Context", "New name:", text=selected.text())
            if ok and new_name.strip():
                self.db.rename_context(selected.text(), new_name.strip())
                self.refresh_list()

    def delete_context(self):
        """Delete the selected context."""
        selected = self.context_list.currentItem()
        if selected:
            self.db.delete_context(selected.text())
            self.refresh_list()

    def toggle_auto_learn(self):
        """Toggle auto-learn setting for contexts."""
        value = "true" if self.auto_checkbox.isChecked() else "false"
        self.db.set_setting("auto_learn_contexts", value)


class DictionaryManager(QDialog):
    """Dialog for managing dictionary entries with multiple meanings."""

    def __init__(self, db: DictionaryDB):
        super().__init__()
        self.setWindowTitle("Dictionary Manager")
        self.setGeometry(200, 200, 650, 500)
        self.db = db

        layout = QVBoxLayout()
        self.word_list = QListWidget()
        self.word_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.word_list.customContextMenuRequested.connect(self.open_context_menu)
        self.refresh_word_list()
        layout.addWidget(self.word_list)

        delete_btn = QPushButton("Delete Selected")
        delete_btn.clicked.connect(self.delete_selected)
        layout.addWidget(delete_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

        self.setLayout(layout)

    def refresh_word_list(self):
        """Refresh the displayed word list with meanings."""
        self.word_list.clear()
        entries = self.db.get_all_entries()
        grouped = {}
        for word, category, pos, definition, context, sense_number in entries:
            key = f"{word} [{category}]"
            grouped.setdefault(key, []).append((pos, definition, context, sense_number))

        for word_key, details in grouped.items():
            display = f"{word_key}\n"
            for pos, definition, context, sense_number in details:
                display += f"  - ({sense_number}) {pos}: {definition} ({context})\n"
            self.word_list.addItem(display.strip())

    def delete_selected(self):
        """Delete the selected word(s) or specific meanings."""
        selected_items = self.word_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Delete", "No word selected.")
            return
        confirm = QMessageBox.question(self, "Delete", "Delete selected word(s)?")
        if confirm == QMessageBox.StandardButton.Yes:
            for item in selected_items:
                lines = item.text().split("\n")
                word = lines[0].split(" [")[0]
                if len(lines) > 2:
                    # Multiple meanings - delete all meanings for this word
                    self.db.delete_entry(word)
                else:
                    # Single meaning - parse sense number
                    if len(lines) > 1:
                        parts = lines[1].strip().split()
                        if parts and parts[0].startswith("(") and parts[0].endswith(")"):
                            try:
                                sense_number = int(parts[0].strip("()"))
                                self.db.delete_entry(word, sense_number=sense_number)
                            except ValueError:
                                self.db.delete_entry(word)
                        else:
                            self.db.delete_entry(word)
                    else:
                        self.db.delete_entry(word)
            self.refresh_word_list()

    def open_context_menu(self, position):
        """Open a right-click context menu for deletion."""
        menu = QMenu()
        delete_action = menu.addAction("Delete")
        action = menu.exec(self.word_list.viewport().mapToGlobal(position))
        if action == delete_action:
            self.delete_selected()
