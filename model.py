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

formatted_date = datetime.now().strftime("%y%m%d")
#target_time = "15:06"

ROOT_DIR= os.path.dirname(os.path.realpath(__file__))
PRESET_DIR= os.path.join(ROOT_DIR,"presets")

class Model:
    """
    1. READ CONTENT FROM PRESET JSON CONFIG
    2. GENERATE LOG
    3. TRACE WORKSPACE
    4. TRACE USER FROM WORKSPACE FOUND
    5. GENERATE REPORT
    6 .SEND SLACK

    """
    def __init__(self, name):
        self.name = name
        self.preset_root = os.path.join(PRESET_DIR, name)
        self.preset_config = os.path.join(self.preset_root, "config.json")
        self.perforce_config = os.path.join(self.preset_root, ".p4config")
        if not os.path.exists(self.preset_root):
            os.makedirs(self.preset_root, exist_ok=True)
            self.create_template()

        JSON = self.open_json()
        self.output_root = JSON["misc"][0]["OutputLogAndReport"]
        self.output_log = os.path.join(self.output_root, f"log_{self.name}_{formatted_date}.txt")
        self.slack_uri = JSON["misc"][0]["SlackUri"]
        self.producer_slack_id = JSON["misc"][0]["Producer"]
        self.department = []
        for entry in JSON["info"]:
            if entry["Department"] not in self.department:
                self.department.append(entry["Department"])

        #print(self.department)

    def __str__(self):
        return self.name

    @staticmethod
    def check_exist(path):
        return os.path.exists(path)

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
        with open(self.perforce_config, 'w') as file:
            file.write(config)

    def open_json(self):
        if not self.check_exist(self.preset_config):
            raise FileNotFoundError(f"File {self.preset_config} does not exist.")
        f = open(self.preset_config, "r", encoding="utf-8")
        return json.load(f)

    def generate_log(self):
        """
        ------------------------- alice ----------------------------
        //depot/project/file1.cpp  - edit - CL 12345 - alice_workspace

        ------------------------- bob ----------------------------
        //depot/scripts/script.py - edit - CL 12347 - bob_ws

        ------------------------- P4 Username ----------------------------
        [1] Current file depot address - [2] Status - [3] Changelist numbers - [4] Client name

        """


        output_log = os.path.join(self.output_root, f"log_{self.name}_{formatted_date}.txt")

        if self.check_exist(output_log):
            print(f"Found old log from {self.name}, deleting...")
            os.remove(output_log)

        os.system(f"p4 set P4CONFIG={self.perforce_config}") #Switch to preset p4config
        p4 = P4()
        try:
            p4.connect()  # Connect to the Perforce server
            print("Login p4 success")
        except P4Exception as e:
            for e in p4.errors:  # Display errors
                raise e

        JSON= self.open_json()
        json_accounts = []
        for entry in JSON["info"]:
            json_accounts.append(entry["AccountName"])

        for name in json_accounts:
            # Run the `p4 opened -u <user>` command
            found_files = p4.run_opened("-u", name)
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
        p4.disconnect()

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

    def trace_user(self)->list:
        """

        :return:
        """
        if not self.check_exist(self.output_log):
            return None

        json_workspaces=[]
        users_index = []

        JSON = self.open_json()
        for entry in JSON["info"]:
            #print(entry["WorkSpace"])
            json_workspaces.append(entry["WorkSpace"])

        with open(self.output_log, "r", encoding="utf-8") as f:
            contents = [line.strip() for line in f] #quick fix to remove all \n in string

            result = self.trace_workspace(contents)
            if result is None:
                return None
            
            for found_workspace in result:
                i=0
                for json_workspace in json_workspaces:
                    if re.match(found_workspace, json_workspace):
                        users_index.append(i)
                    i=i+1
            return users_index

    def generate_report(self,department:str):
        output_report = os.path.join(self.output_root, f"report_{department}_{formatted_date}.txt")
        if self.check_exist(output_report):
            print(f"Found old report from {self.name}, deleting ...")
            os.remove(output_report)

        JSON = self.open_json()
        users_found_index = self.trace_user()
        if users_found_index:
            for user_index in users_found_index:
                if JSON['info'][user_index]['Department'] == department:
                    report = f"{JSON['info'][user_index]['Project']} - {JSON['info'][user_index]['UserName']} - {JSON['info'][user_index]['WorkSpace']} - {JSON['info'][user_index]['Email']}"
                    with open(output_report, 'a', encoding='utf-8') as f:
                        f.write(report + "\n")

    @staticmethod
    def gen_color():
        hex_color = hex(random.randrange(0, 2 ** 24))
        std_color = "#" + hex_color[2:]
        return std_color

    def send_slack(self,department):
        output_report = os.path.join(self.output_root, f"report_{department}_{formatted_date}.txt")
        if not self.check_exist(output_report):
            return

        with open(output_report) as f:
            contents = f.read()
            payload = {
                "attachments": [
                    {
                        "text": f"{contents} CC: <@{self.producer_slack_id}>",
                        "color": f"{self.gen_color()}",
                        "author_name": f"{department}",
                        "fallback": f"Hello  <@{self.producer_slack_id}>, please help notify these artists about their P4V checked out files."
                    }
                ]
            }
            # Send the POST request to Slack
            response = requests.post(self.slack_uri, json=payload, headers={'Content-Type': 'application/json'})

            # Check the response
            if response.status_code == 200:
                print("Message sent successfully!")
            else:
                print(f"Failed to send message. Status code: {response.status_code}, Response: {response.text}")

    def run(self):
        self.generate_log()
        for department in self.department:
            self.generate_report(department=department)
            #self.send_slack(department=department)

def main(*args):
    print("Running P4V Checkout tool")
    while True:
        current_time = time.strftime("%H:%M")
        for arg in args:
            if current_time == arg:
                GFH = Model("GFH")
                ISN_ENV_1 = Model("ISN_ENV_1")
                ISN_ENV_2 = Model("ISN_ENV_2")
                ISN_VFX_1 = Model("ISN_VFX_1")
                ISN_VFX_2 = Model("ISN_VFX_2")
                GFH.run()
                ISN_ENV_1.run()
                ISN_ENV_2.run()
                ISN_VFX_1.run()
                ISN_VFX_2.run()
        time.sleep(60)  # Interval trigger time

if __name__ == "__main__":
    #main("20:45","23:45","01:45")
    GFH = Model("GFH")