import time
import os
import subprocess
import shutil
import requests
import json
import re
from datetime import datetime
from P4 import P4, P4Exception

formatted_date = datetime.now().strftime("%y%m%d")

target_time = "15:06"

TOTAL_TASK=0
ROOT_DIR= os.path.dirname(os.path.realpath(__file__))
PRESET_DIR= os.path.join(ROOT_DIR,"presets")

class Preset:
    def __init__(self, name):
        self.name = name
        self.preset_root = os.path.join(PRESET_DIR, name)
        self.preset_config = os.path.join(self.preset_root, f"config_{self.name}.json")
        self.perforce_config = os.path.join(self.preset_root, f".p4config_{self.name}.txt")

        if not os.path.exists(self.preset_root):
            os.makedirs(self.preset_root, exist_ok=True)
            self.create_template()

        JSON = self.open_json()
        self.output_path = JSON["misc"]["Address"]
        self.slack_uri = JSON["misc"]["Slack"]
        self.producer_slack_id = JSON["misc"]["Producer"]
        self.output_log = None
        self.output_report = None

    def __str__(self):
        return self.name

    @staticmethod
    def check_exist(path):
        if os.path.exists(path):
            return True
        else:
            return False

    def create_template(self):
        dic = {
            "misc":[
                {
                    "Address": "Project address on server network",
                    "Slack": "Slack incoming webhook",
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
        data = json.load(f)
        f.close()
        return data

    @staticmethod
    def filter_log(string_list:list)-> set:
        """
        Log file output string that always come with user@workspace in each line.\n
        Use regex expression to match "mark for add" files and files that have the status of "exclusive checkout"\n
        Lines of text that matched regex will be returned in a set array\n
        Lines of text that fit in ignore case will be ignored since the file itself it's not on depot yet

        :param string_list: string line
        :return: workspace name list that matches regex expression
        """
        pattern= r"by\s+(.*?)(\s+\*exclusive\*)?(\s+\*locked\*)?$"
        ignore_mark_for_add = r".*add.*"
        workspaces=set()
        for string in string_list:
            if re.match(ignore_mark_for_add, string):
                continue
            else:
                if re.match(pattern, string):
                    # Split string with delimiter "@" and take workspace name by index 1
                    workspace_name = string.split("@")[1]
                    workspaces.add(workspace_name)

        return workspaces

    def generate_log(self):
        JSON= self.open_json()
        accounts_name = JSON["info"]["AccountName"]

        if not self.check_exist(self.perforce_config):
            raise FileNotFoundError(f"File {self.perforce_config} does not exist.")

        self.output_log = os.path.join(self.output_path,"logs", f"log_{formatted_date}.txt")

        if self.check_exist(self.output_log):
            os.remove(self.output_log)

        try:  # Catch exceptions with try/except
            p4 = P4()
            p4.p4config_file = self.perforce_config

            p4.connect()  # Connect to the Perforce server
            p4.run_login()
        except P4Exception:
            for e in p4.errors:  # Display errors
                raise e

        for name in accounts_name:
            # Run the `p4 opened -u <user>` command
            opened_files = p4.run_opened("-u", name)

            if opened_files:
                with open(self.output_log, 'a', encoding='utf-8') as f:
                    f.write(f"-------------------------{name}----------------------------\n")
                    # Only write lines that contain the word "edit"
                    for line in output.splitlines():
                        if "edit" in line:
                            f.write(line + "\n")
                    f.write("\n")

    def filter_user(self):
        # Assume FilterLogFile() is defined elsewhere and returns a list of found workspaces.
        result = self.filter_log()
        JSON = self.open_json()
        json_workspaces = JSON['info']['WorkSpace']
        json_indexes = []

        if result is None:
            return None

        for found_workspace in result:
            for i, json_workspace in enumerate(json_workspaces):
                if re.search(found_workspace, json_workspace):
                    json_indexes.append(i)

        return json_indexes

    def generate_report(self,json_indexes:list,department:str):
        self.output_report = os.path.join(self.output_path, "logs", f"check_out_report_{department}_{formatted_date}.txt")
        if self.check_exist(self.output_report):
            os.remove(self.output_report)

        # Read and parse the JSON file
        JSON = self.open_json()
        for index in json_indexes:
            if JSON['info']['Department'][index] == department:
                report = f"{JSON['info']['Project'][index]} - {JSON['info']['UserName'][index]} - {JSON['info']['WorkSpace'][index]} - {JSON['info']['Email'][index]}"
                with open(self.output_report, 'a', encoding='utf-8') as f:
                    f.write(report + "\n")

