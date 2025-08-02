"""
main_window.py

Main application window for StoryKeeper, including menus, toolbar,
dockable widgets, and import/export functionality.
"""

import os
import json
import zipfile
import tempfile
from PyQt6.QtWidgets import (
    QMainWindow, QFileDialog, QStatusBar, QDockWidget, QMessageBox
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt
from db import DictionaryDB
from widgets import Sidebar, SpellCheckTextEdit
from dialogs import ExportDialog, ImportDialog
from constants import APP_VERSION


class StoryKeeper(QMainWindow):
    """Main window of the StoryKeeper application."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"StoryKeeper AI — {APP_VERSION}")
        self.setGeometry(100, 100, 1000, 600)

        self.db = DictionaryDB()
        self.text_edit = SpellCheckTextEdit(self.db)
        self.setCentralWidget(self.text_edit)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.create_menu()
        self.create_sidebar()

    def create_menu(self):
        """Create the menu bar."""
        menu = self.menuBar()
        file_menu = menu.addMenu("File")

        new_action = QAction("New", self)
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)

        open_action = QAction("Open", self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        export_action = QAction("Export Project", self)
        export_action.triggered.connect(self.export_project)
        file_menu.addAction(export_action)

        import_action = QAction("Import Project", self)
        import_action.triggered.connect(self.import_project)
        file_menu.addAction(import_action)

    def create_sidebar(self):
        """Create the right-side dockable tools panel."""
        dock = QDockWidget("Tools", self)
        dock.setWidget(Sidebar(self.db, self))
        dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)

    def new_file(self):
        """Create a new file."""
        self.text_edit.clear()
        self.status_bar.showMessage("New file created", 3000)

    def open_file(self):
        """Open a text file."""
        path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Text Files (*.txt);;All Files (*)")
        if path:
            with open(path, 'r', encoding='utf-8') as file:
                self.text_edit.setText(file.read())
            self.status_bar.showMessage(f"Opened {path}", 3000)

    def save_file(self):
        """Save the current text to a file."""
        path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Text Files (*.txt);;All Files (*)")
        if path:
            with open(path, 'w', encoding='utf-8') as file:
                file.write(self.text_edit.toPlainText())
            self.status_bar.showMessage(f"Saved {path}", 3000)

    def export_project(self):
        """Export the current project to a ZIP file."""
        dialog = ExportDialog()
        if dialog.exec():
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Project", "", "Zip Files (*.zip)")
            if not file_path:
                return

            dictionary_data = self.db.export_dictionary() if dialog.include_dict_cb.isChecked() else None
            context_data = self.db.export_contexts() if dialog.include_ctx_cb.isChecked() else None
            text_data = self.text_edit.toPlainText()

            with tempfile.TemporaryDirectory() as tmpdir:
                if dictionary_data:
                    with open(os.path.join(tmpdir, "dictionary.json"), 'w', encoding='utf-8') as f:
                        json.dump(dictionary_data, f, indent=2)

                if context_data:
                    with open(os.path.join(tmpdir, "contexts.json"), 'w', encoding='utf-8') as f:
                        json.dump(context_data, f, indent=2)

                with open(os.path.join(tmpdir, "content.txt"), 'w', encoding='utf-8') as f:
                    f.write(text_data)

                with zipfile.ZipFile(file_path, 'w') as zipf:
                    for filename in os.listdir(tmpdir):
                        zipf.write(os.path.join(tmpdir, filename), filename)

            QMessageBox.information(self, "Export", "Project exported successfully!")

    def import_project(self):
        """Import a project from a ZIP file."""
        dialog = ImportDialog()
        if dialog.exec():
            file_path, _ = QFileDialog.getOpenFileName(self, "Import Project", "", "Zip Files (*.zip)")
            if not file_path:
                return

            dict_mode = dialog.dict_mode.currentText().lower()
            ctx_mode = dialog.ctx_mode.currentText().lower()

            with tempfile.TemporaryDirectory() as tmpdir:
                with zipfile.ZipFile(file_path, 'r') as zipf:
                    zipf.extractall(tmpdir)

                dict_file = os.path.join(tmpdir, "dictionary.json")
                ctx_file = os.path.join(tmpdir, "contexts.json")
                content_file = os.path.join(tmpdir, "content.txt")

                if os.path.exists(dict_file) and dict_mode != "skip":
                    with open(dict_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.db.import_dictionary(data, mode=dict_mode)

                if os.path.exists(ctx_file) and ctx_mode != "skip":
                    with open(ctx_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.db.import_contexts(data, mode=ctx_mode)

                if os.path.exists(content_file):
                    with open(content_file, 'r', encoding='utf-8') as f:
                        self.text_edit.setText(f.read())

            QMessageBox.information(self, "Import", "Project imported successfully!")
