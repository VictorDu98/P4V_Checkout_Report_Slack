import time
import os
import subprocess
import shutil
import requests
import json
target_time = "15:06"

TOTAL_TASK=0
ROOT_DIR= os.path.dirname(os.path.realpath(__file__))
PRESET_DIR= os.path.join(ROOT_DIR,"presets")

class Preset:
    def __init__(self, task_name, order):
        self.task_name = task_name
        self.task_order = order
        self.preset_root= os.path.join(PRESET_DIR,f"{self.task_name}")
        os.makedirs(self.preset_root,exist_ok=True)
        print(f"Created preset: {self.task_name}")

    def __str__(self):
        return self.task_name

    def run_task(self):
        slack_send(uri)
        #return 0-1
        pass

    def use_config(self,task_name):
        #from P4 import P4, P4Exception
        #p4.config=task_name
        pass


    def create_p4config(self,port,user,client,charset):
        p4_config = os.path.join(self.preset_root, f".p4config_{self.task_name}.txt")
        config = create_p4config(port, user, client, charset)
        with open(p4_config, 'w') as file:
            file.write(config)

    def create_users_list(self):
        users_list = os.path.join(self.preset_root, f"users_{self.task_name}.json")
        dic = create_users_template()
        with open(users_list, 'w') as file:
            file.write(json.dumps(dic, indent=4))

    def create_log(self):
        log = os.path.join(self.preset_root, f"log_{self.task_name}.txt")
        with open(log, 'w') as file:
            file.write("log")


def slack_send(webhook,producer_id):
    # Define the webhook URL provided by Slack
    webhook_url = "https://hooks.slack.com/services/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"

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


def create_users_template() -> dict:
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
    return dic

def create_p4config(port:str,user:str,client:str,charset:str) ->str:
    config = f"""
    P4PORT={port}
    P4USER={user}
    P4CLIENT={client}
    P4CHARSET={charset}
    P4CONFIG="""
    return config


def remove_preset(preset):
    preset_path = os.path.join(PRESET_DIR,f"{preset}")
    if os.path.exists(preset_path):
        # remove if exists
        shutil.rmtree(preset_path)
        print(f"Deleted preset: {preset}")