import time
import os
from datetime import datetime
from model import Model

class Controller:
    def __init__(self, model):
        self.model = model
        self.view = None  # Will be set later to avoid circular dependency
        self.tasks = []

    def set_view(self, view):
        self.view = view

    def handle_new_preset(self, preset_name):
        try:
            self.model = Model(preset_name)  # Create new model instance with preset name
            self.view.display_success(f"Created new preset: {preset_name}")
        except Exception as e:
            self.view.display_error(f"Failed to create preset: {str(e)}")

    def handle_p4_config(self,config):
        try:
            self.model.set_perforce_config(
                port=config['port'],
                user=config['user'],
                client=config['client'],
                charset=config['charset']
            )
            self.view.display_success("P4 configuration updated successfully")
        except Exception as e:
            self.view.display_error(f"Failed to update P4 config: {str(e)}")

    def handle_preset_config(self, preset_name):
        try:
            # Load and display current config
            config = self.model.open_json()
            self.view.display_success("Configuration loaded successfully")
            return config
        except Exception as e:
            self.view.display_error(f"Failed to load configuration: {str(e)}")
            return None

    def handle_schedule_time(self, preset_name, time):
        try:
            self.queue_task(time)
            self.view.display_success(f"Schedule set for {time}")
        except Exception as e:
            self.view.display_error(f"Failed to set schedule: {str(e)}")

    def handle_remove_preset(self, preset_name, confirmed):
        if not confirmed:
            return

        try:
            self.model.remove()
            self.view.display_success(f"Preset '{preset_name}' removed successfully")
        except Exception as e:
            self.view.display_error(f"Failed to remove preset: {str(e)}")

    def handle_generate_report(self, preset_name, department):
        try:
            # Generate log first
            self.model.generate_log()
            # Then generate report for specific department
            self.model.generate_report(department)
            self.view.display_success(f"Report generated successfully for {department}")
        except Exception as e:
            self.view.display_error(f"Failed to generate report: {str(e)}")

    def queue_task(self, target_time):
        """Schedule a task to run at specific time"""
        try:
            # Store the task details
            task = {
                'time': target_time,
                'preset': self.model.name,
                'status': 'scheduled'
            }
            self.tasks.append(task)

            # In a real implementation, you might want to use a proper scheduler
            # For now, we'll just store the task
            return True
        except Exception as e:
            raise Exception(f"Failed to schedule task: {str(e)}")

    def execute_task(self, task):
        """Execute a scheduled task"""
        try:
            # Generate log and report
            self.model.generate_log()
            # You might want to get the department from the configuration
            self.model.generate_report("ENV")  # Default to ENV department
            task['status'] = 'completed'
            return True
        except Exception as e:
            task['status'] = 'failed'
            raise Exception(f"Task execution failed: {str(e)}")

    def check_scheduled_tasks(self):
        """Check and execute scheduled tasks"""
        current_time = time.strftime("%H:%M")
        for task in self.tasks:
            if task['time'] == current_time and task['status'] == 'scheduled':
                try:
                    self.execute_task(task)
                except Exception as e:
                    self.view.display_error(str(e))