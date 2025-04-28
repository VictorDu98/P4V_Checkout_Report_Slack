import model
import time
import os

class schedule():
    def __init__(self):
        self.tasks= []


    def queueTask(self):
        # accept signal clicked
        # get order from model
        # set current task order number
        while True:
            current_time = time.strftime("%H:%M")
            if current_time == target_time:
                subprocess.run(fr"D:\tools\P4V_Checkout_Report_Slack\slack.py")
            time.sleep(60)

    def addTask(self,name):
        # accept user task_name
        # accept user .p4config
        # accept user target_time
        # formulate a list
        # create object
        # assign task to view
        task = model.Task(
            task_name=name,
            order=1,
            p4_port="someport",
            p4_user="someuser",
            p4_client="someclient",
            p4_charset="none")
        self.tasks.append(task)
        self.refreshView()
        return task

    def refreshView(self):
        # update list
        pass
    def executeTask(self):
        # accept signal button clicked
        # run task
        pass

    def statusTask(self):
        # update status of task
        # 0= disabled, 1= failed, 2=success
        pass

    def removeTask(self,task):

        # accept singal button clicked
        # prompt user yes/no
        # find task id
            # stop subprocess of task
        # del object
        for obj in self.tasks:
            print(obj.task_name)
            if obj.task_name == task:
                self.tasks.remove(obj)
            if os.path.exists(f"{obj.task_name}.txt"):
                os.remove(f"{obj.task_name}.txt")
                print(f"Deleted file: {obj.task_name}")

        self.refreshView()


app = schedule()
app.addTask(name="GFH")
#time.sleep(5)
#app.removeTask(task="GFH")