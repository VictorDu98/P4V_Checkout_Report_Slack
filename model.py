import time
import os
import subprocess
target_time = "15:06"

TOTAL_TASK=0

class Task:
    def __init__(self,name,order):
        self.task_name = name
        self.task_order = order
        self.target_hour = 0
        self.target_minute = 0
        self.createConfig()

    def __del__(self):
        if os.path.exists(self.task_name):
            os.remove(self.task_name)
            print(f"Deleted file: {self.task_name}")

    def runTask(self):
        #execute
        #return 0-1
        pass

    def to_dict(self):
        return {key: value for key, value in self.__dict__.items()}

    def createConfig(self):
        filename = f"{self.task_name}.txt"
        with open(filename, 'w') as f:
            for key, value in self.to_dict().items():
                f.write(f"{key}: {value}\n")




