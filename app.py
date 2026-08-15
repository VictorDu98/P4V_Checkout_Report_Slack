#!/usr/bin/env python3
"""
P4-Overwatch Qt6 MVC Application

Architecture:
- Model: src/model.py (PresetConfig, P4Manager, ReportGenerator, Model)
- View: UI components (main_window, preset_widget, log_viewer)
- Controller: Handles user interactions and model updates
"""

import sys
import os
import json
import threading
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QTextEdit, QTabWidget,
    QLabel, QLineEdit, QFormLayout, QGroupBox, QMessageBox, QDialog,
    QFileDialog, QProgressBar, QComboBox, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QColor, QFont

sys.path.insert(0, os.path.dirname(__file__))

from src.model import Model, PresetConfig, P4Manager, ReportGenerator
from src.logger import setup_logger
import logging


class WorkerThread(QThread):
    """Worker thread for running preset jobs without blocking UI."""

    progress = pyqtSignal(str)  # Progress message
    finished = pyqtSignal(bool, str)  # (success, message)
    error = pyqtSignal(str)

    def __init__(self, preset_name: str):
        super().__init__()
        self.preset_name = preset_name

    def run(self):
        try:
            self.progress.emit(f"Starting job for preset: {self.preset_name}")

            model = Model(self.preset_name)
            self.progress.emit(f"Initialized preset: {self.preset_name}")

            success = model.run()

            if success:
                self.progress.emit(f"Job completed successfully for {self.preset_name}")
                self.finished.emit(True, f"Preset '{self.preset_name}' ran successfully")
            else:
                self.progress.emit(f"Job failed for preset: {self.preset_name}")
                self.finished.emit(False, f"Preset '{self.preset_name}' failed")

        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit(False, f"Error: {e}")


class PresetListModel:
    """Model for managing presets."""

    def __init__(self, presets_dir: str):
        self.presets_dir = presets_dir
        self.presets = {}

    def load_presets(self):
        """Load all presets from directory."""
        self.presets.clear()

        if not os.path.exists(self.presets_dir):
            return

        for item in os.listdir(self.presets_dir):
            item_path = os.path.join(self.presets_dir, item)
            if os.path.isdir(item_path):
                config_path = os.path.join(item_path, "config.csv")
                if os.path.exists(config_path):
                    try:
                        preset_config = PresetConfig(item_path)
                        preset_config.load()
                        self.presets[item] = {
                            "path": item_path,
                            "config": preset_config,
                            "accounts": preset_config.get_accounts(),
                            "departments": preset_config.get_departments(),
                            "webhook": preset_config.get_webhook(),
                        }
                    except Exception as e:
                        print(f"Error loading preset {item}: {e}")

    def get_preset_names(self):
        """Get list of preset names."""
        return list(self.presets.keys())

    def get_preset(self, name: str):
        """Get preset by name."""
        return self.presets.get(name)


class PresetManagerWidget(QWidget):
    """Widget for managing presets."""

    def __init__(self, model: PresetListModel):
        super().__init__()
        self.model = model
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Presets list
        self.preset_list = QListWidget()
        self.preset_list.itemSelectionChanged.connect(self.on_preset_selected)
        layout.addWidget(QLabel("Presets:"))
        layout.addWidget(self.preset_list)

        # Preset details
        details_group = QGroupBox("Preset Details")
        details_layout = QFormLayout()

        self.name_label = QLineEdit()
        self.name_label.setReadOnly(True)
        details_layout.addRow("Name:", self.name_label)

        self.accounts_label = QLineEdit()
        self.accounts_label.setReadOnly(True)
        details_layout.addRow("Accounts:", self.accounts_label)

        self.departments_label = QLineEdit()
        self.departments_label.setReadOnly(True)
        details_layout.addRow("Departments:", self.departments_label)

        self.webhook_label = QLineEdit()
        self.webhook_label.setReadOnly(True)
        details_layout.addRow("Webhook:", self.webhook_label)

        details_group.setLayout(details_layout)
        layout.addWidget(details_group)

        # Action buttons
        button_layout = QHBoxLayout()

        self.run_btn = QPushButton("Run Preset")
        self.run_btn.clicked.connect(self.run_preset)
        button_layout.addWidget(self.run_btn)

        self.refresh_btn = QPushButton("Refresh Presets")
        self.refresh_btn.clicked.connect(self.refresh_presets)
        button_layout.addWidget(self.refresh_btn)

        self.open_config_btn = QPushButton("Edit Config")
        self.open_config_btn.clicked.connect(self.open_config)
        button_layout.addWidget(self.open_config_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def refresh_presets(self):
        """Refresh preset list."""
        self.model.load_presets()
        self.update_list()

    def update_list(self):
        """Update preset list widget."""
        self.preset_list.clear()
        for name in self.model.get_preset_names():
            self.preset_list.addItem(name)

    def on_preset_selected(self):
        """Handle preset selection."""
        items = self.preset_list.selectedItems()
        if not items:
            return

        preset_name = items[0].text()
        preset = self.model.get_preset(preset_name)

        if preset:
            self.name_label.setText(preset_name)
            self.accounts_label.setText(", ".join(preset["accounts"]))
            self.departments_label.setText(", ".join(preset["departments"]))
            self.webhook_label.setText(preset["webhook"][:50] + "...")

    def run_preset(self):
        """Run selected preset."""
        items = self.preset_list.selectedItems()
        if not items:
            QMessageBox.warning(self, "No Selection", "Please select a preset")
            return

        preset_name = items[0].text()
        self.worker = WorkerThread(preset_name)
        self.worker.finished.connect(self.on_job_finished)
        self.worker.error.connect(self.on_job_error)
        self.worker.start()

    def on_job_finished(self, success: bool, message: str):
        """Handle job completion."""
        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.warning(self, "Failed", message)

    def on_job_error(self, error: str):
        """Handle job error."""
        QMessageBox.critical(self, "Error", f"Job error: {error}")

    def open_config(self):
        """Open config file in editor."""
        items = self.preset_list.selectedItems()
        if not items:
            return

        preset_name = items[0].text()
        preset = self.model.get_preset(preset_name)

        if preset:
            config_path = os.path.join(preset["path"], "config.csv")
            os.startfile(config_path)  # Windows
            # For Linux: subprocess.Popen(['gedit', config_path])


class LogViewerWidget(QWidget):
    """Widget for viewing logs."""

    def __init__(self, presets_dir: str):
        super().__init__()
        self.presets_dir = presets_dir
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Preset selector
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Select Preset:"))
        self.preset_combo = QComboBox()
        self.preset_combo.currentTextChanged.connect(self.load_logs)
        selector_layout.addWidget(self.preset_combo)
        layout.addLayout(selector_layout)

        # Log viewer
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(QLabel("Latest Log:"))
        layout.addWidget(self.log_text)

        # Refresh button
        refresh_btn = QPushButton("Refresh Logs")
        refresh_btn.clicked.connect(self.load_logs)
        layout.addWidget(refresh_btn)

        self.setLayout(layout)
        self.update_preset_list()

    def update_preset_list(self):
        """Update preset dropdown."""
        self.preset_combo.clear()
        if os.path.exists(self.presets_dir):
            for item in os.listdir(self.presets_dir):
                item_path = os.path.join(self.presets_dir, item)
                if os.path.isdir(item_path):
                    self.preset_combo.addItem(item)

    def load_logs(self):
        """Load logs for selected preset."""
        preset_name = self.preset_combo.currentText()
        if not preset_name:
            return

        try:
            preset_config = PresetConfig(os.path.join(self.presets_dir, preset_name))
            preset_config.load()
            output_root = preset_config.get_output_root()

            # Find latest log file
            if os.path.exists(output_root):
                log_files = [f for f in os.listdir(output_root) if f.startswith(f"log_{preset_name}")]
                if log_files:
                    latest_log = sorted(log_files)[-1]
                    log_path = os.path.join(output_root, latest_log)

                    with open(log_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    self.log_text.setText(content)
                    return

            self.log_text.setText("No logs found")

        except Exception as e:
            self.log_text.setText(f"Error loading logs: {e}")


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("P4-Overwatch - Perforce Check-in Manager")
        self.setGeometry(100, 100, 1200, 800)

        # Initialize model
        presets_dir = os.path.join(os.path.dirname(__file__), "src", "presets")
        self.preset_model = PresetListModel(presets_dir)
        self.preset_model.load_presets()

        # Create tabs
        self.tabs = QTabWidget()

        # Preset Manager tab
        self.preset_manager = PresetManagerWidget(self.preset_model)
        self.tabs.addTab(self.preset_manager, "Preset Manager")

        # Log Viewer tab
        self.log_viewer = LogViewerWidget(presets_dir)
        self.tabs.addTab(self.log_viewer, "Log Viewer")

        # About tab
        self.tabs.addTab(self.create_about_tab(), "About")

        self.setCentralWidget(self.tabs)

        # Status bar
        self.statusBar().showMessage("Ready")

        # Menu bar
        self.create_menu_bar()

    def create_menu_bar(self):
        """Create application menu bar."""
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        file_menu.addAction("Exit", self.close)

        edit_menu = menubar.addMenu("Edit")
        edit_menu.addAction("Refresh Presets", self.preset_manager.refresh_presets)

        help_menu = menubar.addMenu("Help")
        help_menu.addAction("About", self.show_about)

    def create_about_tab(self):
        """Create about tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        about_text = QTextEdit()
        about_text.setReadOnly(True)
        about_text.setText("""
        P4-Overwatch v1.0
        Perforce Check-in Manager

        A tool to remind your team to check in their Perforce work.

        Features:
        • Multiple preset management
        • P4Python integration
        • Microsoft Teams notifications
        • Log viewing and monitoring

        Visit: https://github.com/VictorDu98/P4-Overwatch
                """)

        layout.addWidget(about_text)
        widget.setLayout(layout)
        return widget

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About P4-Overwatch",
            "P4-Overwatch v1.0\n\nA Perforce check-in reminder tool\nwith Microsoft Teams integration"
        )


def main():
    """Application entry point."""
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
