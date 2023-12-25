import customtkinter
class CTkNotification(customtkinter.CTkFrame):
    def __init__(self, text, master, **kwargs):
        self.master_color = master.cget("fg_color")
        super().__init__(master=master, **kwargs, fg_color=self.master_color)
        self.label = customtkinter.CTkLabel(self, text=text, text_color=self.master_color, width=200, wraplength=200, font=("Inter", 16))
        self.label.grid(row=0, column=0, sticky="nsew")
        self.close_button = customtkinter.CTkButton(
            self, width=40, text="X", text_color_disabled=self.master_color, command=self.hide, fg_color="transparent", state="disabled")
        self.close_button.grid(row=0, column=1)
        self.progress_bar = customtkinter.CTkProgressBar(self, determinate_speed=0.4, fg_color=self.master_color, progress_color=self.master_color)
        self.progress_bar.grid(row=1, column=0, columnspan=2, sticky="nsew")

    def hide(self):
        self.configure(fg_color="transparent")
        self.progress_bar.stop()
        self.progress_bar.configure(progress_color=self.master_color)
        self.close_button.configure(state="disabled")
        self.label.configure(text_color=self.master_color)

    def show(self):
        self.configure(fg_color="green")
        self.progress_bar.configure(progress_color="white")
        self.progress_bar.set(0)
        self.progress_bar.start()
        self.close_button.configure(state="normal")
        self.label.configure(text_color="white")