class View:
    def __init__(self, controller):
        self.controller = controller

    def display_main_menu(self):
        while True:
            print("\n--- Welcome to Slack Report Tool  ---")
            print("1. Register new preset")
            print("2. Edit a preset")
            print("3. Remove preset")
            print("4. Generate Report")
            print("5. Exit")

            choice = input("Select an option (1-5): ").strip()

            if choice == '1':
                self.prompt_new_preset()
            elif choice == '2':
                self.display_edit_menu()
            elif choice == '3':
                self.prompt_remove_preset()
            elif choice == '4':
                self.prompt_generate_report()
            elif choice == '5':
                self.display_exit()
                break
            else:
                self.display_invalid_option()

    def prompt_new_preset(self):
        preset_name = input("Enter new preset name: ").strip()
        self.controller.handle_new_preset(preset_name)

    def display_edit_menu(self):
        preset_name = input("Input your preset name: ").strip()
        while True:
            print(f"\n--- Edit Preset {preset_name} Configuration ---")
            print("1. Edit P4 Configuration")
            print("2. Edit Preset Configuration")
            print("3. Set Schedule Time")
            print("4. Back to main menu")
            
            choice = input("Select an option (1-4): ").strip()
            
            if choice == '1':
                self.prompt_p4_config(preset_name)
            elif choice == '2':
                self.controller.handle_preset_config(preset_name)
            elif choice == '3':
                time = input("Enter schedule time (HH:MM): ").strip()
                self.controller.handle_schedule_time(preset_name, time)
            elif choice == '4':
                break
            else:
                self.display_invalid_option()

    def prompt_p4_config(self, preset_name):
        config = {
            'port': input("P4PORT (e.g., perforce:1666): ").strip(),
            'user': input("P4USER: ").strip(),
            'client': input("P4CLIENT: ").strip(),
            'charset': input("P4CHARSET (default: utf-8): ").strip() or "utf-8"
        }
        self.controller.handle_p4_config(preset_name, config)

    def prompt_remove_preset(self):
        preset_name = input("Enter the name of the preset to remove: ").strip()
        confirm = input(f"Are you sure you want to remove '{preset_name}'? (y/n): ").lower()
        self.controller.handle_remove_preset(preset_name, confirm == 'y')

    def prompt_generate_report(self):
        preset_name = input("Enter preset name: ").strip()
        department = input("Enter department: ").strip()
        self.controller.handle_generate_report(preset_name, department)

    def display_success(self, message):
        print(f"Success: {message}")

    def display_error(self, message):
        print(f"Error: {message}")

    def display_invalid_option(self):
        print("Invalid option. Please try again.")

    def display_exit(self):
        print("Goodbye!")