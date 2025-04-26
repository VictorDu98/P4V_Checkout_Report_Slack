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
        self.createConfig()

    def __del__(self):
        if os.path.exists(self.task_name):
            os.remove(self.task_name)
            print(f"Deleted file: {self.task_name}")

    def runTask(self):
        #execute
        #return 0-1
        pass

    def createConfig(self):
        filename = f".p4config_{self.task_name}.txt"
        with open(filename, 'w') as file:
            config = f"""
P4PORT={self.P4PORT}
P4USER={self.P4USER}
P4CLIENT={self.P4CLIENT}
P4CHARSET={self.P4CHARSET}
P4CONFIG=            
            """
            file.write(config)

    def useConfig(self,task_name):
        #from P4 import P4, P4Exception
        #p4.config=task_name
        pass
