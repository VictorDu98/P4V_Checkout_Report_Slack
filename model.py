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


