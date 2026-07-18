import unittest
import os
import sys
import json
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
        """Test validation fails when config.json is missing."""
        is_valid, errors = self.validator.validate_preset(self.preset_name, self.preset_path)
        self.assertFalse(is_valid)
        self.assertTrue(any("config.json" in str(e) for e in errors))

    def test_validate_invalid_json(self):
        """Test validation fails with invalid JSON."""
        config_path = os.path.join(self.preset_path, "config.json")
        with open(config_path, 'w') as f:
            f.write("{invalid json}")

        is_valid, errors = self.validator.validate_preset(self.preset_name, self.preset_path)
        self.assertFalse(is_valid)
        self.assertTrue(any("Invalid JSON" in str(e) for e in errors))

    def test_validate_missing_required_fields(self):
        """Test validation fails when required fields are missing."""
        config = {
            "misc": [],
            "info": []
        }
        config_path = os.path.join(self.preset_path, "config.json")
        with open(config_path, 'w') as f:
            json.dump(config, f)

        is_valid, errors = self.validator.validate_preset(self.preset_name, self.preset_path)
        self.assertFalse(is_valid)
        self.assertTrue(len(errors) > 0)

    def test_validate_placeholder_output(self):
        """Test validation fails when output is placeholder."""
        config = {
            "misc": [{"OutputLogAndReport": "Output address to store logs and report", "Webhook": "https://example.com"}],
            "info": [{"AccountName": "alice", "Department": "VFX", "Email": "alice@test.com", "WorkSpace": "alice_ws"}]
        }
        config_path = os.path.join(self.preset_path, "config.json")
        with open(config_path, 'w') as f:
            json.dump(config, f)

        is_valid, errors = self.validator.validate_preset(self.preset_name, self.preset_path)
        self.assertFalse(is_valid)
        self.assertTrue(any("placeholder" in str(e).lower() for e in errors))

    def test_validate_placeholder_webhook(self):
        """Test validation fails when webhook is placeholder."""
        config = {
            "misc": [{"OutputLogAndReport": self.test_dir, "Webhook": "Microsoft Teams Workflow incoming webhook"}],
            "info": [{"AccountName": "alice", "Department": "VFX", "Email": "alice@test.com", "WorkSpace": "alice_ws"}]
        }
        config_path = os.path.join(self.preset_path, "config.json")
        with open(config_path, 'w') as f:
            json.dump(config, f)

        is_valid, errors = self.validator.validate_preset(self.preset_name, self.preset_path)
        self.assertFalse(is_valid)
        self.assertTrue(any("placeholder" in str(e).lower() for e in errors))

    def test_validate_invalid_webhook_url(self):
        """Test validation fails with invalid webhook URL."""
        config = {
            "misc": [{"OutputLogAndReport": self.test_dir, "Webhook": "not-a-url"}],
            "info": [{"AccountName": "alice", "Department": "VFX", "Email": "alice@test.com", "WorkSpace": "alice_ws"}]
        }
        config_path = os.path.join(self.preset_path, "config.json")
        with open(config_path, 'w') as f:
            json.dump(config, f)

        is_valid, errors = self.validator.validate_preset(self.preset_name, self.preset_path)
        self.assertFalse(is_valid)
        self.assertTrue(any("URL" in str(e) or "webhook" in str(e).lower() for e in errors))

    def test_validate_missing_user_email(self):
        """Test validation fails when user is missing Email."""
        config = {
            "misc": [{"OutputLogAndReport": self.test_dir, "Webhook": "https://example.com"}],
            "info": [{"AccountName": "alice", "Department": "VFX", "WorkSpace": "alice_ws"}]
        }
        config_path = os.path.join(self.preset_path, "config.json")
        with open(config_path, 'w') as f:
            json.dump(config, f)

        is_valid, errors = self.validator.validate_preset(self.preset_name, self.preset_path)
        self.assertFalse(is_valid)
        self.assertTrue(any("Email" in str(e) for e in errors))

    def test_validate_valid_preset(self):
        """Test validation passes with valid preset."""
        config = {
            "misc": [{"OutputLogAndReport": self.test_dir, "Webhook": "https://example.com"}],
            "info": [
                {"AccountName": "alice", "Department": "VFX", "Email": "alice@test.com", "WorkSpace": "alice_ws"},
                {"AccountName": "bob", "Department": "ENV", "Email": "bob@test.com", "WorkSpace": "bob_ws"}
            ]
        }
        config_path = os.path.join(self.preset_path, "config.json")
        with open(config_path, 'w') as f:
            json.dump(config, f)

        is_valid, errors = self.validator.validate_preset(self.preset_name, self.preset_path)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_validate_relative_path_rejected(self):
        """Test validation rejects relative output path."""
        config = {
            "misc": [{"OutputLogAndReport": "relative/path", "Webhook": "https://example.com"}],
            "info": [{"AccountName": "alice", "Department": "VFX", "Email": "alice@test.com", "WorkSpace": "alice_ws"}]
        }
        config_path = os.path.join(self.preset_path, "config.json")
        with open(config_path, 'w') as f:
            json.dump(config, f)

        is_valid, errors = self.validator.validate_preset(self.preset_name, self.preset_path)
        self.assertFalse(is_valid)
        self.assertTrue(any("absolute" in str(e).lower() for e in errors))


if __name__ == '__main__':
    unittest.main()
