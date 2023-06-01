import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from src.draggable_treeview import DraggableTreeview
from src.pdf import Pdf
from src.pdf_canvas import PdfCanvas
from src.utility import check_overlap

class PDFViewer(tk.Frame):
    def __init__(self, pdf_path, master=None):
        super().__init__(master)
        self.master = master
        self.pack(fill='both', expand=1)

        # Load the PDF with PyMuPDF and pdfminer
        self.pdf = Pdf(pdf_path)

        # Create a PanedWindow with horizontal orientation
        self.paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill='both', expand=1)

        # Initialize Canvas
        self.canvas = PdfCanvas(self.paned_window, self.pdf)
        self.paned_window.add(self.canvas)
        self.canvas.bind("<<SafeAreaChanged>>", self.on_safe_area_changed)

        # Initialize Text widget
        self.dtv = DraggableTreeview(self.paned_window)
        self.dtv.bind("<<TreeviewSelect>>", self.on_treeview_select)

        # Add elements to the DraggableTreeview
        self.add_elements_to_treeview()

        self.dtv.pack(fill="both", expand=True)
        self.paned_window.add(self.dtv)

        # Set the minimum size of the Text widget to 60% of the window width
        self.paned_window.update()
        self.paned_window.sashpos(0, 600)

    def add_elements_to_treeview(self):
        for key, element in self.pdf.iter_elements():
            if element.visible:
                self.dtv.insert('', "end", key, values=(element.page_number, element.text))

    def on_treeview_select(self, event):
        # Get the selected item
        selected_item = self.dtv.selection()[0]

        # Extract the page number from the selected item
        page_number, _ = self.dtv.item(selected_item, "values")

        self.canvas.change_page(int(page_number) - 1)

    def on_safe_area_changed(self, event):
        for item in self.dtv.get_children():
            self.dtv.delete(item)

        self.add_elements_to_treeview()