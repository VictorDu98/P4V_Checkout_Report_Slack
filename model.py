import os
import shutil
import requests
import json
import re
from datetime import datetime
from P4 import P4, P4Exception

formatted_date = datetime.now().strftime("%y%m%d")

target_time = "15:06"

ROOT_DIR= os.path.dirname(os.path.realpath(__file__))
PRESET_DIR= os.path.join(ROOT_DIR,"presets")

class Preset:
    """
    GENERATE LOG - > TRACE WORKSPACE  -> TRACE USER -> WRITE REPORT
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
        self.output_log = os.path.join(self.output_root, f"log_{formatted_date}.txt")
        self.slack_uri = JSON["misc"][0]["SlackUri"]
        self.producer_slack_id = JSON["misc"][0]["Producer"]

    def __str__(self):
        return self.name

    @staticmethod
    def check_exist(path):
        return os.path.exists(path)

    def create_template(self):
        dic = {
            "misc":[
                {
                    "Address": "Project address on server network",
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
        P4CLIENT= "p4client"
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
        json_accounts = {entry['AccountName'] for entry in JSON['info']}

        output_log = os.path.join(self.output_root, f"log_{formatted_date}.txt")

        if self.check_exist(output_log):
            print("Found old log, deleting...")
            os.remove(output_log)

        p4 = P4()
        try:
            p4.connect()  # Connect to the Perforce server
        except P4Exception as e:
            for e in p4.errors:  # Display errors
                raise e
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
    def trace_workspace(string_list: list) -> set:
        """
        Use regex expression to match lines that include "edit"
        and extract the workspace names.

        :param string_list: Lines from a log file.
        :return: A set of workspace names that matched.
        """
        pattern = re.compile(r"^.+ - edit - CL (\d+|default) - ([A-Za-z0-9_]+)$")

        workspaces = set()

        for line in string_list:
            match = pattern.match(line.strip())
            if match:
                workspace_name = match.group(2)
                workspaces.add(workspace_name)

        return workspaces

    def trace_user(self):
        JSON = self.open_json()
        json_workspaces = {entry['WorkSpace'] for entry in JSON['info']}
        #print(workspace_indexed)
        #for i , ws in enumerate(workspace_indexed):
            #print(i,ws)
        users_index = []
        if not self.check_exist(self.output_log):
            raise FileNotFoundError(f"File {self.output_log} does not exist.")

        with open(self.output_log, "r", encoding="utf-8") as f:
            contents = [line.strip() for line in f] #quick fix to remove all \n in string

            result = self.trace_workspace(contents)
            if result is None:
                return None
            
            for found_workspace in result:
                for i, json_workspace in enumerate(json_workspaces):
                    if re.search(found_workspace, json_workspace):
                        users_index.append(i)
    
            return users_index

    def generate_report(self,department:str):
        output_report = os.path.join(self.output_root, f"report_{department}_{formatted_date}.txt")
        if self.check_exist(output_report):
            os.remove(output_report)

        JSON = self.open_json()
        users_found = self.trace_user()
        for user in users_found:
            if JSON['info'][user]['Department'] == department:
                report = f"{JSON['info'][user]['Project']} - {JSON['info'][user]['UserName']} - {JSON['info'][user]['WorkSpace']} - {JSON['info'][user]['Email']}"
                with open(output_report, 'a', encoding='utf-8') as f:
                    f.write(report + "\n")


if __name__ == "__main__":
    object = Preset("GFH")
    #print(formatted_date)
    #print(object.trace_user())
    object.generate_report(department="ENV")
    # todo : Test with real p4 server and get log result
    #object.generate_log()