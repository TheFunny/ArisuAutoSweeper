import customtkinter
import json
import sys
from MCE.custom_widgets.ctk_notification import CTkNotification

class Config:
    def __init__(self, linker, config_file):
        self.linker = linker
        self.config_file = config_file
        self.config_data = self.read()
        self.linker.widgets = self.set_values_to_none(self.config_data)
        self.locked = False
        linker.config = self

    def read(self):
        # Read the JSON file
        try:
            with open(self.config_file, 'r') as json_file:
                config_data = json.load(json_file)
            return config_data
        except FileNotFoundError:
            print(f"Config file '{self.config_file}' not found.")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"Invalid JSON format in '{self.config_file}'.")
            sys.exit(1)

    def set_values_to_none(self, input_dict):
        result = {}
        for key, value in input_dict.items():
            if isinstance(value, dict):
                result[key] = self.set_values_to_none(value)
            else:
                result[key] = None
        return result
    
    def load_config(self, widgets=None, config_data=None):
        if widgets == None:
            widgets = self.linker.widgets
            config_data = self.config_data
        for key in widgets:
            if isinstance(widgets[key], dict) and isinstance(config_data[key], dict):
                self.load_config(widgets[key], config_data[key])
            else:
                if widgets[key] is not None:
                    if isinstance(widgets[key], customtkinter.CTkCheckBox):
                        if config_data[key] == True:
                            widgets[key].select()
                        else:
                            widgets[key].deselect()
                    elif isinstance(widgets[key], customtkinter.CTkEntry):
                        widgets[key].insert(0, config_data[key])
                    else:                    
                        widgets[key].set(config_data[key])

    def save_to_json(self, list_keys):
        widget = self.linker.widgets
        data = self.config_data
        for i in list_keys[:-1]:
            widget = widget[i]
            data = data[i]
        widget = widget[list_keys[-1]] 
        value = widget.get()
        if isinstance(widget, customtkinter.CTkCheckBox):
            value = True if value==1 else False
        data[list_keys[-1]] = value
        self.save_file("Configuration")

    def save_file(self, name=None):
        if self.locked:
            with open("MCE\config.json", "r") as config_file:
                new_config = json.load(config_file)
            self.config_data["Queue"] = new_config["Queue"]
            self.config_data["LastRun"] = new_config["LastRun"]
        with open("MCE\config.json", "w") as config_file:
            json.dump(self.config_data, config_file, indent=2)
        if name:    
            self.linker.show_notification(name)
    
class Linker:
    def __init__(self):
        self.capitalise = lambda word: " ".join(x.title() for x in word.split("_"))        
        self.config = None
        self.widgets = {}
        self.sidebar = None
        self.event_id = None

    def show_notification(self, text):
        if self.event_id:
            self.sidebar.after_cancel(self.event_id)
        self.sidebar.notification.show()
        self.event_id = self.sidebar.after(2500, self.sidebar.notification.hide)
