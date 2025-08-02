"""
widgets.py

Contains custom reusable widgets for the StoryKeeper application,
including the Sidebar and SpellCheckTextEdit with dictionary integration.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit, QMenu
from PyQt6.QtGui import QTextCharFormat, QColor
from PyQt6.QtCore import QTimer, Qt
from spellchecker import SpellChecker
from typing import Set
from db import DictionaryDB
from managers import ContextManager, DictionaryManager
from dialogs import MultiPOSDialog


class Sidebar(QWidget):
    """Sidebar widget providing quick access to dictionary and context managers."""

    def __init__(self, db: DictionaryDB, parent=None):
        super().__init__(parent)
        self.db = db
        layout = QVBoxLayout()

        layout.addWidget(QLabel("📚 Dictionary"))
        manage_btn = QPushButton("Manage Words")
        manage_btn.clicked.connect(self.open_dictionary_manager)
        layout.addWidget(manage_btn)

        layout.addWidget(QLabel("🧠 Contexts"))
        context_btn = QPushButton("Manage Contexts")
        context_btn.clicked.connect(self.open_context_manager)
        layout.addWidget(context_btn)

        layout.addStretch()
        self.setLayout(layout)

    def open_dictionary_manager(self):
        """Open the dictionary manager dialog."""
        self.manager = DictionaryManager(self.db)
        self.manager.exec()

    def open_context_manager(self):
        """Open the context manager dialog."""
        self.ctx_manager = ContextManager(self.db)
        self.ctx_manager.exec()


class SpellCheckTextEdit(QTextEdit):
    """Custom QTextEdit with spellchecking and dictionary integration."""

    def __init__(self, db: DictionaryDB):
        super().__init__()
        self.db = db
        self.spellchecker = SpellChecker()
        self.debounce_timer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self.run_spellcheck)
        self.textChanged.connect(self.schedule_spellcheck)

    def schedule_spellcheck(self):
        """Schedule spellcheck after a short debounce delay."""
        self.debounce_timer.start(300)

    def run_spellcheck(self):
        """Run spellchecking on the entire document."""
        try:
            cursor = self.textCursor()
            cursor.select(cursor.SelectionType.Document)
            text = cursor.selectedText()

            # Reset formatting
            cursor.setPosition(0)
            cursor.movePosition(cursor.MoveOperation.End, cursor.MoveMode.KeepAnchor)
            cursor.setCharFormat(QTextCharFormat())

            if not text.strip():
                return

            words = [w.strip(".,!?;:") for w in text.split() if w.isalpha()]
            if not words:
                return

            custom_words: Set[str] = set(w.lower() for w in self.db.get_words_list())
            misspelled = self.spellchecker.unknown(words)

            for word in misspelled:
                if word.lower() not in custom_words:
                    self.highlight_word(word)

        except Exception as e:
            print(f"Spellcheck error: {e}")

    def highlight_word(self, word: str):
        """Highlight misspelled words."""
        format_red = QTextCharFormat()
        format_red.setUnderlineColor(QColor("red"))
        format_red.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SpellCheckUnderline)

        doc = self.document()
        cursor = doc.find(word, 0)
        while cursor and not cursor.isNull():
            cursor.mergeCharFormat(format_red)
            cursor = doc.find(word, cursor.position())

    def contextMenuEvent(self, event):
        """Add context menu option to add words to dictionary with multiple meanings."""
        cursor = self.cursorForPosition(event.pos())
        cursor.select(cursor.SelectionType.WordUnderCursor)
        selected_word = cursor.selectedText()

        menu = QMenu(self)
        if selected_word and selected_word.isalpha():
            custom_words = set(self.db.get_words_list())
            if selected_word.lower() not in custom_words:
                add_action = menu.addAction(f"Add '{selected_word}' to Dictionary")
                action = menu.exec(event.globalPos())
                if action == add_action:
                    dialog = MultiPOSDialog(selected_word, self.db, self)
                    if dialog.exec():
                        self.db.add_multiple_entries(
                            selected_word,
                            dialog.category_input.text(),
                            dialog.entries
                        )
                        self.run_spellcheck()
                        return
        super().contextMenuEvent(event)
