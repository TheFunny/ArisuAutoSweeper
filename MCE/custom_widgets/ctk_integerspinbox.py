import customtkinter
import re
from typing import Callable

class CTkIntegerSpinbox(customtkinter.CTkFrame):
    def __init__(self, *args,
                 width: int = 100,
                 height: int = 32,
                 step_size: int = 1,
                 min_value: int = 0,
                 command: Callable = None,
                 **kwargs):
        super().__init__(*args, width=width, height=height, **kwargs)

        self.step_size = step_size
        self.min_value = min_value
        self.command = command
        self.after_id = None

        self.grid_columnconfigure((0, 2), weight=0)
        self.grid_columnconfigure(1, weight=1)

        self.subtract_button = customtkinter.CTkButton(self, text="-", width=height-6, height=height-6)
        self.subtract_button.grid(row=0, column=0, padx=(3, 0), pady=3)
        self.subtract_button.bind('<ButtonPress-1>', self.start_decrementing)
        self.subtract_button.bind('<ButtonRelease-1>', self.stop_decrementing)

        self.entry = customtkinter.CTkEntry(self, width=width-(2*height), height=height-6, border_width=0)
        self.entry.grid(row=0, column=1, columnspan=1, padx=3, pady=3, sticky="ew")

        self.add_button = customtkinter.CTkButton(self, text="+", width=height-6, height=height-6)
        self.add_button.grid(row=0, column=2, padx=(0, 3), pady=3)
        self.add_button.bind('<ButtonPress-1>', self.start_incrementing)
        self.add_button.bind('<ButtonRelease-1>', self.stop_incrementing)

        self.entry.insert(0, "0")
        
        # Configure validatecommand to allow only integers
        vcmd = (self.entry.register(self.validate_input), '%P')
        self.entry.configure(validate='key', validatecommand=vcmd)

    def start_incrementing(self, event):
        self.increment()
        self.after_id = self.after(150, self.start_incrementing, event)

    def stop_incrementing(self, event):
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None

    def start_decrementing(self, event):
        self.decrement()
        self.after_id = self.after(150, self.start_decrementing, event)

    def stop_decrementing(self, event):
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None

    def increment(self):
        value = int(self.entry.get()) + self.step_size
        self.entry.delete(0, "end")
        self.entry.insert(0, max(self.min_value, value))  # Ensure the value is not less than 1
        if self.command is not None:
            self.command()

    def decrement(self):
        value = int(self.entry.get()) - self.step_size
        self.entry.delete(0, "end")
        self.entry.insert(0, max(self.min_value, value))  # Ensure the value is not less than 0
        if self.command is not None:
            self.command()

    def validate_input(self, new_value):
        # Validate that the input is a non-negative integer
        return re.match(r'^\d*$', new_value) is not None

    def get(self) -> int:
        try:
            return int(self.entry.get())
        except ValueError:
            return 0

    def set(self, value: int):
        self.entry.delete(0, "end")
        self.entry.insert(0, max(self.min_value, value))  # Ensure the value is not less than 0

    def configure(self, **kwargs):
        state = kwargs.get("state", None)
        if state is not None:
            self.subtract_button.configure(state=state)
            self.add_button.configure(state=state)
            self.entry.configure(state=state)
            kwargs.pop("state")
        super().configure(**kwargs)