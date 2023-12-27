import customtkinter
import json
from MCE.custom_widgets.ctk_scrollable_dropdown import CTkScrollableDropdown
import os
from tkinter import END

class InputHelper(customtkinter.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.create_tabview()
        self.create_invite_student_widgets()
        self.create_lessons_widgets()


    def create_tabview(self):
        self.tabview = customtkinter.CTkTabview(master=self)
        self.tabview.grid(row=0, column=0)

        self.cafe_tab = self.tabview.add("Cafe")  # add tab at the end
        self.lessons_tab = self.tabview.add("Lessons")  # add tab at the end
        self.tabview.set("Cafe")  # set currently visible 

    def create_invite_student_widgets(self):
        self.invitation_label = customtkinter.CTkLabel(master=self.cafe_tab, text="Copy and paste this in AAS Invitation Settings:")
        self.invitation_label.grid(row=0, column=0, padx=60)

        self.invitation_entry = customtkinter.CTkEntry(master=self.cafe_tab, width=500)
        self.invitation_entry.grid(row=1, column=0)

        self.invite_copy_button = customtkinter.CTkButton(master=self.cafe_tab, text="Copy", width=40, command=lambda : self.copy_entry(self.invitation_entry, self.invite_copy_button))
        self.invite_copy_button.grid(row=1, column=3, padx=5)

        self.invite_clear_button = customtkinter.CTkButton(master=self.cafe_tab, text="Clear", width=40, fg_color="crimson", command=lambda : self.invitation_entry.delete(0, END))
        self.invite_clear_button.grid(row=1, column=4, padx=5)

        self.invite_frame = customtkinter.CTkFrame(master=self.cafe_tab, fg_color="transparent")
        self.invite_frame.grid(row=2, column=0, padx=20, pady=20)

        self.server_dropdown = customtkinter.CTkOptionMenu(master=self.invite_frame, values=self.find_json_files("MCE/student_list"), command=self.switch_server, width=40)
        self.server_dropdown.grid(row=0, column=0)

        self.student_entry = customtkinter.CTkComboBox(master=self.invite_frame, width=300)
        self.student_entry.grid(row=0, column=1, padx=(50,0))

        self.student_dropdown = CTkScrollableDropdown(self.student_entry, width=300, height=550, autocomplete=True, command=lambda choice: self.insert(choice, self.invitation_entry), values=[""])
        self.server_dropdown.set("EN")
        self.switch_server("EN")

    def create_lessons_widgets(self):
        self.lessons_label = customtkinter.CTkLabel(master=self.lessons_tab, text="Copy and paste this in AAS Lessons Settings:")
        self.lessons_label.grid(row=0, column=0, padx=60)

        self.lessons_entry = customtkinter.CTkEntry(master=self.lessons_tab, width=500)
        self.lessons_entry.grid(row=1, column=0)
    
        self.lessons_copy_button = customtkinter.CTkButton(master=self.lessons_tab, text="Copy", width=40, command=lambda : self.copy_entry(self.lessons_entry, self.lessons_copy_button))
        self.lessons_copy_button.grid(row=1, column=1, padx=5)

        self.lessons_clear_button = customtkinter.CTkButton(master=self.lessons_tab, text="Clear", width=40, fg_color="crimson", command=lambda : self.lessons_entry.delete(0, END))
        self.lessons_clear_button.grid(row=1, column=2, padx=5)

        self.lessons_buttons_frame = customtkinter.CTkFrame(master=self.lessons_tab, fg_color="transparent")
        self.lessons_buttons_frame.grid(row=2, column=0, padx=20, pady=20)

        for i in range(9):
            self.lesson_button = customtkinter.CTkButton(master=self.lessons_buttons_frame, text=str(i+1), command=lambda choice=str(i+1): self.insert(choice, self.lessons_entry), width=40)
            self.lesson_button.grid(row=0, column=i, padx=5)


    def find_json_files(self,folder_path):
        json_files = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith(".json"):
                    json_files.append(os.path.splitext(file)[0])
        return json_files

    def switch_server(self, server):
        with open(f"MCE/student_list/{server}.json", "r") as f:
            student_list = json.load(f)
        self.student_dropdown.configure(values=student_list)

    def insert(self, value, entry):
        entry.insert(index=END, string=value + " > ")

    def copy_entry(self, entry, button):
        text_to_copy = entry.get()

        # Check if there is text to copy
        if text_to_copy:
            # Clear the clipboard and set the new text
            self.clipboard_clear()
            self.clipboard_append(text_to_copy)
            self.update()  # This is necessary on some systems to update the clipboard
            button_color = button.cget("fg_color")
            button.configure(fg_color="green")
            self.after(2000, lambda : button.configure(fg_color=['#3B8ED0', '#1F6AA5']))

if __name__ == "__main__":
    app = InputHelper()
    app.title("Input Helper")
    app.mainloop()
