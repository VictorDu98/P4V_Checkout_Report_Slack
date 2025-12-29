import os
import sys
import shutil
import requests
import json
import re
import random
import time
from datetime import datetime, timedelta, timezone
from P4 import P4, P4Exception
from abc import ABC, abstractmethod

ROOT_DIR= os.path.dirname(os.path.realpath(__file__))
PRESET_DIR= os.path.join(ROOT_DIR,"presets")

class Preset(ABC):
    """
    Abstract base class for P4 and MS Teams workflow models.
    Defines structure, lifecycle, and shared helpers.
    """

    def __init__(self, name: str):
        self.name = name

        # ---- Preset paths
        self.preset_root = os.path.join(PRESET_DIR, name)
        self.preset_p4ticket = os.path.join(self.preset_root, ".p4tickets")
        self.preset_config = os.path.join(self.preset_root, "config.json")
        self.preset_p4config = os.path.join(self.preset_root, ".p4config")

        if not os.path.exists(self.preset_root):
            os.makedirs(self.preset_root, exist_ok=True)
            self.create_template()

        self._load_config()
        self.p4 = None

    def __str__(self):
        return self.name

    # ==========================
    # Abstract contract
    # ==========================

    @abstractmethod
    def create_template(self):
        pass

    @abstractmethod
    def init_p4(self):
        pass

    @abstractmethod
    def generate_log(self):
        pass

    @abstractmethod
    def generate_report(self, department: str):
        pass

    @abstractmethod
    def send_teams(self, department: str):
        pass

    # ==========================
    # Shared logic
    # ==========================

    def _load_config(self):
        with open(self.preset_config, "r", encoding="utf-8") as f:
            JSON = json.load(f)

        self.output_root = JSON["misc"][0]["OutputLogAndReport"]
        self.webhook = JSON["misc"][0]["Webhook"]
        self.output_log = os.path.join(
            self.output_root,
            f"log_{self.name}_{self.get_date()}.txt"
        )

        self.department = []
        self.json_accounts = []
        self.json_workspaces = []

        for entry in JSON["info"]:
            if entry["Department"] not in self.department:
                self.department.append(entry["Department"])
            self.json_workspaces.append(entry["WorkSpace"])
            self.json_accounts.append(entry["AccountName"])

    # ==========================
    # Static helpers (unchanged)
    # ==========================

    @staticmethod
    def get_date():
        return datetime.now().strftime("%y%m%d")

    @staticmethod
    def get_time():
        utc_plus_7 = timezone(timedelta(hours=7))
        return datetime.now(utc_plus_7).strftime("%I:%M %p")

    @staticmethod
    def check_exist(path):
        return os.path.exists(path)

    @staticmethod
    def trace_workspace(string_list: list):
        pattern = re.compile(r"^.+ - edit - CL (\d+|default) - ([A-Za-z0-9._]+)")
        workspaces = []
        for line in string_list:
            match = pattern.match(line.strip())
            if match:
                ws = match.group(2)
                if ws not in workspaces:
                    workspaces.append(ws)
        return workspaces

    @staticmethod
    def compare_data(found, config):
        users_index = []
        for found_ws in found:
            for i, json_ws in enumerate(config):
                if re.match(found_ws, json_ws):
                    users_index.append(i)
        return users_index

    def open_preset_config_json(self):
        if not self.check_exist(self.preset_config):
            raise FileNotFoundError(self.preset_config)
        with open(self.preset_config, "r", encoding="utf-8") as f:
            return json.load(f)


class Model(Preset):

    def create_template(self):
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
                    "UserName": "User real name",
                    "Department": "ENV/VFX/LIGHTING",
                    "Email": "artist@virtuosgames.com",
                    "WorkSpace": "workspace_name"
                }
            ]
        }

        with open(self.preset_config, "w", encoding="utf-8") as f:
            json.dump(dic, f, indent=4)

        with open(self.preset_p4config, "w") as f:
            f.write("""
P4PORT=perforce:1666
P4USER=p4user
P4CHARSET=utf8
P4CLIENT=p4client
""")

    def init_p4(self):
        os.system(f"p4 set P4CONFIG={self.preset_p4config}")

        if not self.check_exist(self.preset_p4ticket):
            self.create_p4ticket()
            return

        self.p4 = P4()
        self.p4.ticket_file = self.preset_p4ticket

        try:
            if not self.p4.connected():
                self.p4.connect()
            self.p4.run_opened()
        except P4Exception:
            self.p4 = None

    def create_p4ticket(self):
        self.p4 = P4()
        self.p4.ticket_file = self.preset_p4ticket

        retries = 3
        while retries > 0:
            self.p4.password = input(f"Enter {self.name} P4 password: ")
            try:
                self.p4.connect()
                self.p4.run_login()
                return
            except P4Exception:
                retries -= 1

        self.p4 = None

    def generate_log(self):
        if self.check_exist(self.output_log):
            os.remove(self.output_log)

        self.p4.connect()

        for user in self.json_accounts:
            files = self.p4.run_opened("-u", user)
            if not files:
                continue

            with open(self.output_log, "a", encoding="utf-8") as f:
                f.write(f"------------------------- {user} ----------------------------\n")
                for file in files:
                    if file.get("action") == "edit":
                        f.write(
                            f"{file['depotFile']} - edit - CL {file['change']} - {file['client']}\n"
                        )
                f.write("\n")

        self.p4.disconnect()

    def trace_user(self):
        if not self.check_exist(self.output_log):
            return None

        with open(self.output_log, "r", encoding="utf-8") as f:
            contents = [line.strip() for line in f]
        found = self.trace_workspace(contents)
        return self.compare_data(found, self.json_workspaces)

    def generate_report(self, department: str):
        output = os.path.join(
            self.output_root,
            f"report_{department}_{self.get_date()}.txt"
        )

        if self.check_exist(output):
            os.remove(output)

        JSON = self.open_preset_config_json()
        users = self.trace_user()

        if not users:
            return

        with open(output, "w", encoding="utf-8") as f:
            f.write(f"Các bạn này đang checkout file P4V lúc {self.get_time()} 🚨<br><br>")
            for i in users:
                user = JSON["info"][i]
                if user["Department"] == department:
                    f.write(f"<at>{user['Email']}</at><br>")
            f.write("<br>Xem log tại:<br>" + self.output_log)

    def send_teams(self, department: str):
        output = os.path.join(
            self.output_root,
            f"report_{department}_{self.get_date()}.txt"
        )

        if not self.check_exist(output):
            return

        with open(output, encoding="utf-8") as f:
            payload = {"text": f.read()}

        requests.post(
            self.webhook,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"}
        )

    def run(self):
        self.init_p4()
        if not self.p4:
            print(f"{self.name} P4 invalid, skipped.")
            return

        self.generate_log()
        for dept in self.department:
            self.generate_report(dept)
            self.send_teams(dept)


if __name__ == "__main__":
    pass
    # TODO : Separate p4python elements from main class into separate class
