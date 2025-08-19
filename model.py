import os
import sys
import shutil
import requests
import json
import re
import random
import time
from datetime import datetime
from P4 import P4, P4Exception

ROOT_DIR= os.path.dirname(os.path.realpath(__file__))
PRESET_DIR= os.path.join(ROOT_DIR,"presets")

class Model:
    """
    1. READ CONTENT FROM PRESET JSON CONFIG
    2. LOGIN P4 WITH .P4TICKET
    3. GENERATE LOG
    4. TRACE WORKSPACE
    5. TRACE USER FROM WORKSPACE FOUND
    6. GENERATE REPORT
    7 .SEND SLACK

    """
    def __init__(self, name):
        self.name = name
        self.preset_root = os.path.join(PRESET_DIR, name)
        self.preset_p4ticket = os.path.join(self.preset_root, ".p4tickets")
        self.preset_config = os.path.join(self.preset_root, "config.json")
        self.preset_p4config = os.path.join(self.preset_root, ".p4config")
        if not os.path.exists(self.preset_root):
            os.makedirs(self.preset_root, exist_ok=True)
            self.create_template()

        with open(self.preset_config, "r", encoding="utf-8") as f:
            JSON= json.load(f)
            self.output_root = JSON["misc"][0]["OutputLogAndReport"]
            self.output_log = os.path.join(self.output_root, f"log_{self.name}_{self.get_time()}.txt")
            self.webhook = JSON["misc"][0]["Webhook"]
            self.department = []
            self.json_accounts=[]
            self.json_workspaces=[]
            for entry in JSON["info"]:
                if entry["Department"] not in self.department:
                    self.department.append(entry["Department"])
                self.json_workspaces.append(entry["WorkSpace"])
                self.json_accounts.append(entry["AccountName"])

        self.p4  = None

    def __str__(self):
        return self.name

    @staticmethod
    def get_time():
        return datetime.now().strftime("%y%m%d")

    @staticmethod
    def check_exist(path):
        return os.path.exists(path)

    @staticmethod
    def trace_workspace(string_list: list):
        """
        Use regex expression to match lines that include "edit"
        to extract the workspace names.

        :param string_list: Lines from a log file.
        :return: A set of workspace names that matched.
        """
        pattern = re.compile(r"^.+ - edit - CL (\d+|default) - ([A-Za-z0-9._]+)")
        workspaces = []
        for line in string_list:
            match = pattern.match(line.strip())
            if match:
                workspace_name = match.group(2)
                if workspace_name not in workspaces:
                    workspaces.append(workspace_name)

        return workspaces

    @staticmethod
    def compare_data(x,y):
        users_index = []
        for found_workspace in x:
            i = 0
            for json_workspace in y:
                if re.match(found_workspace, json_workspace):
                    users_index.append(i)
                i = i + 1
        return users_index

    @staticmethod
    def gen_color():
        return hex(random.randrange(0, 2 ** 24))[2:]

    def create_template(self):
        dic = {
            "misc":[
                {
                    "OutputLogAndReport": "Project address on server network",
                    "SlackUri": "Slack incoming webhook",
                    "Producer": "Producer slack id"
                }
            ],
            "info":[
                    {
                        "UserName": "Artist real name",
                        "AccountName": "Artist P4V account name",
                        "Project": "Project name",
                        "Department": "ENV/VFX/LIGHTING/RIGGING/CHARACTER/...",
                        "Email": "Artist email",
                        "WorkSpace": "Artist P4V workspace name"
                    },
                    {
                        "UserName": "Artist real name",
                        "AccountName": "Artist P4V account name",
                        "Project": "Project name",
                        "Department": "ENV/VFX/LIGHTING/RIGGING/CHARACTER/...",
                        "Email": "Artist email",
                        "WorkSpace": "Artist P4V workspace name"
                    }
            ]
        }
        with open(self.preset_config, 'w') as file:
            file.write(json.dumps(dic, indent=4))

        config = f"""
        P4PORT= "perforce:1666"
        P4USER= "p4user"
        P4CHARSET= "utf8"
        P4CLIENT="p4client"
        """
        with open(self.preset_p4config, 'w') as file:
            file.write(config)

    def open_json(self):
        if not self.check_exist(self.preset_config):
            raise FileNotFoundError(f"File {self.preset_config} does not exist.")
        f = open(self.preset_config, "r", encoding="utf-8")
        return json.load(f)

    def init_p4(self):
        """

        :return:
        """
        os.system(f"p4 set P4CONFIG={self.preset_p4config}")  # Switch to preset p4config
        if not self.check_exist(self.preset_p4ticket):
            self.create_p4ticket()
        else:
            self.p4 = P4()
            self.p4.ticket_file = self.preset_p4ticket
            try:
                if not self.p4.connected():
                    self.p4.connect()  # Connect to the Perforce server
                self.p4.run_opened()

            except P4Exception:
                for e in self.p4.errors:  # Display errors
                    print(self.name,e)
                self.p4 = None

    def create_p4ticket(self):
        """
        Attempt to create new preset .p4ticket if not have any , skip init p4 module if failed 3 times
        :return:
        """
        self.p4  = P4()
        retries = 3
        while True:
            if retries == 0:
                self.p4 = None
                return

            self.p4.ticket_file = self.preset_p4ticket
            self.p4.password = input(f"Enter your {self.name} P4 Password : ")
            try:
                if not self.p4.connected():
                    self.p4.connect()  # Connect to the Perforce server
                self.p4.run_login()
                break
            except P4Exception:
                for e in self.p4.errors:  # Display errors
                    print(e)
                retries = retries - 1

    def generate_log(self):
        """
        ------------------------- alice ----------------------------
        //depot/project/file1.cpp  - edit - CL 12345 - alice_workspace

        ------------------------- bob ----------------------------
        //depot/scripts/script.py - edit - CL 12347 - bob_ws

        ------------------------- P4 Username ----------------------------
        [1] Current file depot address - [2] Status - [3] Changelist numbers - [4] Client name

        """
        output_log = os.path.join(self.output_root, f"log_{self.name}_{self.get_time()}.txt")
        if self.check_exist(output_log):
            print(f"Found old log from {self.name}, deleting...")
            os.remove(output_log)

        if not self.p4.connected():
            self.p4.connect()  # Connect to the Perforce server

        for name in self.json_accounts:
            # Run the `p4 opened -u <user>` command
            found_files = self.p4.run_opened("-u", name)
            if not found_files:
                continue
            with open(output_log, 'a', encoding='utf-8') as f:
                f.write(f"------------------------- {name} ----------------------------\n")
                for file in found_files:
                    if file.get("action") == "edit":
                        depot_file = file.get("depotFile", "unknown")
                        changelist = file.get("change", "unknown")
                        client = file.get("client", "unknown")
                        f.write(f"{depot_file} - edit - CL {changelist} - {client}\n")
                f.write("\n")
        self.p4.disconnect()

    def trace_user(self)->list:
        if not self.check_exist(self.output_log):
            return None

        with open(self.output_log, "r", encoding="utf-8") as f:
            contents = [line.strip() for line in f] #quick fix to remove all \n in string
            result = self.trace_workspace(contents)
            if result is None:
                return None
            return self.compare_data(result , self.json_workspaces)

    def generate_report(self,department:str):
        output_report = os.path.join(self.output_root, f"report_{department}_{self.get_time()}.txt")
        if self.check_exist(output_report):
            print(f"Found old report from {self.name}, deleting ...")
            os.remove(output_report)

        JSON = self.open_json()
        users_found_index = self.trace_user()
        with open(output_report, 'a', encoding='utf-8') as f:
            if users_found_index:
                for num_index, user_index in enumerate(users_found_index):
                    user= JSON['info'][user_index]
                    if user['Department'] == department:
                        report = f"{user['Project']}-{user['UserName']}-{user['WorkSpace']}-{user['Email']}"
                        if num_index == len(users_found_index)-1:
                                f.write(report)
                        else:
                                f.write(report+ "\n")
            else:
                print(f"No user found on {self.name}")

    def send_teams(self,department):
        """
        :param department: Text file suffix, must identical with preset config.json key "Department" value . e.g : VFX/ENV/CHA
        :return:
        """
        output_report = os.path.join(self.output_root, f"report_{department}_{self.get_time()}.txt")

        if self.check_exist(output_report):
            with open(output_report) as f:
                contents = f.read()
                payload = {
                    "text": contents
                }
            # Send the POST request to Slack
            response = requests.post(
                self.webhook,
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'}
            )
            if response.status_code == 202:
                print("Payload sent successfully!")
            else:
                print(f"Failed to send payload. Status code: {response.status_code}, Response: {response.text}")

    def run(self):
        self.init_p4()
        if self.p4:
            self.generate_log()
            for department in self.department:
                self.generate_report(department=department)
                self.send_teams(department=department)
        else:
            print(f"{self.name} P4 is invalid, job skipped.")

if __name__ == "__main__":
    pass
    # TODO : Overcome p4trust
    # TODO : Separate main function into new file
