import unittest
import os
import sys
import json
import tempfile
import shutil
from unittest.mock import Mock, patch, mock_open, MagicMock, call
from datetime import datetime, timezone, timedelta
from pathlib import Path
from http import HTTPStatus

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.model import Model, PresetConfig, P4Manager, ReportGenerator


class TestReportGeneratorStaticMethods(unittest.TestCase):
    """Test ReportGenerator static utility methods."""

    def test_trace_workspace_single_match(self):
        """Test trace_workspace extracts workspace names from log lines."""
        log_lines = [
            "//depot/file.cpp - edit - CL 12345 - alice_workspace",
            "//depot/script.py - edit - CL 12346 - bob_ws",
        ]
        result = ReportGenerator.trace_workspace(log_lines)
        self.assertEqual(result, ["alice_workspace", "bob_ws"])

    def test_trace_workspace_no_duplicates(self):
        """Test trace_workspace removes duplicate workspace names."""
        log_lines = [
            "//depot/file1.cpp - edit - CL 12345 - alice_workspace",
            "//depot/file2.cpp - edit - CL 12346 - alice_workspace",
            "//depot/file3.cpp - edit - CL 12347 - bob_ws",
        ]
        result = ReportGenerator.trace_workspace(log_lines)
        self.assertEqual(result, ["alice_workspace", "bob_ws"])

    def test_trace_workspace_ignores_non_edit_lines(self):
        """Test trace_workspace ignores lines without 'edit' action."""
        log_lines = [
            "//depot/file.cpp - add - CL 12345 - alice_workspace",
            "//depot/file.cpp - delete - CL 12345 - bob_ws",
            "//depot/file.cpp - edit - CL 12345 - charlie_ws",
        ]
        result = ReportGenerator.trace_workspace(log_lines)
        self.assertEqual(result, ["charlie_ws"])

    def test_trace_workspace_empty_input(self):
        """Test trace_workspace with empty list."""
        result = ReportGenerator.trace_workspace([])
        self.assertEqual(result, [])

    def test_find_matching_users_exact_match(self):
        """Test find_matching_users returns correct indices."""
        found = ["alice_workspace", "bob_ws"]
        config = ["alice_workspace", "bob_ws", "charlie_ws"]
        result = ReportGenerator.find_matching_users(found, config)
        self.assertEqual(result, [0, 1])

    def test_find_matching_users_partial_match(self):
        """Test find_matching_users with regex prefix matching."""
        found = ["alice"]
        config = ["alice_workspace", "bob_ws"]
        result = ReportGenerator.find_matching_users(found, config)
        self.assertEqual(result, [0])

    def test_find_matching_users_no_match(self):
        """Test find_matching_users returns empty list when no matches."""
        found = ["unknown"]
        config = ["alice_workspace", "bob_ws"]
        result = ReportGenerator.find_matching_users(found, config)
        self.assertEqual(result, [])

    def test_find_matching_users_empty_found(self):
        """Test find_matching_users with empty found workspaces."""
        result = ReportGenerator.find_matching_users([], ["alice_workspace"])
        self.assertEqual(result, [])


class TestModelStaticMethods(unittest.TestCase):
    """Test Model static utility methods."""

    def test_get_date(self):
        """Test get_date returns YYMMDD format."""
        result = Model.get_date()
        self.assertEqual(len(result), 6)
        self.assertTrue(result.isdigit())
        expected = datetime.now().strftime("%y%m%d")
        self.assertEqual(result, expected)

    def test_get_time(self):
        """Test get_time returns HH:MM AM/PM in UTC+7."""
        result = Model.get_time()
        self.assertRegex(result, r'\d{2}:\d{2} (?:AM|PM)')


class TestPresetConfig(unittest.TestCase):
    """Test PresetConfig class."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.preset_path = os.path.join(self.test_dir, "TEST_PRESET")
        os.makedirs(self.preset_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_load_valid_config(self):
        """Test loading valid config.json."""
        config = {
            "misc": [{"OutputLogAndReport": self.test_dir, "Webhook": "https://example.com"}],
            "info": [
                {"AccountName": "alice", "Department": "VFX", "Email": "alice@test.com", "WorkSpace": "alice_ws"}
            ]
        }
        config_path = os.path.join(self.preset_path, "config.json")
        with open(config_path, 'w') as f:
            json.dump(config, f)

        preset = PresetConfig(self.preset_path)
        preset.load()

        self.assertEqual(preset.get_output_root(), self.test_dir)
        self.assertEqual(preset.get_webhook(), "https://example.com")
        self.assertEqual(preset.get_accounts(), ["alice"])
        self.assertEqual(preset.get_workspaces(), ["alice_ws"])
        self.assertEqual(preset.get_departments(), ["VFX"])

    def test_load_missing_config(self):
        """Test loading missing config raises error."""
        preset = PresetConfig(self.preset_path)
        with self.assertRaises(FileNotFoundError):
            preset.load()

    def test_load_invalid_json(self):
        """Test loading invalid JSON raises error."""
        config_path = os.path.join(self.preset_path, "config.json")
        with open(config_path, 'w') as f:
            f.write("{invalid json}")

        preset = PresetConfig(self.preset_path)
        with self.assertRaises(ValueError):
            preset.load()

    def test_get_user_by_index(self):
        """Test getting user by index."""
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

        preset = PresetConfig(self.preset_path)
        preset.load()

        user = preset.get_user_by_index(0)
        self.assertEqual(user["AccountName"], "alice")

    def test_create_template(self):
        """Test template creation."""
        preset = PresetConfig(self.preset_path)
        preset.create_template()

        self.assertTrue(os.path.exists(os.path.join(self.preset_path, "config.json")))
        self.assertTrue(os.path.exists(os.path.join(self.preset_path, ".p4config")))

        preset.load()
        self.assertIn("misc", preset.config)
        self.assertIn("info", preset.config)


class TestP4Manager(unittest.TestCase):
    """Test P4Manager class."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.log = Mock()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_get_opened_files_empty(self):
        """Test get_opened_files with no files."""
        manager = P4Manager(self.test_dir, self.log)
        manager.p4 = Mock()
        manager.p4.connected.return_value = True
        manager.p4.run_opened.return_value = []

        result = manager.get_opened_files("alice")
        self.assertEqual(result, [])

    def test_get_opened_files_not_connected(self):
        """Test get_opened_files when P4 not connected."""
        manager = P4Manager(self.test_dir, self.log)
        manager.p4 = None

        result = manager.get_opened_files("alice")
        self.assertEqual(result, [])
        self.log.warning.assert_called()

    def test_context_manager_enter(self):
        """Test P4Manager context manager __enter__."""
        manager = P4Manager(self.test_dir, self.log)
        result = manager.__enter__()
        self.assertIs(result, manager)

    def test_context_manager_exit(self):
        """Test P4Manager context manager __exit__ calls disconnect."""
        manager = P4Manager(self.test_dir, self.log)
        manager.disconnect = Mock()

        manager.__exit__(None, None, None)

        manager.disconnect.assert_called_once()

    def test_context_manager_exit_on_exception(self):
        """Test P4Manager __exit__ still disconnects even with exception."""
        manager = P4Manager(self.test_dir, self.log)
        manager.disconnect = Mock()

        # Simulate exception context
        exc_type = ValueError
        exc_val = ValueError("Test error")
        exc_tb = None

        result = manager.__exit__(exc_type, exc_val, exc_tb)

        manager.disconnect.assert_called_once()
        self.assertFalse(result)  # Should return False to propagate exception

    def test_context_manager_with_statement(self):
        """Test P4Manager works as context manager."""
        with P4Manager(self.test_dir, self.log) as manager:
            self.assertIsNotNone(manager)
            manager.disconnect = Mock()

        manager.disconnect.assert_called_once()


class TestReportGenerator(unittest.TestCase):
    """Test ReportGenerator class."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.log = Mock()
        self.gen = ReportGenerator(self.log)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_workspace_pattern_is_class_variable(self):
        """Test WORKSPACE_PATTERN is compiled at class level."""
        self.assertIsNotNone(ReportGenerator.WORKSPACE_PATTERN)
        # Pattern should be a compiled regex object
        self.assertTrue(hasattr(ReportGenerator.WORKSPACE_PATTERN, 'match'))

    def test_trace_workspace_uses_class_pattern(self):
        """Test trace_workspace uses class-level regex pattern."""
        lines = [
            "//depot/file.cpp - edit - CL 12345 - alice_workspace",
            "//depot/file2.cpp - edit - CL 12346 - bob_ws",
        ]
        result = ReportGenerator.trace_workspace(lines)
        self.assertEqual(result, ["alice_workspace", "bob_ws"])

    def test_generate_report_with_users(self):
        """Test generating report with found users."""
        log_content = """------------------------- alice ----------------------------
//depot/file1.cpp - edit - CL 12345 - alice_workspace
"""
        config_workspaces = ["alice_workspace", "bob_ws"]
        config_users = [
            {"AccountName": "alice", "Department": "VFX", "Email": "alice@test.com", "WorkSpace": "alice_workspace", "UserName": "Alice"},
            {"AccountName": "bob", "Department": "ENV", "Email": "bob@test.com", "WorkSpace": "bob_ws"}
        ]

        report_path = os.path.join(self.test_dir, "report.txt")
        result = self.gen.generate(
            report_path,
            log_content,
            config_workspaces,
            config_users,
            "VFX",
            "02:30 PM"
        )

        self.assertTrue(result)
        self.assertTrue(os.path.exists(report_path))

        with open(report_path, 'r') as f:
            content = f.read()
            self.assertIn("alice@test.com", content)
            self.assertIn("02:30 PM", content)

    def test_generate_report_no_matching_users(self):
        """Test generating report when no users match."""
        log_content = """------------------------- unknown ----------------------------
//depot/file.cpp - edit - CL 12345 - unknown_ws
"""
        config_workspaces = ["alice_workspace", "bob_ws"]
        config_users = []

        report_path = os.path.join(self.test_dir, "report.txt")
        result = self.gen.generate(
            report_path,
            log_content,
            config_workspaces,
            config_users,
            "VFX",
            "02:30 PM"
        )

        self.assertFalse(result)

    def test_send_to_teams_success_with_http_status(self):
        """Test successful Teams message send using HTTPStatus.ACCEPTED."""
        report_path = os.path.join(self.test_dir, "report.txt")
        with open(report_path, 'w') as f:
            f.write("Test report content")

        with patch('src.model.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = HTTPStatus.ACCEPTED  # 202
            mock_post.return_value = mock_response

            result = self.gen.send_to_teams(report_path, "https://webhook.com")

            self.assertTrue(result)
            mock_post.assert_called_once()
            self.log.info.assert_called_with("✅ Report sent to Teams successfully")

    def test_send_to_teams_failure_with_http_status(self):
        """Test failed Teams message send logs error."""
        report_path = os.path.join(self.test_dir, "report.txt")
        with open(report_path, 'w') as f:
            f.write("Test report content")

        with patch('src.model.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 400  # Bad request
            mock_response.text = "Invalid payload"
            mock_post.return_value = mock_response

            result = self.gen.send_to_teams(report_path, "https://webhook.com")

            self.assertFalse(result)
            self.log.error.assert_called()

    def test_send_to_teams_missing_file(self):
        """Test sending when report file doesn't exist."""
        result = self.gen.send_to_teams("/nonexistent/report.txt", "https://webhook.com")
        self.assertFalse(result)
        self.log.warning.assert_called()

    def test_send_to_teams_request_timeout(self):
        """Test Teams request timeout is handled."""
        report_path = os.path.join(self.test_dir, "report.txt")
        with open(report_path, 'w') as f:
            f.write("Test report content")

        with patch('src.model.requests.post') as mock_post:
            import requests
            mock_post.side_effect = requests.exceptions.Timeout("Connection timeout")

            result = self.gen.send_to_teams(report_path, "https://webhook.com")

            self.assertFalse(result)
            self.log.error.assert_called()


class TestModel(unittest.TestCase):
    """Test Model class."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.preset_name = "TEST_PRESET"
        self.preset_path = os.path.join(self.test_dir, "presets", self.preset_name)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_model_init_creates_preset(self):
        """Test Model initialization creates preset directory."""
        with patch('src.model.PRESET_DIR', os.path.join(self.test_dir, "presets")):
            with patch('src.model.setup_logger'):
                model = Model(self.preset_name)

                self.assertEqual(model.name, self.preset_name)
                self.assertTrue(os.path.exists(self.preset_path))

    def test_model_init_loads_config(self):
        """Test Model initialization loads config."""
        os.makedirs(self.preset_path)
        config = {
            "misc": [{"OutputLogAndReport": self.test_dir, "Webhook": "https://example.com"}],
            "info": [
                {"AccountName": "alice", "Department": "VFX", "Email": "alice@test.com", "WorkSpace": "alice_ws"}
            ]
        }
        config_path = os.path.join(self.preset_path, "config.json")
        with open(config_path, 'w') as f:
            json.dump(config, f)

        with patch('src.model.PRESET_DIR', os.path.join(self.test_dir, "presets")):
            with patch('src.model.setup_logger'):
                model = Model(self.preset_name)

                self.assertEqual(model.webhook, "https://example.com")
                self.assertEqual(model.accounts, ["alice"])
                self.assertEqual(model.workspaces, ["alice_ws"])

    def test_model_generate_log(self):
        """Test log generation."""
        os.makedirs(self.preset_path)
        config = {
            "misc": [{"OutputLogAndReport": self.test_dir, "Webhook": "https://example.com"}],
            "info": [{"AccountName": "alice", "Department": "VFX", "Email": "alice@test.com", "WorkSpace": "alice_ws"}]
        }
        config_path = os.path.join(self.preset_path, "config.json")
        with open(config_path, 'w') as f:
            json.dump(config, f)

        with patch('src.model.PRESET_DIR', os.path.join(self.test_dir, "presets")):
            with patch('src.model.setup_logger'):
                model = Model(self.preset_name)

                # Mock P4Manager
                model.p4_manager.get_opened_files = Mock(return_value=[
                    {"action": "edit", "depotFile": "//depot/file.cpp", "change": "12345", "client": "alice_ws"}
                ])

                result = model.generate_log()

                self.assertTrue(result)
                self.assertTrue(os.path.exists(model.output_log))

                with open(model.output_log, 'r') as f:
                    content = f.read()
                    self.assertIn("alice", content)
                    self.assertIn("file.cpp", content)

    def test_model_generate_log_atomic_write(self):
        """Test log generation uses atomic writes (no temp file left on success)."""
        os.makedirs(self.preset_path)
        config = {
            "misc": [{"OutputLogAndReport": self.test_dir, "Webhook": "https://example.com"}],
            "info": [{"AccountName": "alice", "Department": "VFX", "Email": "alice@test.com", "WorkSpace": "alice_ws"}]
        }
        config_path = os.path.join(self.preset_path, "config.json")
        with open(config_path, 'w') as f:
            json.dump(config, f)

        with patch('src.model.PRESET_DIR', os.path.join(self.test_dir, "presets")):
            with patch('src.model.setup_logger'):
                model = Model(self.preset_name)

                model.p4_manager.get_opened_files = Mock(return_value=[
                    {"action": "edit", "depotFile": "//depot/file.cpp", "change": "12345", "client": "alice_ws"}
                ])

                result = model.generate_log()

                self.assertTrue(result)
                # Verify no .tmp file left behind
                temp_path = Path(model.output_log).with_suffix('.tmp')
                self.assertFalse(temp_path.exists(), "Temp file should be cleaned up after successful write")

    def test_model_generate_log_temp_cleanup_on_error(self):
        """Test temp file is cleaned up even on write error."""
        os.makedirs(self.preset_path, exist_ok=True)
        os.makedirs(self.test_dir, exist_ok=True)  # Ensure output dir exists
        config = {
            "misc": [{"OutputLogAndReport": self.test_dir, "Webhook": "https://example.com"}],
            "info": [{"AccountName": "alice", "Department": "VFX", "Email": "alice@test.com", "WorkSpace": "alice_ws"}]
        }
        config_path = os.path.join(self.preset_path, "config.json")
        with open(config_path, 'w') as f:
            json.dump(config, f)

        with patch('src.model.PRESET_DIR', os.path.join(self.test_dir, "presets")):
            with patch('src.model.setup_logger'):
                model = Model(self.preset_name)

                # Mock P4Manager to raise an exception during file retrieval
                model.p4_manager.get_opened_files = Mock(side_effect=IOError("Permission denied"))

                result = model.generate_log()

                self.assertFalse(result)  # Should fail due to exception
                # Verify no orphaned temp files
                temp_path = Path(model.output_log).with_suffix('.tmp')
                self.assertFalse(temp_path.exists(), "Temp file should be cleaned up on error")


if __name__ == '__main__':
    unittest.main()
