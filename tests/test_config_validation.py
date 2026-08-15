import unittest
import os
import sys
import csv
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.model import PresetConfig


class TestConfigFilesValidation(unittest.TestCase):
    """Scan and validate all config.csv files in src/presets/"""

    PRESETS_DIR = os.path.join(os.path.dirname(__file__), '..', 'src', 'presets')

    def get_all_presets(self):
        """Get list of all preset directories."""
        if not os.path.exists(self.PRESETS_DIR):
            return []

        presets = []
        for item in os.listdir(self.PRESETS_DIR):
            item_path = os.path.join(self.PRESETS_DIR, item)
            if os.path.isdir(item_path):
                presets.append((item, item_path))

        return sorted(presets)

    def test_all_config_files_exist(self):
        """Test that all presets have config.csv files."""
        presets = self.get_all_presets()

        if not presets:
            self.skipTest("No presets found in src/presets/")

        missing_configs = []
        for preset_name, preset_path in presets:
            config_path = os.path.join(preset_path, "config.csv")
            if not os.path.exists(config_path):
                missing_configs.append(preset_name)

        if missing_configs:
            self.fail(f"The following presets are missing config.csv: {missing_configs}")

    def test_all_config_files_valid_csv(self):
        """Test that all config.csv files have valid CSV syntax."""
        presets = self.get_all_presets()

        if not presets:
            self.skipTest("No presets found in src/presets/")

        invalid_configs = {}
        for preset_name, preset_path in presets:
            config_path = os.path.join(preset_path, "config.csv")
            if not os.path.exists(config_path):
                continue

            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for _ in reader:
                        pass  # Just read through to verify CSV is valid
            except Exception as e:
                invalid_configs[preset_name] = str(e)

        if invalid_configs:
            error_msg = "The following configs have invalid CSV:\n"
            for preset, error in invalid_configs.items():
                error_msg += f"  - {preset}: {error}\n"
            self.fail(error_msg)

    def test_all_config_files_have_required_fields(self):
        """Test that all config.csv files have required fields."""
        presets = self.get_all_presets()

        if not presets:
            self.skipTest("No presets found in src/presets/")

        errors = {}
        for preset_name, preset_path in presets:
            config_path = os.path.join(preset_path, "config.csv")
            if not os.path.exists(config_path):
                continue

            try:
                preset_config = PresetConfig(preset_path)
                preset_config.load()

                # Check required sections and fields
                preset_errors = []

                # Test misc section
                try:
                    output_root = preset_config.get_output_root()
                except (KeyError, IndexError) as e:
                    preset_errors.append(f"Missing or invalid 'misc.OutputLogAndReport': {e}")

                try:
                    webhook = preset_config.get_webhook()
                except (KeyError, IndexError) as e:
                    preset_errors.append(f"Missing or invalid 'misc.Webhook': {e}")

                # Test info section
                try:
                    accounts = preset_config.get_accounts()
                    if not accounts:
                        preset_errors.append("No accounts found in 'info' array")
                except (KeyError, TypeError) as e:
                    preset_errors.append(f"Invalid 'info' section: {e}")

                try:
                    workspaces = preset_config.get_workspaces()
                except (KeyError, TypeError) as e:
                    preset_errors.append(f"Missing 'WorkspaceName' field in info entries: {e}")

                try:
                    department = preset_config.get_department()
                except (KeyError, TypeError) as e:
                    preset_errors.append(f"Missing 'Department' in misc section: {e}")

                try:
                    schedule_time = preset_config.get_schedule_time()
                except (KeyError, TypeError) as e:
                    preset_errors.append(f"Missing 'Schedule Time' in misc section: {e}")

                if preset_errors:
                    errors[preset_name] = preset_errors

            except Exception as e:
                errors[preset_name] = [f"Unexpected error: {e}"]

        if errors:
            error_msg = "The following configs have validation errors:\n"
            for preset, preset_errors in errors.items():
                error_msg += f"  {preset}:\n"
                for error in preset_errors:
                    error_msg += f"    - {error}\n"
            self.fail(error_msg)

    def test_output_directories_exist(self):
        """Test that all configured output directories exist or are creatable."""
        presets = self.get_all_presets()

        if not presets:
            self.skipTest("No presets found in src/presets/")

        issues = {}
        for preset_name, preset_path in presets:
            config_path = os.path.join(preset_path, "config.json")
            if not os.path.exists(config_path):
                continue

            try:
                preset_config = PresetConfig(preset_path)
                preset_config.load()
                output_root = preset_config.get_output_root()

                # Check if path is absolute and not a placeholder
                if output_root == "Output address to store logs and report":
                    issues[preset_name] = "OutputLogAndReport is still a placeholder"
                elif not os.path.isabs(output_root) and not output_root.startswith('/'):
                    issues[preset_name] = f"OutputLogAndReport is not absolute: {output_root}"

            except Exception as e:
                issues[preset_name] = str(e)

        if issues:
            error_msg = "The following presets have output path issues:\n"
            for preset, issue in issues.items():
                error_msg += f"  - {preset}: {issue}\n"
            self.fail(error_msg)

    def test_webhook_urls_valid_format(self):
        """Test that webhook URLs are valid format."""
        presets = self.get_all_presets()

        if not presets:
            self.skipTest("No presets found in src/presets/")

        issues = {}
        for preset_name, preset_path in presets:
            config_path = os.path.join(preset_path, "config.json")
            if not os.path.exists(config_path):
                continue

            try:
                preset_config = PresetConfig(preset_path)
                preset_config.load()
                webhook = preset_config.get_webhook()

                # Check if placeholder
                if webhook == "Microsoft Teams Workflow incoming webhook":
                    issues[preset_name] = "Webhook is still a placeholder"
                # Check if valid URL format
                elif not (webhook.startswith('http://') or webhook.startswith('https://')):
                    issues[preset_name] = f"Webhook is not valid URL format: {webhook}"

            except Exception as e:
                issues[preset_name] = str(e)

        if issues:
            error_msg = "The following presets have webhook issues:\n"
            for preset, issue in issues.items():
                error_msg += f"  - {preset}: {issue}\n"
            self.fail(error_msg)

    def test_email_fields_exist_when_needed(self):
        """Test that user entries have Email field."""
        presets = self.get_all_presets()

        if not presets:
            self.skipTest("No presets found in src/presets/")

        issues = {}
        for preset_name, preset_path in presets:
            config_path = os.path.join(preset_path, "config.json")
            if not os.path.exists(config_path):
                continue

            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                preset_issues = []
                for idx, user in enumerate(config.get('info', [])):
                    if 'Email' not in user:
                        preset_issues.append(f"User {idx} missing 'Email' field")
                    if 'AccountName' not in user:
                        preset_issues.append(f"User {idx} missing 'AccountName' field")

                if preset_issues:
                    issues[preset_name] = preset_issues

            except Exception as e:
                issues[preset_name] = [str(e)]

        if issues:
            error_msg = "The following presets have user field issues:\n"
            for preset, preset_issues in issues.items():
                error_msg += f"  {preset}:\n"
                for issue in preset_issues:
                    error_msg += f"    - {issue}\n"
            self.fail(error_msg)

    def test_print_config_summary(self):
        """Print summary of all found configs (informational)."""
        presets = self.get_all_presets()

        if not presets:
            print("\nNo presets found in src/presets/")
            return

        print(f"\nFound {len(presets)} preset(s):")
        print("=" * 70)

        for preset_name, preset_path in presets:
            config_path = os.path.join(preset_path, "config.json")

            if not os.path.exists(config_path):
                print(f"\nError: {preset_name}")
                print("   - Missing: config.csv")
                continue

            try:
                preset_config = PresetConfig(preset_path)
                preset_config.load()

                print(f"\n{preset_name}")
                print(f"   - Output: {preset_config.get_output_root()}")
                print(f"   - Webhook: {preset_config.get_webhook()[:50]}...")

                accounts = preset_config.get_accounts()
                print(f"   - Accounts: {len(accounts)} ({', '.join(accounts[:3])}{'...' if len(accounts) > 3 else ''})")

                department = preset_config.get_department()
                schedule_time = preset_config.get_schedule_time()
                print(f"   - Department: {department}")
                print(f"   - Schedule Time: {schedule_time}")

            except Exception as e:
                print(f"\nError: {preset_name}")
                print(f"   - Error: {e}")

        print("\n" + "=" * 70)


if __name__ == '__main__':
    unittest.main()
