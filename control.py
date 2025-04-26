class schedule:
    def __init__(self):
        pass

    def queueTask(self):
        # accept signal clicked
        # get order from model
        # set current task order number
        while True:
            current_time = time.strftime("%H:%M")
            if current_time == target_time:
                subprocess.run(fr"D:\tools\P4V_Checkout_Report_Slack\slack.py")
            time.sleep(60)

    def addTask(self):
        # accept user task_name
        # accept user .p4config
        # accept user target_time
        # formulate a list
        # assign task to view
        self.refreshView()
        pass

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

    def removeTask(self):
        # accept signal button clicked
        # get task
        # send model to destroy it
        # assert task
        self.refreshView()

