import customtkinter
import tkinter as tk

class CTkTimeEntry(customtkinter.CTkFrame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.hour = tk.StringVar()
        self.minute = tk.StringVar()
        self.second = tk.StringVar()

        self.hour_entry = customtkinter.CTkEntry(self, width=50, textvariable=self.hour, validate="key", validatecommand=(self.register(self.validate_hour), '%P'))
        self.hour_entry.pack(side=tk.LEFT)

        self.minute_entry = customtkinter.CTkEntry(self,width=50, textvariable=self.minute, validate="key", validatecommand=(self.register(self.validate_min_sec), '%P'))
        self.minute_entry.pack(side=tk.LEFT)

        self.second_entry = customtkinter.CTkEntry(self, width=50, textvariable=self.second, validate="key", validatecommand=(self.register(self.validate_min_sec), '%P'))
        self.second_entry.pack(side=tk.LEFT)

    def validate_hour(self, P):
        return len(P) <= 2 and (P.isdigit() and int(P) <= 23 or P == "")

    def validate_min_sec(self, P):
        return len(P) <= 2 and (P.isdigit() and int(P) <= 59 or P == "")

    def set(self, time_str):
        h, m, s = map(str, time_str.split(':'))
        self.hour.set(h)
        self.minute.set(m)
        self.second.set(s)

    def get(self):
        h = self.hour.get() if self.hour.get() else "00"
        m = self.minute.get() if self.minute.get() else "00"
        s = self.second.get() if self.second.get() else "00"
        return f"{h.zfill(2)}:{m.zfill(2)}:{s.zfill(2)}"