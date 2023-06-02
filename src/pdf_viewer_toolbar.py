import tkinter as tk

class PdfViewerToolbar(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent, bd=1, relief=tk.RAISED)
        self.pack(side=tk.TOP, fill=tk.X)

        self.buttons = {}
        self.add_button("Safe Area")
        self.add_button("Visibility")
        self.add_button("Merge & Split")
        self.add_button("Order")

        self.button_states = {name: False for name in self.buttons}

        self.toggle_button("Safe Area")

    def add_button(self, name):
        self.buttons[name] = tk.Button(self, text=name, command=lambda: self.toggle_button(name))
        self.buttons[name].pack(side='left', padx=2, pady=2)

    def toggle_button(self, name):
        # Reset all buttons
        for button_name, button_state in self.button_states.items():
            self.button_states[button_name] = False
            self.buttons[button_name].config(relief=tk.RAISED)

        # Toggle the clicked button
        self.button_states[name] = not self.button_states[name]
        if self.button_states[name]:
            self.buttons[name].config(relief=tk.SUNKEN)