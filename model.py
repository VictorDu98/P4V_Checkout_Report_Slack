import time
import os
import subprocess
target_time = "15:06"

TOTAL_TASK=0

class Task:
    def __init__(self, task_name, order, p4_port,
                 p4_user, p4_charset, p4_client):
        self.task_name = task_name
        self.task_order = order
        self.P4PORT = p4_port
        self.P4USER = p4_user
        self.P4CHARSET= p4_charset
        self.P4CLIENT = p4_client
        self.create_preset()

    def __del__(self):
        if os.path.exists(self.task_name):
            os.remove(self.task_name)
            print(f"Deleted file: {self.task_name}")

    def run_task(self):
        #execute
        #return 0-1
        pass

    def create_preset(self):
        p4_config_name = f".p4config_{self.task_name}.txt"
        user_list = f"users_{self.task_name}.json"
        log = f"log_{self.task_name}.json"

        with open(p4_config_name, 'w') as config_file:
            config = f"""
P4PORT={self.P4PORT}
P4USER={self.P4USER}
P4CLIENT={self.P4CLIENT}
P4CHARSET={self.P4CHARSET}
P4CONFIG=            
            """
            config_file.write(config)

        with open(user_list, 'w') as users_file:
            users_file.write("user")

        with open(log, 'w') as log_file:
            log_file.write("log")

    def use_config(self,task_name):
        #from P4 import P4, P4Exception
        #p4.config=task_name
        pass
