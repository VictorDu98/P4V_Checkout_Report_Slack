import os
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
    GENERATE LOG - >  TRACE WORKSPACE  -> TRACE USER -> WRITE REPORT -> SEND SLACK
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
        print(self.department)

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
        P4CHARSET= "utf-8"
        """
        with open(self.perforce_config, 'w') as file:
            file.write(config)

    def remove(self):
        if self.check_exist(self.preset_config):
            shutil.rmtree(self.preset_config)
            print(f"Deleted preset: {self.name}")

    def set_perforce_config(self, port, user, client, charset):
        config = f"""
        P4PORT= "{port}"
        P4USER= "{user}"
        P4CLIENT= "{client}"
        P4CHARSET= "{charset}"
        """
        if not self.check_exist(self.perforce_config):
            raise FileNotFoundError(f"File {self.perforce_config} does not exist.")

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
        //depot/project/file1.cpp - edit - CL 12345 - alice_workspace

        ------------------------- bob ----------------------------
        //depot/scripts/script.py - edit - CL 12347 - bob_ws
        """
        JSON= self.open_json()
        json_accounts = []
        for entry in JSON["info"]:
            json_accounts.append(entry["AccountName"])

        output_log = os.path.join(self.output_root, f"log_{self.name}_{formatted_date}.txt")

        if self.check_exist(output_log):
            print("Found old log, deleting...")
            os.remove(output_log)

        os.system(f"p4 set P4CONFIG={self.perforce_config}")
        p4 = P4()
        try:
            p4.connect()  # Connect to the Perforce server
            print("Login p4 success")
        except P4Exception as e:
            for e in p4.errors:  # Display errors
                raise e

        for name in json_accounts:
            # Run the `p4 opened -u <user>` command
            found_files = p4.run_opened("-u", name)
            #print(found_files)
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
        and extract the workspace names.

        :param string_list: Lines from a log file.
        :return: A set of workspace names that matched.
        """
        pattern = re.compile(r"^.+ - edit - CL (\d+|default) - ([A-Za-z0-9_]+)")

        workspaces = []

        for line in string_list:
            match = pattern.match(line.strip())
            if match:
                workspace_name = match.group(2)
                #print(workspace_name)
                if workspace_name not in workspaces:
                    workspaces.append(workspace_name)

        return workspaces

    def trace_user(self):
        JSON = self.open_json()
        json_workspaces=[]
        for entry in JSON["info"]:
            #print(entry["WorkSpace"])
            json_workspaces.append(entry["WorkSpace"])
        users_index = []

        if not self.check_exist(self.output_log):
            return None

        with open(self.output_log, "r", encoding="utf-8") as f:
            contents = [line.strip() for line in f] #quick fix to remove all \n in string

            result = self.trace_workspace(contents)
            if result is None:
                return None
            
            for found_workspace in result:
                #print(found_workspace)
                i=0
                for json_workspace in json_workspaces:
                    if re.match(found_workspace, json_workspace):
                        users_index.append(i)
                    i=i+1
            #print(users_index)
            return users_index

    def generate_report(self,department:str):
        output_report = os.path.join(self.output_root, f"report_{department}_{formatted_date}.txt")
        if self.check_exist(output_report):
            print("Found old report, deleting ...")
            os.remove(output_report)

        JSON = self.open_json()
        users_found = self.trace_user()
        if users_found:
            for user in users_found:
                if JSON['info'][user]['Department'] == department:
                    report = f"{JSON['info'][user]['Project']} - {JSON['info'][user]['UserName']} - {JSON['info'][user]['WorkSpace']} - {JSON['info'][user]['Email']}"
                    with open(output_report, 'a', encoding='utf-8') as f:
                        f.write(report + "\n")
        else:
            print("No user found")

    def send_slack(self,department):
        hex_color = hex(random.randrange(0, 2**24))
        std_color = "#" + hex_color[2:]

        output_report = os.path.join(self.output_root, f"report_{department}_{formatted_date}.txt")
        if not self.check_exist(output_report):
            return

        with open(output_report) as f:
            contents = f.read()
            payload = {
                "attachments": [
                    {
                        "text": f"{contents} CC: <@{self.producer_slack_id}>",
                        "color": f"{std_color}",
                        "author_name": f"{department}",
                        "fallback": f"Hello producer, please help notify these artists about their P4V checked out files."
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
            self.send_slack(department=department)

if __name__ == "__main__":
    while True:
        current_time = time.strftime("%H:%M")
        if current_time == "20:45" or current_time == "23:45" or current_time == "1:45":
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

        time.sleep(60) # Interval trigger time
