import os
import sys
import shutil
import requests
import csv
import re
import random
import time
import logging
import getpass
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from pathlib import Path
from http import HTTPStatus
from P4 import P4, P4Exception
from src.logger import setup_logger
from src.preset_validator import PresetValidator


ROOT_DIR: str = os.path.dirname(os.path.realpath(__file__))
PRESET_DIR: str = os.path.join(ROOT_DIR, "presets")




class PresetConfig:
    """Handle preset configuration loading and management."""

    def __init__(self, preset_root: str, log: Optional[logging.Logger] = None) -> None:
        self.preset_root = preset_root
        self.config_path = os.path.join(preset_root, "config.csv")
        self.p4config_path = os.path.join(preset_root, ".p4config")
        self.config: Dict[str, Any] = {}
        self.log = log or logging.getLogger(__name__)
        self.log.debug(f"PresetConfig initialized for: {preset_root}")

    def load(self) -> None:
        """Load configuration from config.csv."""
        self.log.debug(f"Loading config from: {self.config_path}")

        if not os.path.exists(self.config_path):
            self.log.error(f"Config file not found: {self.config_path}")
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        try:
            self.config = self._parse_csv()

            # Validate required fields
            try:
                self.get_output_root()
                self.get_webhook()
            except KeyError as e:
                self.log.error(f"Missing required field in config: {e}")
                raise

            user_count = len(self.config.get('info', []))
            self.log.info(f"Config loaded successfully with {user_count} user(s)")
        except KeyError:
            raise
        except Exception as e:
            self.log.error(f"Failed to read {self.config_path}: {e}")
            raise IOError(f"Failed to read {self.config_path}: {e}")

    def _parse_csv(self) -> Dict[str, Any]:
        """Parse CSV file into config dictionary."""
        config = {"misc": [], "info": []}

        with open(self.config_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)

        current_section = None
        headers = None

        for row in rows:
            # Skip empty rows
            if not row or not row[0].strip():
                continue

            first_col = row[0].strip()

            # Check for section headers
            if first_col == "Miscellaneous":
                current_section = "misc"
                headers = None
                continue

            if first_col == "User info":
                current_section = "info"
                headers = None
                continue

            # For info section, first non-empty row after header is column names
            if current_section == "info" and headers is None:
                headers = [col.strip() for col in row if col.strip()]
                continue

            # Parse data rows
            if current_section == "misc" and len(row) >= 2:
                # Misc section: key in first column, value in second
                key = first_col
                value = row[1].strip() if len(row) > 1 else ""
                if key and value:  # Only add non-empty entries
                    config["misc"].append({key: value})

            elif current_section == "info" and headers:
                # Info section: use headers as keys
                user_data = {}
                for idx, header in enumerate(headers):
                    value = row[idx].strip() if idx < len(row) else ""
                    if value:  # Only add non-empty values
                        user_data[header] = value

                if user_data.get("AccountName"):  # Only add if AccountName exists
                    config["info"].append(user_data)

        return config

    def _get_misc_value(self, key: str) -> str:
        """Get value from misc section by key."""
        for entry in self.config.get("misc", []):
            if key in entry:
                return entry[key]
        raise KeyError(f"Missing '{key}' in misc section")

    def get_output_root(self) -> str:
        """Get output directory from config."""
        self.log.debug("Retrieving output root directory")
        try:
            output_root = self._get_misc_value("OutputLogAndReport")
            self.log.debug(f"Output root: {output_root}")
            return output_root
        except KeyError as e:
            self.log.error(f"{e}")
            raise KeyError(f"Missing 'OutputLogAndReport' in config: {e}")

    def get_webhook(self) -> str:
        """Get webhook URL from config."""
        self.log.debug("Retrieving webhook URL")
        try:
            webhook = self._get_misc_value("Webhook")
            self.log.debug("Webhook retrieved successfully")
            return webhook
        except KeyError as e:
            self.log.error(f"{e}")
            raise KeyError(f"Missing 'Webhook' in config: {e}")

    def get_accounts(self) -> List[str]:
        """Get list of P4 account names."""
        self.log.debug("Retrieving account names")
        accounts = []
        try:
            for entry in self.config.get("info", []):
                if "AccountName" in entry:
                    accounts.append(entry["AccountName"])
            self.log.debug(f"Found {len(accounts)} account(s): {accounts}")
        except Exception as e:
            self.log.error(f"Error retrieving account names: {e}")
            raise KeyError(f"Error retrieving account names: {e}")
        return accounts

    def get_workspaces(self) -> List[str]:
        """Get list of workspace names."""
        self.log.debug("Retrieving workspace names")
        workspaces = []
        try:
            for entry in self.config.get("info", []):
                if "WorkspaceName" in entry:
                    workspaces.append(entry["WorkspaceName"])
            self.log.debug(f"Found {len(workspaces)} workspace(s)")
        except Exception as e:
            self.log.error(f"Error retrieving workspace names: {e}")
            raise KeyError(f"Error retrieving workspace names: {e}")
        return workspaces

    def get_department(self) -> str:
        """Get department from config (misc section)."""
        self.log.debug("Retrieving department")
        try:
            department = self._get_misc_value("Department")
            self.log.debug(f"Department: {department}")
            return department
        except KeyError as e:
            self.log.error(f"{e}")
            raise KeyError(f"Missing 'Department' in misc section: {e}")

    def get_schedule_time(self) -> str:
        """Get schedule time from config (misc section)."""
        self.log.debug("Retrieving schedule time")
        try:
            schedule_time = self._get_misc_value("Schedule Time")
            self.log.debug(f"Schedule time: {schedule_time}")
            return schedule_time
        except KeyError as e:
            self.log.error(f"{e}")
            raise KeyError(f"Missing 'Schedule Time' in misc section: {e}")

    def get_user_by_index(self, index: int) -> Dict[str, Any]:
        """Get user info by index."""
        self.log.debug(f"Retrieving user at index {index}")
        try:
            user = self.config["info"][index]
            self.log.debug(f"Retrieved user: {user.get('AccountName', 'unknown')}")
            return user
        except (IndexError, KeyError) as e:
            self.log.error(f"Invalid user index {index}: {e}")
            raise IndexError(f"Invalid user index {index}: {e}")

    def create_template(self) -> None:
        """Create template configuration files."""
        self.log.info(f"Creating template files in: {self.preset_root}")

        csv_content = [
            ["Miscellaneous", "", "", ""],
            ["OutputLogAndReport", "Output address to store logs and report", "", ""],
            ["Webhook", "Microsoft Teams Workflow incoming webhook", "", ""],
            ["Schedule Time", "18:30", "", ""],
            ["Department", "ENV", "", ""],
            ["", "", "", ""],
            ["User info", "", "", ""],
            ["AccountName", "UserName(Optional)", "Hostname(Optional)", "WorkspaceName", "Email"],
            ["Artist P4 account name", "User real name - optional and can excluded in config", "Workstation name", "Artist P4V workspace name", "Artist @virtuosgames.com"],
            ["Artist P4 account name", "", "", "Artist P4V workspace name", ""]
        ]

        try:
            self.log.debug(f"Writing config template to: {self.config_path}")
            with open(self.config_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(csv_content)
            self.log.info(f"Config template created: {self.config_path}")
        except IOError as e:
            self.log.error(f"Failed to write {self.config_path}: {e}")
            raise IOError(f"Failed to write {self.config_path}: {e}")

        p4config_content = """P4PORT= "perforce:1666"
P4USER= "p4user"
P4CHARSET= "utf8"
P4CLIENT="p4client"
"""

        try:
            self.log.debug(f"Writing P4 config template to: {self.p4config_path}")
            with open(self.p4config_path, 'w', encoding='utf-8') as f:
                f.write(p4config_content)
            self.log.info(f"P4 config template created: {self.p4config_path}")
        except IOError as e:
            self.log.error(f"Failed to write {self.p4config_path}: {e}")
            raise IOError(f"Failed to write {self.p4config_path}: {e}")


class P4Manager:
    """Handle all P4Python operations."""

    def __init__(self, preset_root: str, log: logging.Logger) -> None:
        self.preset_root = preset_root
        self.p4ticket_path = os.path.join(preset_root, ".p4ticket")
        self.p4config_path = os.path.join(preset_root, ".p4config")
        self.p4: Optional[P4] = None
        self.log = log

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit — ensures P4 disconnects."""
        self.disconnect()
        return False

    def initialize(self, preset_name: str) -> bool:
        """Initialize P4 connection. Returns True if successful."""
        self.log.info(f"Initializing P4 connection for preset: {preset_name}")
        self.log.debug(f"P4 config path: {self.p4config_path}")
        self.log.debug(f"P4 ticket path: {self.p4ticket_path}")

        try:
            self.log.debug(f"Setting P4CONFIG environment variable")
            os.system(f"p4 set P4CONFIG={self.p4config_path}")

            if not os.path.exists(self.p4ticket_path):
                self.log.info(f"Ticket not found, creating new one")
                return self._create_ticket(preset_name)

            self.log.info(f"Using existing ticket")
            return self._connect_with_ticket()

        except Exception as e:
            self.log.error(f"Failed to initialize P4: {e}", exc_info=True)
            self.p4 = None
            return False

    def _create_ticket(self, preset_name: str) -> bool:
        """Create new P4 ticket via login. Returns True if successful."""
        self.log.info(f"Creating new P4 ticket for {preset_name}")
        self.p4 = P4()
        retries = 3

        while retries > 0:
            try:
                self.p4.ticket_file = self.p4ticket_path
                self.log.debug(f"Prompting for P4 password (attempt {4 - retries}/3)")

                password = getpass.getpass(f"Enter P4 password for {preset_name}: ")
                self.p4.password = password

                self.log.debug(f"Connecting to P4 server")
                if not self.p4.connected():
                    self.p4.connect()

                self.log.debug(f"Logging in to P4")
                self.p4.run_login()
                self.log.info(f"✅ P4 ticket created successfully for {preset_name}")
                return True

            except P4Exception as e:
                retries -= 1
                self.log.warning(f"P4 login failed (retries left: {retries}): {e}")
                if retries == 0:
                    self.log.error(f"❌ P4 login failed after 3 attempts")
                    self.p4 = None
                    return False

    def _connect_with_ticket(self) -> bool:
        """Connect using existing ticket. Returns True if successful."""
        self.log.info(f"Connecting to P4 with existing ticket")
        self.log.debug(f"Ticket file: {self.p4ticket_path}")

        try:
            self.p4 = P4()
            self.p4.ticket_file = self.p4ticket_path

            self.log.debug(f"Connecting to P4 server")
            if not self.p4.connected():
                self.p4.connect()

            # Test connection
            self.log.debug(f"Testing connection with p4 opened command")
            self.p4.run_opened()
            self.log.info(f"✅ P4 connected successfully with ticket")
            return True

        except P4Exception as e:
            self.log.error(f"❌ Failed to connect P4: {e}")
            self.p4 = None
            return False
        except Exception as e:
            self.log.error(f"❌ Unexpected error connecting P4: {e}", exc_info=True)
            self.p4 = None
            return False

    def get_opened_files(self, account: str) -> List[Dict[str, str]]:
        """Get files opened by a specific account."""
        self.log.debug(f"Getting opened files for account: {account}")

        if not self.p4 or not self.p4.connected():
            self.log.warning(f"P4 not connected, cannot get opened files for {account}")
            return []

        try:
            self.log.debug(f"Executing 'p4 opened -u {account}'")
            files = self.p4.run_opened("-u", account)

            if files:
                self.log.info(f"Found {len(files)} file(s) opened by {account}")
                for file_info in files:
                    self.log.debug(f"  - {file_info.get('depotFile', 'unknown')} ({file_info.get('action', 'unknown')})")
            else:
                self.log.debug(f"No files opened by {account}")

            return files if files else []

        except P4Exception as e:
            self.log.error(f"Failed to get opened files for {account}: {e}")
            return []

    def disconnect(self) -> None:
        """Safely disconnect from P4."""
        self.log.debug(f"Disconnecting from P4")

        if self.p4:
            try:
                self.p4.disconnect()
                self.log.info(f"P4 disconnected successfully")
            except Exception as e:
                self.log.warning(f"Error disconnecting P4: {e}")
        else:
            self.log.debug(f"P4 not initialized, nothing to disconnect")


class ReportGenerator:
    """Handle report generation and Teams message sending."""

    WORKSPACE_PATTERN = re.compile(r"^.+ - edit - CL (\d+|default) - ([A-Za-z0-9._]+)")

    def __init__(self, log: Optional[logging.Logger] = None) -> None:
        self.log = log or logging.getLogger(__name__)
        self.log.debug("ReportGenerator initialized")

    @classmethod
    def trace_workspace(cls, lines: List[str]) -> List[str]:
        """Extract workspace names from log lines."""
        logger = logging.getLogger(__name__)
        logger.debug(f"Tracing workspaces from {len(lines)} lines")

        workspaces: List[str] = []

        for line in lines:
            match = cls.WORKSPACE_PATTERN.match(line.strip())
            if match:
                workspace = match.group(2)
                if workspace not in workspaces:
                    workspaces.append(workspace)
                    logger.debug(f"Found workspace: {workspace}")

        logger.info(f"Traced {len(workspaces)} unique workspace(s)")
        return workspaces

    @staticmethod
    def find_matching_users(found_workspaces: List[str], config_workspaces: List[str]) -> List[int]:
        """Find indices of matching workspaces in config."""
        logger = logging.getLogger(__name__)
        logger.debug(f"Matching {len(found_workspaces)} found workspace(s) against {len(config_workspaces)} config workspace(s)")

        user_indices: List[int] = []

        for found in found_workspaces:
            for idx, config in enumerate(config_workspaces):
                if re.match(found, config):
                    user_indices.append(idx)
                    logger.debug(f"Matched workspace '{found}' to config index {idx}")
                    break  # Match each found workspace only once

        logger.info(f"Found {len(user_indices)} matching user(s)")
        return user_indices

    def generate(
        self,
        output_path: str,
        log_content: str,
        log_path:str,
        config_workspaces: List[str],
        config_users: List[Dict[str, Any]],
        department: str,
        timestamp: str
    ) -> bool:
        """Generate report file. Returns True if successful."""
        self.log.info(f"Generating report for department: {department}")
        self.log.debug(f"Output path: {output_path}")

        try:
            lines = [line.strip() for line in log_content.split('\n')]
            self.log.debug(f"Processing {len(lines)} lines from log content")

            found_workspaces = self.trace_workspace(lines)

            if not found_workspaces:
                self.log.info(f"No users found for department {department}")
                return False

            user_indices = self.find_matching_users(found_workspaces, config_workspaces)
            if not user_indices:
                self.log.warning(f"No matching users for department {department}")
                return False

            self.log.debug(f"Writing report with {len(user_indices)} user(s)")

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"Các bạn này đang checkout file P4V vào lúc {timestamp} 🚨<br><br>")

                users_written = 0
                for idx, user_idx in enumerate(user_indices):
                    try:
                        user = config_users[user_idx]

                        if user.get("UserName") is None:
                            user_entry = f"<at>{user['Email']}</at>"
                        else:
                            user_entry = f"<at>{user['Email']}</at> - {user.get('UserName')} - {user.get('WorkspaceName')}"

                        f.write(user_entry)
                        users_written += 1
                        self.log.debug(f"Wrote user entry for {user.get('AccountName', 'unknown')}")

                        if idx < len(user_indices) - 1:
                            f.write("<br>")

                    except (KeyError, IndexError) as e:
                        self.log.warning(f"Error processing user {user_idx}: {e}")
                        continue

                # Add log file reference
                f.write(f"<br><br>Vào đây xem log để biết file nào đang checkout nè:<br>{log_path}")

            self.log.info(f"Report generated successfully: {output_path} ({users_written} user(s))")
            return True

        except Exception as e:
            self.log.error(f"Failed to generate report: {e}", exc_info=True)
            return False

    def send_to_teams(self, report_path: str, webhook: str) -> bool:
        """Send report to Teams via webhook. Returns True if successful."""
        self.log.info(f"Sending report to Teams: {report_path}")
        self.log.debug(f"Webhook: {webhook[:50]}...")

        if not os.path.exists(report_path):
            self.log.warning(f"Report file not found: {report_path}")
            return False

        try:
            self.log.debug(f"Reading report file: {report_path}")
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.log.debug(f"Report content size: {len(content)} bytes")

            payload = {"text": content}
            self.log.debug("Sending POST request to Teams webhook")

            response = requests.post(
                webhook,
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )

            self.log.debug(f"Teams API response code: {response.status_code}")

            if response.status_code == HTTPStatus.ACCEPTED:
                self.log.info("✅ Report sent to Teams successfully")
                return True
            else:
                self.log.error(f"❌ Teams API returned {response.status_code}: {response.text}")
                return False

        except requests.exceptions.Timeout as e:
            self.log.error(f"Request timeout sending to Teams: {e}")
            return False
        except requests.exceptions.RequestException as e:
            self.log.error(f"Failed to send request to Teams: {e}")
            return False
        except Exception as e:
            self.log.error(f"Failed to send report to Teams: {e}", exc_info=True)
            return False


class Model:
    """
    Orchestrates P4 integration with Microsoft Teams.

    Delegates to:
    - PresetConfig: Configuration loading
    - P4Manager: Perforce operations
    - ReportGenerator: Report generation and posting
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self.preset_root = os.path.join(PRESET_DIR, name)

        # Ensure preset directory exists
        if not os.path.exists(self.preset_root):
            os.makedirs(self.preset_root, exist_ok=True)

            # Create template config
            config = PresetConfig(self.preset_root)
            config.create_template()

        # Load configuration
        self.config = PresetConfig(self.preset_root)
        try:
            self.config.load()
        except (FileNotFoundError, ValueError, KeyError) as e:
            raise RuntimeError(f"Failed to load config for preset {name}: {e}")

        # Extract config values
        try:
            self.output_root = self.config.get_output_root()
            self.webhook = self.config.get_webhook()
            self.accounts = self.config.get_accounts()
            self.workspaces = self.config.get_workspaces()
            self.department = self.config.get_department()
            self.schedule_time = self.config.get_schedule_time()
        except KeyError as e:
            raise RuntimeError(f"Invalid configuration: {e}")

        # Ensure output directory exists
        os.makedirs(self.output_root, exist_ok=True)

        # Setup logger
        self.log = setup_logger(self.name, self.output_root)

        # Initialize components
        self.p4_manager = P4Manager(self.preset_root, self.log)
        self.report_gen = ReportGenerator(self.log)

        # Lazy-load log path
        self._output_log: Optional[str] = None

    def __str__(self) -> str:
        return self.name

    @property
    def output_log(self) -> str:
        """Get log file path (lazy-loaded)."""
        if self._output_log is None:
            self._output_log = os.path.join(
                self.output_root,
                f"log_{self.name}_{self.get_date()}.txt"
            )
        return self._output_log

    @staticmethod
    def get_date() -> str:
        """Get current date in YYMMDD format."""
        return datetime.now().strftime("%y%m%d")

    @staticmethod
    def get_time() -> str:
        """Get current time in HH:MM AM/PM (UTC+7)."""
        utc_plus_7 = timezone(timedelta(hours=7))
        return datetime.now(utc_plus_7).strftime("%I:%M %p")

    def generate_log(self) -> bool:
        """Generate log of opened files. Returns True if successful."""
        self.log.info(f"Generating log for {len(self.accounts)} account(s)")
        self.log.debug(f"Log file: {self.output_log}")

        log_path = Path(self.output_log)
        temp_path = log_path.with_suffix('.tmp')

        try:
            # Write to temp file first (atomic operation)
            self.log.debug(f"Writing to temp file: {temp_path}")

            with open(temp_path, 'w', encoding='utf-8') as f:
                all_found = False
                total_files = 0

                for account in self.accounts:
                    self.log.debug(f"Processing account: {account}")
                    files = self.p4_manager.get_opened_files(account)

                    if not files:
                        self.log.debug(f"No files found for {account}")
                        continue

                    all_found = True
                    f.write(f"------------------------- {account} ----------------------------\n")

                    for file_entry in files:
                        if file_entry.get("action") == "edit":
                            depot_file = file_entry.get("depotFile", "unknown")
                            changelist = file_entry.get("change", "unknown")
                            client = file_entry.get("client", "unknown")
                            f.write(f"{depot_file} - edit - CL {changelist} - {client}\n")
                            total_files += 1

                    f.write("\n")

            # Atomic rename
            self.log.debug(f"Atomically renaming temp file to: {log_path}")
            temp_path.replace(log_path)

            if all_found:
                self.log.info(f"✅ Log generated successfully: {len(self.accounts)} account(s), {total_files} file(s)")
            else:
                self.log.info("⚠️  No opened files found for any account")

            return all_found

        except IOError as e:
            self.log.error(f"Failed to write to log file: {e}")
            if temp_path.exists():
                self.log.debug(f"Cleaning up temp file: {temp_path}")
                temp_path.unlink()
            return False

        except Exception as e:
            self.log.error(f"Unexpected error generating log: {e}", exc_info=True)
            if temp_path.exists():
                self.log.debug(f"Cleaning up temp file on error: {temp_path}")
                temp_path.unlink()
            return False

    def generate_reports(self) -> bool:
        """Generate and send report for the configured department. Returns True if successful."""
        self.log.info(f"Generating report for department: {self.department}")

        try:
            if not os.path.exists(self.output_log):
                self.log.warning("Log file not found, skipping report")
                return False

            self.log.debug(f"Reading log file: {self.output_log}")
            with open(self.output_log, 'r', encoding='utf-8') as f:
                log_content = f.read()
            self.log.debug(f"Log file size: {len(log_content)} bytes")

            report_path = os.path.join(
                self.output_root,
                f"report_{self.department}_{self.get_date()}.txt"
            )

            # Remove old report if exists
            if os.path.exists(report_path):
                self.log.info(f"Removing old report: {report_path}")
                os.remove(report_path)

            # Generate report
            self.log.debug(f"Generating report for {self.department}")
            if self.report_gen.generate(
                output_path=report_path,
                log_content=log_content,
                log_path=self.output_log,
                config_workspaces=self.workspaces,
                config_users=self.config.config.get("info", []),
                department=self.department,
                timestamp=self.get_time()
            ):
                self.log.debug(f"Report generated, sending to Teams")

                # Send to Teams
                if self.report_gen.send_to_teams(report_path, self.webhook):
                    self.log.info(f"✅ Report generated and sent for {self.department}")
                    return True
                else:
                    self.log.warning(f"Failed to send report for {self.department}")
                    return False
            else:
                self.log.warning(f"Failed to generate report for {self.department}")
                return False

        except Exception as e:
            self.log.error(f"Unexpected error generating reports: {e}", exc_info=True)
            return False

    def validate_config(self) -> bool:
        """Validate preset configuration using PresetValidator. Returns True if valid."""

        self.log.info(f"\n📋 Validating configuration...")

        validator = PresetValidator(self.log)
        is_valid, errors = validator.validate_preset(self.name, self.preset_root)

        if not is_valid:
            self.log.error(f"❌ Configuration validation failed:")
            for error in errors:
                self.log.error(f"   - {error}")
            return False

        self.log.info(f"✅ Configuration validation passed")
        return True

    def run(self) -> bool:
        """Execute the full workflow. Returns True if successful."""
        self.log.info(f"=" * 70)
        self.log.info(f"🚀 Starting job for preset: {self.name}")
        self.log.info(f"=" * 70)

        # Step 0: Validate configuration
        self.log.info(f"\n📋 Step 0: Validating configuration...")
        if not self.validate_config():
            self.log.warning("❌ Configuration validation failed, job skipped")
            return False

        try:
            # Initialize P4
            self.log.info(f"\n📋 Step 1: Initializing P4 connection...")
            if not self.p4_manager.initialize(self.name):
                self.log.warning("❌ P4 initialization failed, job skipped")
                return False

            # Generate log of opened files
            self.log.info(f"\n📋 Step 2: Generating log of opened files...")
            if not self.generate_log():
                self.log.error("❌ Failed to generate log")
                return False

            # Generate and send reports
            self.log.info(f"\n📋 Step 3: Generating and sending reports...")
            if not self.generate_reports():
                self.log.warning("⚠️  Some reports failed to generate/send")
                return False

            self.log.info(f"\n{'=' * 70}")
            self.log.info(f"✅ Job completed successfully for {self.name}")
            self.log.info(f"{'=' * 70}\n")
            return True

        except Exception as e:
            self.log.error(f"❌ Unexpected error in run: {e}", exc_info=True)
            return False

        finally:
            self.log.info(f"Closing P4 connection...")
            self.p4_manager.disconnect()


    def start_schedule(self) -> None:
        """
        Start scheduler to run preset at configured schedule time.

        The schedule time is read from the config (Schedule Time in Miscellaneous section).
        Format: "HH:MM" (24-hour format), e.g., "18:30"
        """
        self.log.info(f"Starting scheduler for preset '{self.name}' at {self.schedule_time}")

        while True:
            try:
                current_time = time.strftime("%H:%M")

                if current_time == self.schedule_time:
                    self.log.info(f"⏰ Trigger time '{self.schedule_time}' reached, starting job")
                    try:
                        self.run()
                    except Exception as e:
                        self.log.error(f"❌ Job failed: {e}", exc_info=True)

                time.sleep(60)  # Check every 60 seconds

            except KeyboardInterrupt:
                self.log.info("Scheduler stopped by user (KeyboardInterrupt)")
                break
            except Exception as e:
                self.log.error(f"Unexpected error in scheduler: {e}", exc_info=True)
                time.sleep(60)

    @staticmethod
    def schedule(preset_name: str, *trigger_times: str) -> None:
        """
        [Deprecated] Run preset on a schedule at specified times.

        Use start_schedule() instance method instead, which reads schedule time from config.

        Args:
            preset_name: Name of the preset to run
            *trigger_times: Times to trigger (format: "HH:MM"), e.g., schedule("RPT", "09:00", "18:30")

        Example:
            model = Model("RPT")
            model.start_schedule()  # Runs daily at time specified in config
        """
        logger = logging.getLogger(__name__)
        logger.info(f"Starting scheduler for preset '{preset_name}' at times: {', '.join(trigger_times)}")

        while True:
            try:
                current_time = time.strftime("%H:%M")

                for trigger_time in trigger_times:
                    if current_time == trigger_time:
                        logger.info(f"⏰ Trigger time '{trigger_time}' reached, starting job")
                        try:
                            model = Model(preset_name)
                            model.run()
                        except Exception as e:
                            logger.error(f"❌ Job failed: {e}", exc_info=True)

                time.sleep(60)  # Check every 60 seconds

            except KeyboardInterrupt:
                logger.info("Scheduler stopped by user (KeyboardInterrupt)")
                break
            except Exception as e:
                logger.error(f"Unexpected error in scheduler: {e}", exc_info=True)
                time.sleep(60)


if __name__ == "__main__":
    pass
