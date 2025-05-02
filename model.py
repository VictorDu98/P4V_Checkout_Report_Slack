import time
import os
import subprocess
import shutil
from os.path import exists

import requests
import json
import re
target_time = "15:06"

TOTAL_TASK=0
ROOT_DIR= os.path.dirname(os.path.realpath(__file__))
PRESET_DIR= os.path.join(ROOT_DIR,"presets")

class Preset:
    def __init__(self, name):
        self.name = name
        self.preset_root = os.path.join(PRESET_DIR,name)
        self.preset_config = os.path.join(self.preset_root, f"config_{self.name}.json")
        if not os.path.exists(self.preset_root):
            os.makedirs(self.preset_root, exist_ok=True)
            self.create()

    def __str__(self):
        return self.name

    @staticmethod
    def check_exist(path):
        if os.path.exists(path):
            return True
        else:
            return False

    def create(self):
        dic = {
            "output":[
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

    def remove(self):
        if self.check_exist(self.preset_config):
            shutil.rmtree(self.preset_config)
            print(f"Deleted preset: {self.name}")

def slack_debug(webhook):
    # Define the webhook URL provided by Slack
    webhook_url = webhook

    # Define the message payload
    payload = {
        "text": "Here is a message with an attachment.",
        "attachments": [
            {
                "color": "#3192DC",  # Set the color of the attachment
                "author_name": "Attachment Author",
                "title": "Attachment Title",
                "text": "This is the content of the attachment.",
                "footer": "Attachment Footer",
                "ts": 1234567890  # Timestamp (optional)
            }
        ]
    }

    # Send the POST request to Slack's webhook URL
    response = requests.post(webhook_url, json=payload)

    # Check the response
    if response.status_code == 200:
        print("Message sent successfully.")
    else:
        print(f"Failed to send message: {response.status_code}, {response.text}")


class PerforceWorkspaceReport(Preset):
    def __init__(self, name):
        super().__init__(name)
        self.p4_config = os.path.join(self.preset_root, f".p4config_{self.name}.txt")
        if not os.path.exists(self.p4_config):
            self.create()

    def create(self):
        config = f"""
        P4PORT= "perforce:1666"
        P4USER= "p4user"
        P4CLIENT= "p4client"
        P4CHARSET= "utf-8"
        """
        with open(self.p4_config, 'w') as file:
            file.write(config)

    def login(self):
        if not self.check_exist(self.p4_config):
            raise FileNotFoundError(f"File {self.p4_config} does not exist.")

        from P4 import P4, P4Exception
        p4 = P4()
        p4.config = self.p4_config

        try:  # Catch exceptions with try/except
            p4.connect()  # Connect to the Perforce server
            info = p4.run("info")  # Run "p4 info" (returns a dict)
            for key in info[0]:  # and display all key-value pairs
                print(key, "=", info[0][key])

        except P4Exception:
            for e in p4.errors:  # Display errors
                print(e)

    @staticmethod
    def regex_filter(string_list:list)-> set:
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


    def generate_report(self,department:str,output:str):
        # Process VFX department reports
        if not self.check_exist(output):
            raise FileNotFoundError(f"File {output} does not exist.")\

        if JSON['info']['Department'][index] == department:
            report = (f"{JSON['info']['Project'][index]} - {JSON['info']['UserName'][index]} - "
                f"{JSON['info']['WorkSpace'][index]} - {JSON['info']['Email'][index]}")
            with open(output, 'a', encoding='utf-8') as f:
                f.write(report + "\n")

    def find_user():
        # Assume FilterLogFile() is defined elsewhere and returns a list of found workspaces.
        result = regex_filter()
        json_workspaces = JSON['info']['WorkSpace']
        json_index = []

        if result is None:
            return None

        for found_workspace in result:
            for i, json_workspace in enumerate(json_workspaces):
                if re.search(found_workspace, json_workspace):
                    json_index.append(i)

        # Process VFX department reports
        for index in json_index:
            generate_report("ENV")
