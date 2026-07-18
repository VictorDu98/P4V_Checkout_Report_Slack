"""Preset validator - validates presets before scheduling using real test rules."""

import os
import json
import logging
from typing import List, Tuple, Optional
from src.model import PresetConfig


class PresetValidator:
    """Validates preset configurations against test rules."""

    def __init__(self, log: logging.Logger):
        self.log = log

    def validate_preset(self, preset_name: str, preset_path: str) -> Tuple[bool, List[str]]:
        """
        Validate a preset against all test rules.

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Rule 1: config.json exists
        if not self._check_config_exists(preset_path):
            errors.append(f"Missing config.json in {preset_name}")
            return False, errors

        # Rule 2: valid JSON syntax
        if not self._check_valid_json(preset_path):
            errors.append(f"Invalid JSON in {preset_name}/config.json")
            return False, errors

        # Rule 3: required fields exist
        field_errors = self._check_required_fields(preset_path, preset_name)
        if field_errors:
            errors.extend(field_errors)

        # Rule 4: output directory is valid
        output_errors = self._check_output_directory(preset_path, preset_name)
        if output_errors:
            errors.extend(output_errors)

        # Rule 5: webhook URL is valid
        webhook_errors = self._check_webhook_url(preset_path, preset_name)
        if webhook_errors:
            errors.extend(webhook_errors)

        # Rule 6: user fields exist
        user_errors = self._check_user_fields(preset_path, preset_name)
        if user_errors:
            errors.extend(user_errors)

        return len(errors) == 0, errors

    def _check_config_exists(self, preset_path: str) -> bool:
        """Check that config.json exists."""
        config_path = os.path.join(preset_path, "config.json")
        return os.path.exists(config_path)

    def _check_valid_json(self, preset_path: str) -> bool:
        """Check that config.json has valid JSON syntax."""
        config_path = os.path.join(preset_path, "config.json")
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                json.load(f)
            return True
        except (json.JSONDecodeError, IOError):
            return False

    def _check_required_fields(self, preset_path: str, preset_name: str) -> List[str]:
        """Check that all required fields exist in config."""
        errors = []
        try:
            preset_config = PresetConfig(preset_path, self.log)
            preset_config.load()

            # Check output root
            try:
                preset_config.get_output_root()
            except (KeyError, IndexError):
                errors.append(f"{preset_name}: Missing or invalid 'misc.OutputLogAndReport'")

            # Check webhook
            try:
                preset_config.get_webhook()
            except (KeyError, IndexError):
                errors.append(f"{preset_name}: Missing or invalid 'misc.Webhook'")

            # Check accounts
            try:
                accounts = preset_config.get_accounts()
                if not accounts:
                    errors.append(f"{preset_name}: No accounts found in 'info' array")
            except (KeyError, TypeError):
                errors.append(f"{preset_name}: Invalid 'info' section")

            # Check workspaces
            try:
                preset_config.get_workspaces()
            except (KeyError, TypeError):
                errors.append(f"{preset_name}: Missing 'WorkSpace' field in info entries")

            # Check departments
            try:
                preset_config.get_departments()
            except (KeyError, TypeError):
                errors.append(f"{preset_name}: Missing 'Department' field in info entries")

        except Exception as e:
            errors.append(f"{preset_name}: Unexpected error: {e}")

        return errors

    def _check_output_directory(self, preset_path: str, preset_name: str) -> List[str]:
        """Check that output directory path is valid."""
        errors = []
        try:
            preset_config = PresetConfig(preset_path, self.log)
            preset_config.load()
            output_root = preset_config.get_output_root()

            # Check for placeholder
            if output_root == "Output address to store logs and report":
                errors.append(f"{preset_name}: OutputLogAndReport is still a placeholder")
            # Check for absolute path
            elif not os.path.isabs(output_root) and not output_root.startswith('/'):
                errors.append(f"{preset_name}: OutputLogAndReport is not absolute: {output_root}")

        except Exception as e:
            errors.append(f"{preset_name}: Output directory check failed: {e}")

        return errors

    def _check_webhook_url(self, preset_path: str, preset_name: str) -> List[str]:
        """Check that webhook URL is valid format."""
        errors = []
        try:
            preset_config = PresetConfig(preset_path, self.log)
            preset_config.load()
            webhook = preset_config.get_webhook()

            # Check for placeholder
            if webhook == "Microsoft Teams Workflow incoming webhook":
                errors.append(f"{preset_name}: Webhook is still a placeholder")
            # Check for valid URL format
            elif not (webhook.startswith('http://') or webhook.startswith('https://')):
                errors.append(f"{preset_name}: Webhook is not valid URL format: {webhook}")

        except Exception as e:
            errors.append(f"{preset_name}: Webhook check failed: {e}")

        return errors

    def _check_user_fields(self, preset_path: str, preset_name: str) -> List[str]:
        """Check that all user entries have required fields."""
        errors = []
        try:
            config_path = os.path.join(preset_path, "config.json")
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            for idx, user in enumerate(config.get('info', [])):
                if 'Email' not in user:
                    errors.append(f"{preset_name}: User {idx} missing 'Email' field")
                if 'AccountName' not in user:
                    errors.append(f"{preset_name}: User {idx} missing 'AccountName' field")

        except Exception as e:
            errors.append(f"{preset_name}: User field check failed: {e}")

        return errors
