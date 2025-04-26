import time
import os
import subprocess
target_time = "15:06"


class Task:
    def __init__(self, task_id, task_status, task_order):
        self.task_id = task_id
        self.task_status = task_status
        self.task_order = task_order

    def __del__(self):
        pass

    def runTask(self):
        #execute
        #return 0-1
        pass

    def formulateReport(self):
        pass






