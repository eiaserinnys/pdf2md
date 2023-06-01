import tkinter as tk
from PIL import Image, ImageTk

class PdfCanvas(tk.Canvas):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.bind('<Motion>', self.on_mouse_move)
        self.elements = []

    def create_element(self, key, x1, y1, x2, y2, **kwargs):
        alpha = int(kwargs.pop('alpha', 1) * 255)
        fill = kwargs.pop('fill', 'white')
        fill = self.winfo_rgb(fill) + (alpha,)
        image = Image.new('RGBA', (int(x2-x1), int(y2-y1)), fill)
        image = ImageTk.PhotoImage(image)
        image_id = self.create_image(x1, y1, image=image, anchor='nw')
        self.itemconfig(image_id, state='hidden')  # initially hide the image

        rectangle = super().create_rectangle(x1, y1, x2, y2, **kwargs)

        self.elements.append((key, rectangle, image_id, image))

        return rectangle

    def get_image_extent(self, pix):
        window_width = max(self.winfo_width(), 1)  # ensure width is at least 1
        window_height = max(self.winfo_height(), 1)  # ensure height is at least 1

        window_ratio = window_width / window_height
        page_ratio = pix.width / pix.height

        if window_ratio < page_ratio:
            # Window is relatively taller than the page, so scale based on width
            new_width = window_width
            new_height = max(int(window_width / page_ratio), 1)  # ensure height is at least 1
        else:
            # Window is relatively wider than the page, so scale based on height
            new_height = window_height
            new_width = max(int(window_height * page_ratio), 1)  # ensure width is at least 1

        return new_width, new_height

    def is_inside_rectangle(self, x, y, rectangle):
        """Check if the point (x, y) is inside the given rectangle."""
        x1, y1, x2, y2 = self.coords(rectangle)
        return x1 <= x <= x2 and y1 <= y <= y2

    def on_mouse_move(self, event):
        """Handle mouse moving over the canvas."""
        x, y = self.canvasx(event.x), self.canvasy(event.y)
        for _, rectangle, image_id, _ in self.elements:
            if self.is_inside_rectangle(x, y, rectangle):
                self.itemconfig(image_id, state='normal')  # show image
            else:
                self.itemconfig(image_id, state='hidden')  # hide image

    def clear(self):
        self.delete('all')  # delete all canvas items
        self.elements = []  # clear rectangles list

    def show_page(self, pix, page_extent, safe_margin, elements):

        self.clear()

        page_width, page_height = page_extent

        # Convert the PyMuPDF page to PIL Image and resize to fit window
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img = img.resize((self.get_image_extent(pix)), Image.LANCZOS)

        # Convert the PIL Image to PhotoImage and show it on the Canvas
        self.photoimg = ImageTk.PhotoImage(img)
        self.create_image(0, 0, image=self.photoimg, anchor='nw')

        # Draw the pdfminer layout on the PIL Image
        scale_factor_x = img.width / page_width
        scale_factor_y = img.height / page_height

        #for element in pdfminer_page:
        for key, element in elements:
            x1, y1, x2, y2 = [x * scale_factor_x for x in element.bbox[:2]] + [x * scale_factor_y for x in element.bbox[2:]]

            x1, x2 = min(x1, x2), max(x1, x2)
            if x1 == x2:
                x2 = x1 + 1

            y1, y2 = min(img.height - y1, img.height - y2), max(img.height - y1, img.height - y2)
            if y1 == y2:
                y2 = y1 + 1

            # Create the rectangle and save the handle
            self.create_element(
                key, 
                x1, y1, x2, y2, 
                fill="green" if element.visible else "gray80", 
                outline="green" if element.visible else "gray80", 
                width=2 if element.visible else 1,
                alpha=0.25)

        safe_x1 = scale_factor_x * page_width * safe_margin.x1
        safe_x2 = scale_factor_x * page_width * safe_margin.x2
        safe_y1 = scale_factor_y * page_height * safe_margin.y1
        safe_y2 = scale_factor_y * page_height * safe_margin.y2
        super().create_rectangle(safe_x1, safe_y1, safe_x2, safe_y2, outline="red")
