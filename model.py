import time
import os
import subprocess
import shutil
import requests
import json
import re
target_time = "15:06"

TOTAL_TASK=0
ROOT_DIR= os.path.dirname(os.path.realpath(__file__))
PRESET_DIR= os.path.join(ROOT_DIR,"presets")

class Preset:
    def __init__(self, name, order):
        self.name = name
        self.order = order
        self.preset_root = os.path.join(PRESET_DIR,name)

    def __str__(self):
        return self.name


    def run_task(self):
        #slack_send(uri)
        #return 0-1
        pass

    def use_config(self,task_name):
        #from P4 import P4, P4Exception
        #p4.config=task_name
        pass


    def create_p4config(self,port :str,user:str,client :str,charset :str):
        config_root = os.path.join(self.preset_root, f".p4config_{self.name}.txt")
        config = f"""
        P4PORT={port}
        P4USER={user}
        P4CLIENT={client}
        P4CHARSET={charset}
        P4CONFIG="""

        with open(config_root, 'w') as file:
            file.write(config)

    def create_users_list(self):
        users_list = os.path.join(self.preset_root, f"users_{self.name}.json")
        dic = {
            "info":
                [
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
        with open(users_list, 'w') as file:
            file.write(json.dumps(dic, indent=4))

    @classmethod
    def create_preset(cls,preset_name):
        preset_root= os.path.join(PRESET_DIR,f"{preset_name}")
        os.makedirs(preset_root,exist_ok=True)
        print(f"Created preset: {preset_name}")

    @classmethod
    def remove_preset(cls,preset):
        preset_path = os.path.join(PRESET_DIR, f"{preset}")
        if os.path.exists(preset_path):
            shutil.rmtree(preset_path)
            print(f"Deleted preset: {preset}")

def slack_send(webhook,producer_id):
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


class PerforceWorkspaceReport:
    def __init__(self, p4_config):
        self.p4_config = p4_config
        self.producer_id = str()

    def login(self):
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

    def add_producer(self,slack_id):
        self.producer_id = slack_id


def regex_filter(string_list:list)-> set:
    pattern= "by\s+(.*?)(\s+\*exclusive\*)?(\s+\*locked\*)?$"
    ignore_mark_for_add = ".*add.*"
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


def del_text_file(file_full_path):
    # Remove old report files if they exist
    if os.path.exists(file_full_path):
        os.remove(file_full_path)

def generate_report(indexes:list):
    # Process VFX department reports
    for index in indexes:
        if JSON['info']['Department'][index] == "VFX":
            report = (f"{JSON['info']['Project'][index]} - {JSON['info']['UserName'][index]} - "
                      f"{JSON['info']['WorkSpace'][index]} - {JSON['info']['Email'][index]}")
            with open(OUTPUT_REPORT_VFX, 'a', encoding='utf-8') as f:
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
        if JSON['info']['Department'][index] == "VFX":
            report = (f"{JSON['info']['Project'][index]} - {JSON['info']['UserName'][index]} - "
                      f"{JSON['info']['WorkSpace'][index]} - {JSON['info']['Email'][index]}")
            with open(OUTPUT_REPORT_VFX, 'a', encoding='utf-8') as f:
                f.write(report + "\n")

    # Process ENV department reports
    for index in json_index:
        if JSON['info']['Department'][index] == "ENV":
            report = (f"{JSON['info']['Project'][index]} - {JSON['info']['UserName'][index]} - "
                      f"{JSON['info']['WorkSpace'][index]} - {JSON['info']['Email'][index]}")
            with open(OUTPUT_REPORT_ENV, 'a', encoding='utf-8') as f:
                f.write(report + "\n")