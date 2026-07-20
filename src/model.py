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

    def __init__(self, preset_root: str, log: Optional[logging.Logger] = None) -> None:
        self.preset_root = preset_root
        self.config_path = os.path.join(preset_root, "config.json")
        self.p4config_path = os.path.join(preset_root, ".p4config")
        self.config: Dict[str, Any] = {}
        self.log = log or logging.getLogger(__name__)
        self.log.debug(f"PresetConfig initialized for: {preset_root}")

    def load(self) -> None:
        """Load configuration from config.json."""
        self.log.debug(f"Loading config from: {self.config_path}")

        if not os.path.exists(self.config_path):
            self.log.error(f"Config file not found: {self.config_path}")
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
            self.log.info(f"Config loaded successfully with {len(self.config.get('info', []))} user(s)")
        except json.JSONDecodeError as e:
            self.log.error(f"Invalid JSON in {self.config_path}: {e}")
            raise ValueError(f"Invalid JSON in {self.config_path}: {e}")
        except IOError as e:
            self.log.error(f"Failed to read {self.config_path}: {e}")
            raise IOError(f"Failed to read {self.config_path}: {e}")

    def get_output_root(self) -> str:
        """Get output directory from config."""
        self.log.debug("Retrieving output root directory")
        try:
            output_root = self.config["misc"][0]["OutputLogAndReport"]
            self.log.debug(f"Output root: {output_root}")
            return output_root
        except (KeyError, IndexError) as e:
            self.log.error(f"Missing 'misc.OutputLogAndReport' in config: {e}")
            raise KeyError(f"Missing 'misc.OutputLogAndReport' in config: {e}")

    def get_webhook(self) -> str:
        """Get webhook URL from config."""
        self.log.debug("Retrieving webhook URL")
        try:
            webhook = self.config["misc"][0]["Webhook"]
            self.log.debug("Webhook retrieved successfully")
            return webhook
        except (KeyError, IndexError) as e:
            self.log.error(f"Missing 'misc.Webhook' in config: {e}")
            raise KeyError(f"Missing 'misc.Webhook' in config: {e}")

    def get_accounts(self) -> List[str]:
        """Get list of P4 account names."""
        self.log.debug("Retrieving account names")
        accounts = []
        try:
            for entry in self.config.get("info", []):
                accounts.append(entry["AccountName"])
            self.log.debug(f"Found {len(accounts)} account(s): {accounts}")
        except KeyError as e:
            self.log.error(f"Missing 'AccountName' in config entry: {e}")
            raise KeyError(f"Missing 'AccountName' in config entry: {e}")
        return accounts

    def get_workspaces(self) -> List[str]:
        """Get list of workspace names."""
        self.log.debug("Retrieving workspace names")
        workspaces = []
        try:
            for entry in self.config.get("info", []):
                workspaces.append(entry["WorkSpace"])
            self.log.debug(f"Found {len(workspaces)} workspace(s)")
        except KeyError as e:
            self.log.error(f"Missing 'WorkSpace' in config entry: {e}")
            raise KeyError(f"Missing 'WorkSpace' in config entry: {e}")
        return workspaces

    def get_departments(self) -> List[str]:
        """Get unique departments from config."""
        self.log.debug("Retrieving departments")
        departments = []
        try:
            for entry in self.config.get("info", []):
                dept = entry["Department"]
                if dept not in departments:
                    departments.append(dept)
            self.log.debug(f"Found {len(departments)} department(s): {departments}")
        except KeyError as e:
            self.log.error(f"Missing 'Department' in config entry: {e}")
            raise KeyError(f"Missing 'Department' in config entry: {e}")
        return departments

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
            self.log.debug(f"Writing config template to: {self.config_path}")
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(dic, f, indent=4)
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

                        if user.get("Department") != department:
                            self.log.debug(f"Skipping user {user_idx}: department mismatch")
                            continue

                        if user.get("UserName") is None:
                            user_entry = f"<at>{user['Email']}</at>"
                        else:
                            user_entry = f"<at>{user['Email']}</at> - {user.get('UserName')} - {user['WorkSpace']}"

                        f.write(user_entry)
                        users_written += 1
                        self.log.debug(f"Wrote user entry for {user.get('AccountName', 'unknown')}")

                        if idx < len(user_indices) - 1:
                            f.write("<br>")

                    except (KeyError, IndexError) as e:
                        self.log.warning(f"Error processing user {user_idx}: {e}")
                        continue

                # Add log file reference
                f.write(f"<br><br>Vào đây xem log để biết file nào đang checkout nè:<br>{output_path}")

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
        """Generate and send reports for all departments. Returns True if all succeeded."""
        self.log.info(f"Generating reports for {len(self.departments)} department(s)")

        try:
            if not os.path.exists(self.output_log):
                self.log.warning("Log file not found, skipping reports")
                return False

            self.log.debug(f"Reading log file: {self.output_log}")
            with open(self.output_log, 'r', encoding='utf-8') as f:
                log_content = f.read()
            self.log.debug(f"Log file size: {len(log_content)} bytes")

            success = True
            reports_generated = 0
            reports_sent = 0

            for department in self.departments:
                self.log.info(f"Processing department: {department}")

                report_path = os.path.join(
                    self.output_root,
                    f"report_{department}_{self.get_date()}.txt"
                )

                # Remove old report if exists
                if os.path.exists(report_path):
                    self.log.info(f"Removing old report: {report_path}")
                    os.remove(report_path)

                # Generate report
                self.log.debug(f"Generating report for {department}")
                if self.report_gen.generate(
                    report_path,
                    log_content,
                    self.workspaces,
                    self.config.config.get("info", []),
                    department,
                    self.get_time()
                ):
                    reports_generated += 1
                    self.log.debug(f"Report generated, sending to Teams")

                    # Send to Teams
                    if self.report_gen.send_to_teams(report_path, self.webhook):
                        reports_sent += 1
                    else:
                        self.log.warning(f"Failed to send report for {department}")
                        success = False
                else:
                    self.log.warning(f"Failed to generate report for {department}")
                    success = False

            self.log.info(f"Report generation complete: {reports_generated}/{len(self.departments)} generated, {reports_sent}/{reports_generated} sent")
            return success

        except Exception as e:
            self.log.error(f"Unexpected error generating reports: {e}", exc_info=True)
            return False

    def run(self) -> bool:
        """Execute the full workflow. Returns True if successful."""
        self.log.info(f"=" * 70)
        self.log.info(f"🚀 Starting job for preset: {self.name}")
        self.log.info(f"=" * 70)
        self.log.info(f"Accounts: {', '.join(self.accounts)}")
        self.log.info(f"Departments: {', '.join(self.departments)}")
        self.log.info(f"Timestamp: {self.get_time()}")

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


    @staticmethod
    def schedule(preset_name: str, *trigger_times: str) -> None:
        """
        Run preset on a schedule at specified times.

        Args:
            preset_name: Name of the preset to run
            *trigger_times: Times to trigger (format: "HH:MM"), e.g., schedule("RPT", "09:00", "18:30")

        Example:
            Model.schedule("RPT", "18:30")  # Runs daily at 6:30 PM
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
