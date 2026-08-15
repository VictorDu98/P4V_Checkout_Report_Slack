import unittest
import os
import sys
import json
import csv
import tempfile
import shutil
import logging
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.preset_validator import PresetValidator


class TestPresetValidator(unittest.TestCase):
    """Test PresetValidator class."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.preset_name = "TEST_PRESET"
        self.preset_path = os.path.join(self.test_dir, self.preset_name)
        os.makedirs(self.preset_path)

        # Create a quiet logger for tests (no console output)
        self.log = logging.getLogger("test_validator")
        self.log.handlers.clear()
        self.log.addHandler(logging.NullHandler())
        self.log.setLevel(logging.DEBUG)

        self.validator = PresetValidator(self.log)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_validate_missing_config(self):
        """Test validation fails when config.csv is missing."""
        is_valid, errors = self.validator.validate_preset(self.preset_name, self.preset_path)
        self.assertFalse(is_valid)
        self.assertTrue(any("config.csv" in str(e) for e in errors))

    def test_validate_invalid_csv(self):
        """Test validation fails with invalid CSV."""
        config_path = os.path.join(self.preset_path, "config.csv")
        with open(config_path, 'w') as f:
            f.write("")  # Empty CSV

        is_valid, errors = self.validator.validate_preset(self.preset_name, self.preset_path)
        self.assertFalse(is_valid)
        self.assertTrue(any("Invalid CSV" in str(e) for e in errors))

    def test_validate_missing_required_fields(self):
        """Test validation fails when required fields are missing."""
        csv_data = [
            ["Miscellaneous", "", "", ""],
            ["", "", "", ""],
            ["User info", "", "", ""]
        ]
        config_path = os.path.join(self.preset_path, "config.csv")
        with open(config_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(csv_data)

        is_valid, errors = self.validator.validate_preset(self.preset_name, self.preset_path)
        self.assertFalse(is_valid)
        self.assertTrue(len(errors) > 0)

    def test_validate_placeholder_output(self):
        """Test validation fails when output is placeholder."""
        csv_data = [
            ["Miscellaneous", "", "", ""],
            ["OutputLogAndReport", "Output address to store logs and report", "", ""],
            ["Webhook", "https://example.com", "", ""],
            ["Schedule Time", "18:30", "", ""],
            ["Department", "VFX", "", ""],
            ["", "", "", ""],
            ["User info", "", "", ""],
            ["AccountName", "UserName(Optional)", "Hostname(Optional)", "WorkspaceName", "Email"],
            ["alice", "", "", "alice_ws", "alice@test.com"]
        ]
        config_path = os.path.join(self.preset_path, "config.csv")
        with open(config_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(csv_data)

        is_valid, errors = self.validator.validate_preset(self.preset_name, self.preset_path)
        self.assertFalse(is_valid)
        self.assertTrue(any("placeholder" in str(e).lower() for e in errors))

    def test_validate_placeholder_webhook(self):
        """Test validation fails when webhook is placeholder."""
        csv_data = [
            ["Miscellaneous", "", "", ""],
            ["OutputLogAndReport", self.test_dir, "", ""],
            ["Webhook", "Microsoft Teams Workflow incoming webhook", "", ""],
            ["Schedule Time", "18:30", "", ""],
            ["Department", "VFX", "", ""],
            ["", "", "", ""],
            ["User info", "", "", ""],
            ["AccountName", "UserName(Optional)", "Hostname(Optional)", "WorkspaceName", "Email"],
            ["alice", "", "", "alice_ws", "alice@test.com"]
        ]
        config_path = os.path.join(self.preset_path, "config.csv")
        with open(config_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(csv_data)

        is_valid, errors = self.validator.validate_preset(self.preset_name, self.preset_path)
        self.assertFalse(is_valid)
        self.assertTrue(any("placeholder" in str(e).lower() for e in errors))

    def test_validate_invalid_webhook_url(self):
        """Test validation fails with invalid webhook URL."""
        csv_data = [
            ["Miscellaneous", "", "", ""],
            ["OutputLogAndReport", self.test_dir, "", ""],
            ["Webhook", "not-a-url", "", ""],
            ["Schedule Time", "18:30", "", ""],
            ["Department", "VFX", "", ""],
            ["", "", "", ""],
            ["User info", "", "", ""],
            ["AccountName", "UserName(Optional)", "Hostname(Optional)", "WorkspaceName", "Email"],
            ["alice", "", "", "alice_ws", "alice@test.com"]
        ]
        config_path = os.path.join(self.preset_path, "config.csv")
        with open(config_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(csv_data)

        is_valid, errors = self.validator.validate_preset(self.preset_name, self.preset_path)
        self.assertFalse(is_valid)
        self.assertTrue(any("URL" in str(e) or "webhook" in str(e).lower() for e in errors))

    def test_validate_missing_user_email(self):
        """Test validation fails when user is missing Email."""
        csv_data = [
            ["Miscellaneous", "", "", ""],
            ["OutputLogAndReport", self.test_dir, "", ""],
            ["Webhook", "https://example.com", "", ""],
            ["Schedule Time", "18:30", "", ""],
            ["Department", "VFX", "", ""],
            ["", "", "", ""],
            ["User info", "", "", ""],
            ["AccountName", "UserName(Optional)", "Hostname(Optional)", "WorkspaceName"],
            ["alice", "", "", "alice_ws"]
        ]
        config_path = os.path.join(self.preset_path, "config.csv")
        with open(config_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(csv_data)

        is_valid, errors = self.validator.validate_preset(self.preset_name, self.preset_path)
        self.assertFalse(is_valid)
        self.assertTrue(any("Email" in str(e) for e in errors))

    def test_validate_valid_preset(self):
        """Test validation passes with valid preset."""
        csv_data = [
            ["Miscellaneous", "", "", ""],
            ["OutputLogAndReport", self.test_dir, "", ""],
            ["Webhook", "https://example.com", "", ""],
            ["Schedule Time", "18:30", "", ""],
            ["Department", "VFX", "", ""],
            ["", "", "", ""],
            ["User info", "", "", ""],
            ["AccountName", "UserName(Optional)", "Hostname(Optional)", "WorkspaceName", "Email"],
            ["alice", "", "", "alice_ws", "alice@test.com"],
            ["bob", "", "", "bob_ws", "bob@test.com"]
        ]
        config_path = os.path.join(self.preset_path, "config.csv")
        with open(config_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(csv_data)

        is_valid, errors = self.validator.validate_preset(self.preset_name, self.preset_path)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_validate_relative_path_rejected(self):
        """Test validation rejects relative output path."""
        csv_data = [
            ["Miscellaneous", "", "", ""],
            ["OutputLogAndReport", "relative/path", "", ""],
            ["Webhook", "https://example.com", "", ""],
            ["Schedule Time", "18:30", "", ""],
            ["Department", "VFX", "", ""],
            ["", "", "", ""],
            ["User info", "", "", ""],
            ["AccountName", "UserName(Optional)", "Hostname(Optional)", "WorkspaceName", "Email"],
            ["alice", "", "", "alice_ws", "alice@test.com"]
        ]
        config_path = os.path.join(self.preset_path, "config.csv")
        with open(config_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(csv_data)

        is_valid, errors = self.validator.validate_preset(self.preset_name, self.preset_path)
        self.assertFalse(is_valid)
        self.assertTrue(any("absolute" in str(e).lower() for e in errors))


if __name__ == '__main__':
    unittest.main()
