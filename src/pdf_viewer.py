import fitz  # PyMuPDF
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from pdfminer.layout import LTTextBox, LTImage, LTFigure
from pdfminer.high_level import extract_pages
from src.draggable_treeview import DraggableTreeview
from src.pdf import Pdf
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
        self.canvas = tk.Canvas(self.paned_window)
        self.canvas.bind('<Motion>', self.on_mouse_move)
        self.canvas.bind("<Configure>", self.on_resize)
        self.paned_window.add(self.canvas)

        # Initialize Text widget
        self.dlb = DraggableTreeview(self.paned_window)
        self.dlb.bind("<<TreeviewSelect>>", self.on_treeview_select)  # Add this line

        for key, element in self.pdf.iter_elements():
            if element.visible:
                self.dlb.insert('', "end", key, values=(element.page_number, element.text))

        self.dlb.pack(fill="both", expand=True)
        self.paned_window.add(self.dlb)

        # List to hold rectangle handles
        self.rectangles = []

        # Set the minimum size of the Text widget to 60% of the window width
        self.paned_window.update()
        self.paned_window.sashpos(0, 600)

    def on_treeview_select(self, event):
        selected_item = self.dlb.selection()[0]  # Get the selected item
        page_number, _ = self.dlb.item(selected_item, "values")  # Extract the page number
        self.current_page = int(page_number) - 1  # Update the current page
        self.redraw()  # Redraw the page

    def create_rectangle(self, x1, y1, x2, y2, **kwargs):
        alpha = int(kwargs.pop('alpha', 1) * 255)
        fill = kwargs.pop('fill', 'white')
        fill = self.winfo_rgb(fill) + (alpha,)
        image = Image.new('RGBA', (int(x2-x1), int(y2-y1)), fill)
        image = ImageTk.PhotoImage(image)
        image_id = self.canvas.create_image(x1, y1, image=image, anchor='nw')
        self.canvas.itemconfig(image_id, state='hidden')  # initially hide the image

        rectangle = self.canvas.create_rectangle(x1, y1, x2, y2, **kwargs)

        self.rectangles.append((rectangle, image_id, image))

        return rectangle
    
    def redraw(self):
        self.canvas.delete('all')  # delete all canvas items
        self.rectangles = []  # clear rectangles list
        self.show_page()

    def on_resize(self, event):
        """Handle window resizing."""
        self.redraw()

    def get_image_extent(self):
        window_width = max(self.canvas.winfo_width(), 1)  # ensure width is at least 1
        window_height = max(self.canvas.winfo_height(), 1)  # ensure height is at least 1

        window_ratio = window_width / window_height

        page_ratio = self.pdf.get_page_ratio(self.current_page)

        if window_ratio < page_ratio:
            # Window is relatively taller than the page, so scale based on width
            new_width = window_width
            new_height = max(int(window_width / page_ratio), 1)  # ensure height is at least 1
        else:
            # Window is relatively wider than the page, so scale based on height
            new_height = window_height
            new_width = max(int(window_height * page_ratio), 1)  # ensure width is at least 1

        return new_width, new_height

    def show_page(self):
        # Get page from PyMuPDF and pdfminer
        page_width, page_height = self.pdf.get_page_extent(self.current_page)
        safe_margin = self.pdf.get_safe_margin()

        # Convert the PyMuPDF page to PIL Image and resize to fit window
        pix = self.pdf.get_pixmap(self.current_page)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img = img.resize((self.get_image_extent()), Image.LANCZOS)

        # Convert the PIL Image to PhotoImage and show it on the Canvas
        self.photoimg = ImageTk.PhotoImage(img)
        self.canvas.create_image(0, 0, image=self.photoimg, anchor='nw')

        # Draw the pdfminer layout on the PIL Image
        #img_draw = ImageDraw.Draw(img)
        scale_factor_x = img.width / page_width
        scale_factor_y = img.height / page_height
        self.rectangles = []
        self.images = []

        #for element in pdfminer_page:
        for _, element in self.pdf.iter_elements_page(self.current_page):
            x1, y1, x2, y2 = [x * scale_factor_x for x in element.bbox[:2]] + [x * scale_factor_y for x in element.bbox[2:]]

            x1, x2 = min(x1, x2), max(x1, x2)
            if x1 == x2:
                x2 = x1 + 1

            y1, y2 = min(img.height - y1, img.height - y2), max(img.height - y1, img.height - y2)
            if y1 == y2:
                y2 = y1 + 1

            # Create the rectangle and save the handle
            self.create_rectangle(
                x1, y1, x2, y2, 
                fill="green" if element.visible else "gray80", 
                outline="green" if element.visible else "gray80", 
                width=2 if element.visible else 1,
                alpha=0.25)

        safe_x1 = scale_factor_x * page_width * safe_margin.x1
        safe_x2 = scale_factor_x * page_width * safe_margin.x2
        safe_y1 = scale_factor_y * page_height * safe_margin.y1
        safe_y2 = scale_factor_y * page_height * safe_margin.y2
        self.canvas.create_rectangle(safe_x1, safe_y1, safe_x2, safe_y2, outline="red")

    def is_inside_rectangle(self, x, y, rectangle):
        """Check if the point (x, y) is inside the given rectangle."""
        x1, y1, x2, y2 = self.canvas.coords(rectangle)
        return x1 <= x <= x2 and y1 <= y <= y2

    def on_mouse_move(self, event):
        """Handle mouse moving over the canvas."""
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        for rectangle, image_id, _ in self.rectangles:
            if self.is_inside_rectangle(x, y, rectangle):
                self.canvas.itemconfig(image_id, state='normal')  # show image
            else:
                self.canvas.itemconfig(image_id, state='hidden')  # hide image
