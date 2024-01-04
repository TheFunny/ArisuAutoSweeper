import customtkinter

class CTkAddButton(customtkinter.CTkFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.button = customtkinter.CTkButton(self, text="Add Down", corner_radius=0, width=120)
        self.button.grid(row=0, column=0)
        self.option_menu = customtkinter.CTkOptionMenu(
            self, values= ["Add Up", "Add Down"], width=10, command=self.set_button, corner_radius=0
            )
        self.option_menu.set("")
        self.option_menu.grid(row=0, column=1)

    def set_button(self, value):
        self.option_menu.set("")
        self.button.configure(text=value)