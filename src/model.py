import os
import sys
import shutil
import requests
import json
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

ROOT_DIR: str = os.path.dirname(os.path.realpath(__file__))
PRESET_DIR: str = os.path.join(ROOT_DIR, "presets")




class PresetConfig:
    """Handle preset configuration loading and management."""

    def __init__(self, preset_root: str) -> None:
        self.preset_root = preset_root
        self.config_path = os.path.join(preset_root, "config.json")
        self.p4config_path = os.path.join(preset_root, ".p4config")
        self.config: Dict[str, Any] = {}

    def load(self) -> None:
        """Load configuration from config.json."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {self.config_path}: {e}")
        except IOError as e:
            raise IOError(f"Failed to read {self.config_path}: {e}")

    def get_output_root(self) -> str:
        """Get output directory from config."""
        try:
            return self.config["misc"][0]["OutputLogAndReport"]
        except (KeyError, IndexError) as e:
            raise KeyError(f"Missing 'misc.OutputLogAndReport' in config: {e}")

    def get_webhook(self) -> str:
        """Get webhook URL from config."""
        try:
            return self.config["misc"][0]["Webhook"]
        except (KeyError, IndexError) as e:
            raise KeyError(f"Missing 'misc.Webhook' in config: {e}")

    def get_accounts(self) -> List[str]:
        """Get list of P4 account names."""
        accounts = []
        try:
            for entry in self.config.get("info", []):
                accounts.append(entry["AccountName"])
        except KeyError as e:
            raise KeyError(f"Missing 'AccountName' in config entry: {e}")
        return accounts

    def get_workspaces(self) -> List[str]:
        """Get list of workspace names."""
        workspaces = []
        try:
            for entry in self.config.get("info", []):
                workspaces.append(entry["WorkSpace"])
        except KeyError as e:
            raise KeyError(f"Missing 'WorkSpace' in config entry: {e}")
        return workspaces

    def get_departments(self) -> List[str]:
        """Get unique departments from config."""
        departments = []
        try:
            for entry in self.config.get("info", []):
                dept = entry["Department"]
                if dept not in departments:
                    departments.append(dept)
        except KeyError as e:
            raise KeyError(f"Missing 'Department' in config entry: {e}")
        return departments

    def get_user_by_index(self, index: int) -> Dict[str, Any]:
        """Get user info by index."""
        try:
            return self.config["info"][index]
        except (IndexError, KeyError) as e:
            raise IndexError(f"Invalid user index {index}: {e}")

    def create_template(self) -> None:
        """Create template configuration files."""
        dic = {
            "misc": [
                {
                    "OutputLogAndReport": "Output address to store logs and report",
                    "Webhook": "Microsoft Teams Workflow incoming webhook"
                }
            ],
            "info": [
                {
                    "AccountName": "Artist P4V account name",
                    "UserName": "User real name - optional and can excluded in config",
                    "Department": "ENV/VFX/LIGHTING/RIGGING/CHARACTER/...",
                    "Email": "Artist @virtuosgames.com email , must be @virtuogames.com otherwise Teams Workflow can't tag user on channel",
                    "WorkSpace": "Artist P4V workspace name"
                },
                {
                    "AccountName": "Artist P4V account name",
                    "Department": "ENV/VFX/LIGHTING/RIGGING/CHARACTER/...",
                    "Email": "Artist @virtuosgames email",
                    "WorkSpace": "Artist P4V workspace name"
                }
            ]
        }
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(dic, f, indent=4)
        except IOError as e:
            raise IOError(f"Failed to write {self.config_path}: {e}")

        p4config_content = """P4PORT= "perforce:1666"
P4USER= "p4user"
P4CHARSET= "utf8"
P4CLIENT="p4client"
"""
        try:
            with open(self.p4config_path, 'w', encoding='utf-8') as f:
                f.write(p4config_content)
        except IOError as e:
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
        try:
            os.system(f"p4 set P4CONFIG={self.p4config_path}")

            if not os.path.exists(self.p4ticket_path):
                return self._create_ticket(preset_name)

            return self._connect_with_ticket()
        except Exception as e:
            self.log.error(f"Failed to initialize P4: {e}")
            self.p4 = None
            return False

    def _create_ticket(self, preset_name: str) -> bool:
        """Create new P4 ticket via login. Returns True if successful."""
        self.p4 = P4()
        retries = 3

        while retries > 0:
            try:
                self.p4.ticket_file = self.p4ticket_path
                password = getpass.getpass(f"Enter P4 password for {preset_name}: ")
                self.p4.password = password

                if not self.p4.connected():
                    self.p4.connect()
                self.p4.run_login()
                self.log.info(f"P4 ticket created for {preset_name}")
                return True

            except P4Exception as e:
                retries -= 1
                self.log.error(f"P4 login failed (retries left: {retries}): {e}")
                if retries == 0:
                    self.p4 = None
                    return False

    def _connect_with_ticket(self) -> bool:
        """Connect using existing ticket. Returns True if successful."""
        try:
            self.p4 = P4()
            self.p4.ticket_file = self.p4ticket_path

            if not self.p4.connected():
                self.p4.connect()

            # Test connection
            self.p4.run_opened()
            self.log.info("P4 connected successfully")
            return True

        except P4Exception as e:
            self.log.error(f"Failed to connect P4: {e}")
            self.p4 = None
            return False
        except Exception as e:
            self.log.error(f"Unexpected error connecting P4: {e}")
            self.p4 = None
            return False

    def get_opened_files(self, account: str) -> List[Dict[str, str]]:
        """Get files opened by a specific account."""
        if not self.p4 or not self.p4.connected():
            self.log.warning(f"P4 not connected, cannot get opened files for {account}")
            return []

        try:
            files = self.p4.run_opened("-u", account)
            return files if files else []
        except P4Exception as e:
            self.log.error(f"Failed to get opened files for {account}: {e}")
            return []

    def disconnect(self) -> None:
        """Safely disconnect from P4."""
        if self.p4:
            try:
                self.p4.disconnect()
            except Exception as e:
                self.log.warning(f"Error disconnecting P4: {e}")


class ReportGenerator:
    """Handle report generation and Teams message sending."""

    WORKSPACE_PATTERN = re.compile(r"^.+ - edit - CL (\d+|default) - ([A-Za-z0-9._]+)")

    def __init__(self, log: logging.Logger) -> None:
        self.log = log

    @classmethod
    def trace_workspace(cls, lines: List[str]) -> List[str]:
        """Extract workspace names from log lines."""
        workspaces: List[str] = []

        for line in lines:
            match = cls.WORKSPACE_PATTERN.match(line.strip())
            if match:
                workspace = match.group(2)
                if workspace not in workspaces:
                    workspaces.append(workspace)

        return workspaces

    @staticmethod
    def find_matching_users(found_workspaces: List[str], config_workspaces: List[str]) -> List[int]:
        """Find indices of matching workspaces in config."""
        user_indices: List[int] = []

        for found in found_workspaces:
            for idx, config in enumerate(config_workspaces):
                if re.match(found, config):
                    user_indices.append(idx)
                    break  # Match each found workspace only once

        return user_indices

    def generate(
        self,
        output_path: str,
        log_content: str,
        config_workspaces: List[str],
        config_users: List[Dict[str, Any]],
        department: str,
        timestamp: str
    ) -> bool:
        """Generate report file. Returns True if successful."""
        try:
            lines = [line.strip() for line in log_content.split('\n')]
            found_workspaces = self.trace_workspace(lines)

            if not found_workspaces:
                self.log.info(f"No users found for department {department}")
                return False

            user_indices = self.find_matching_users(found_workspaces, config_workspaces)
            if not user_indices:
                return False

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"Các bạn này đang checkout file P4V vào lúc {timestamp} 🚨<br><br>")

                for idx, user_idx in enumerate(user_indices):
                    try:
                        user = config_users[user_idx]

                        if user.get("Department") != department:
                            continue

                        # Try to include UserName if available
                        try:
                            user_entry = f"<at>{user['Email']}</at> - {user.get('UserName', 'N/A')} - {user['WorkSpace']}"
                        except KeyError:
                            user_entry = f"<at>{user['Email']}</at>"

                        f.write(user_entry)

                        if idx < len(user_indices) - 1:
                            f.write("<br>")

                    except (KeyError, IndexError) as e:
                        self.log.warning(f"Error processing user {user_idx}: {e}")
                        continue

                # Add log file reference
                f.write(f"<br><br>Vào đây xem log để biết file nào đang checkout nè:<br>{log_content.split(chr(10))[0]}")

            self.log.info(f"Report generated: {output_path}")
            return True

        except Exception as e:
            self.log.error(f"Failed to generate report: {e}")
            return False

    def send_to_teams(self, report_path: str, webhook: str) -> bool:
        """Send report to Teams via webhook. Returns True if successful."""
        if not os.path.exists(report_path):
            self.log.warning(f"Report file not found: {report_path}")
            return False

        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()

            payload = {"text": content}
            response = requests.post(
                webhook,
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )

            if response.status_code == HTTPStatus.ACCEPTED:
                self.log.info("Report sent to Teams successfully")
                return True
            else:
                self.log.error(f"Teams API returned {response.status_code}: {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            self.log.error(f"Failed to send request to Teams: {e}")
            return False
        except Exception as e:
            self.log.error(f"Failed to send report to Teams: {e}")
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
            self.departments = self.config.get_departments()
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
        log_path = Path(self.output_log)
        temp_path = log_path.with_suffix('.tmp')

        try:
            # Write to temp file first (atomic operation)
            with open(temp_path, 'w', encoding='utf-8') as f:
                all_found = False
                for account in self.accounts:
                    files = self.p4_manager.get_opened_files(account)
                    if not files:
                        continue

                    all_found = True
                    f.write(f"------------------------- {account} ----------------------------\n")
                    for file_entry in files:
                        if file_entry.get("action") == "edit":
                            depot_file = file_entry.get("depotFile", "unknown")
                            changelist = file_entry.get("change", "unknown")
                            client = file_entry.get("client", "unknown")
                            f.write(f"{depot_file} - edit - CL {changelist} - {client}\n")
                    f.write("\n")

            # Atomic rename
            temp_path.replace(log_path)

            if all_found:
                self.log.info(f"Log generated: {self.output_log}")
            else:
                self.log.info("No opened files found")

            return all_found

        except IOError as e:
            self.log.error(f"Failed to write to log file: {e}")
            if temp_path.exists():
                temp_path.unlink()
            return False

        except Exception as e:
            self.log.error(f"Unexpected error generating log: {e}")
            if temp_path.exists():
                temp_path.unlink()
            return False

    def generate_reports(self) -> bool:
        """Generate and send reports for all departments. Returns True if all succeeded."""
        try:
            if not os.path.exists(self.output_log):
                self.log.warning("Log file not found, skipping reports")
                return False

            with open(self.output_log, 'r', encoding='utf-8') as f:
                log_content = f.read()

            success = True
            for department in self.departments:
                report_path = os.path.join(
                    self.output_root,
                    f"report_{department}_{self.get_date()}.txt"
                )

                # Remove old report if exists
                if os.path.exists(report_path):
                    self.log.info(f"Removing old report: {report_path}")
                    os.remove(report_path)

                # Generate report
                if self.report_gen.generate(
                    report_path,
                    log_content,
                    self.workspaces,
                    self.config.config.get("info", []),
                    department,
                    self.get_time()
                ):
                    # Send to Teams
                    if not self.report_gen.send_to_teams(report_path, self.webhook):
                        success = False
                else:
                    success = False

            return success

        except Exception as e:
            self.log.error(f"Unexpected error generating reports: {e}")
            return False

    def run(self) -> bool:
        """Execute the full workflow. Returns True if successful."""
        self.log.info(f"Starting job for preset: {self.name}")

        try:
            # Initialize P4
            if not self.p4_manager.initialize(self.name):
                self.log.warning("P4 initialization failed, job skipped")
                return False

            # Generate log of opened files
            if not self.generate_log():
                self.log.error("Failed to generate log")
                return False

            # Generate and send reports
            if not self.generate_reports():
                self.log.warning("Some reports failed to generate/send")
                return False

            self.log.info(f"Job completed successfully for {self.name}")
            return True

        except Exception as e:
            self.log.error(f"Unexpected error in run: {e}")
            return False

        finally:
            self.p4_manager.disconnect()


if __name__ == "__main__":
    pass
