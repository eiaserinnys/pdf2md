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
        self.current_page = 0

        # Create a PanedWindow with horizontal orientation
        self.paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill='both', expand=1)

        # Initialize Canvas
        self.canvas = PdfCanvas(self.paned_window)
        self.canvas.bind("<Configure>", self.on_resize)
        self.paned_window.add(self.canvas)

        # Initialize Text widget
        self.dtv = DraggableTreeview(self.paned_window)
        self.dtv.bind("<<TreeviewSelect>>", self.on_treeview_select)

        # Add elements to the DraggableTreeview
        for key, element in self.pdf.iter_elements():
            if element.visible:
                self.dtv.insert('', "end", key, values=(element.page_number, element.text))

        self.dtv.pack(fill="both", expand=True)
        self.paned_window.add(self.dtv)

        # Set the minimum size of the Text widget to 60% of the window width
        self.paned_window.update()
        self.paned_window.sashpos(0, 600)

    def on_treeview_select(self, event):
        # Get the selected item
        selected_item = self.dtv.selection()[0]

        # Extract the page number from the selected item
        page_number, _ = self.dtv.item(selected_item, "values")
        self.current_page = int(page_number) - 1

        # Redraw the canvas
        self.redraw()
   
    def on_resize(self, event):
        """Handle window resizing."""
        self.redraw()

    def redraw(self):
        self.canvas.show_page(
            self.pdf.get_pixmap(self.current_page),
            self.pdf.get_page_extent(self.current_page), 
            self.pdf.get_safe_margin(),
            self.pdf.iter_elements_page(self.current_page))
