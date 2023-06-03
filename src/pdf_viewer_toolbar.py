import tkinter as tk
from src.pdf_viewer_toolbar_item import PdfViewerToolbarItem

class PdfViewerToolbar(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent, bd=1, relief=tk.RAISED)
        self.pack(side=tk.TOP, fill=tk.X)

        self.buttons = {}
        for item in PdfViewerToolbarItem:
            self.add_button(item)

        self.button_states = {item: False for item in self.buttons}

        self.current_selection = None

    def add_button(self, item):
        self.buttons[item] = tk.Button(self, text=item.display_name, command=lambda item=item: self.toggle_button(item))
        self.buttons[item].pack(side='left', padx=2, pady=2)

    def toggle_button(self, item):
        # Reset all buttons
        for button_item, button_state in self.button_states.items():
            self.button_states[button_item] = False
            self.buttons[button_item].config(relief=tk.RAISED)

        # Toggle the clicked button
        self.button_states[item] = not self.button_states[item]
        if self.button_states[item]:
            self.buttons[item].config(relief=tk.SUNKEN)

        self.current_selection = item

        self.event_generate("<<ToolbarButtonClicked>>", when="tail")

    def get_current_selection(self):
        return self.current_selection