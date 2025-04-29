import time
import os
import subprocess
import shutil
target_time = "15:06"

TOTAL_TASK=0
ROOT_DIR= os.path.dirname(os.path.realpath(__file__))
PRESET_DIR= os.path.join(ROOT_DIR,"presets")

class Preset:

    def __init__(self, task_name, order, p4_port,
                 p4_user, p4_charset, p4_client):
        self.task_name = task_name
        self.task_order = order
        self.P4PORT = p4_port
        self.P4USER = p4_user
        self.P4CHARSET= p4_charset
        self.P4CLIENT = p4_client
        self.preset_root= os.path.join(PRESET_DIR,f"{self.task_name}")
        os.makedirs(self.preset_root,exist_ok=True)
        self.create_preset()
        print(f"Created preset: {self.task_name}")

    def __str__(self):
        return self.task_name

    def run_task(self):
        #execute
        #return 0-1
        pass

    def create_preset(self):
        def create_p4config():
            p4_config = os.path.join(self.preset_root,f".p4config_{self.task_name}.txt")
            with open(p4_config, 'w') as file:
                config = f"""
        P4PORT={self.P4PORT}
        P4USER={self.P4USER}
        P4CLIENT={self.P4CLIENT}
        P4CHARSET={self.P4CHARSET}
        P4CONFIG=            
                    """
                file.write(config)


        def create_users_list():
            users_list = os.path.join(self.preset_root,f"users_{self.task_name}.json")
            with open(users_list, 'w') as file:
                file.write("user")

        def create_log():
            log = os.path.join(self.preset_root,f"log_{self.task_name}.txt")
            with open(log, 'w') as file:
                file.write("log")

        #Execute all functions inside this method
        for name, func in locals().items():
            if callable(func):
                func()

    @classmethod
    def remove_preset(cls,preset):
        preset_path = os.path.join(PRESET_DIR,f"{preset}")
        if os.path.exists(preset_path):
            # remove if exists
            shutil.rmtree(preset_path)
            print(f"Deleted preset: {preset}")

    def use_config(self,task_name):
        #from P4 import P4, P4Exception
        #p4.config=task_name
        pass
