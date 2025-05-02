import time
import os

class Controller():
    def __init__(self,model,view):
        self.model = model
        self.view = view


    def queue_task(self,target_time):
        # accept signal clicked
        # get order from model
        # set current task order number
        # get user input target_time
        """while True:
            current_time = time.strftime("%H:%M")
            if current_time == target_time:
            #subprocess.run(fr"D:\\tools\\P4V_Checkout_Report_Slack\\slack.py")
            time.sleep(60)'"""

    def add_task(self,name):
        # find preset with name
            # accept user input P4 env
            # accept user input  target_time to trigger Task
            #Q
            #
        # if not exist then create new preset
             # create object based on View input
        task = self.model.Preset(name=name)
        #TODO: Replace with View string input
        """task.create_p4config(
            port="perforce:1666",
            user="p4user",
            client="p4client",
            charset="utf-8")
        """

        self.tasks.append(task)
        # assign task to view
        #self.refresh_view()

    def refresh_view(self):
        # update view list
        pass
    def execute_task(self):
        # accept signal button clicked
        # run task
        pass

    def status_task(self):
        # update status of task
        # 0= disabled, 1= failed, 2=success
        pass

    def remove_task(self,task):
        # accept singal button clicked
        # prompt user yes/no
        # find task name
            # stop subprocess of task
        model.Preset.remove_preset(preset=task)
        #self.refreshView()


app = schedule()
app.add_task(name="GFH")
#app.remove_task(task="GFH")