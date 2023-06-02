import tkinter as tk
from PIL import Image, ImageTk
from src.draggable_rectangle import DraggableRectangle
from src.pdf import PdfRect

class PdfCanvas(tk.Canvas):
    def __init__(self, master=None, pdf=None, **kwargs):
        super().__init__(master, **kwargs)
        self.pdf = pdf
        
        self.bind('<Motion>', self.on_mouse_move)
        self.bind("<Configure>", self.on_resize)

        self.bind("<Button-1>", self.on_mouse_down)

        # bind mouse wheel events
        self.bind("<MouseWheel>", self.on_mouse_wheel)  # Windows
        self.bind("<Button-4>", self.on_scroll_up)      # linux
        self.bind("<Button-5>", self.on_scroll_down)    # linux

        # bind drag events
        self.bind("<<SafeAreaDragEnd>>", self.on_drag_end)

        self.current_page = 0
        self.elements = []

    def change_page(self, new_page_number):
        if new_page_number >= 0 and new_page_number < self.pdf.get_page_number():
            self.current_page = new_page_number
            self.redraw()
   
    def on_mouse_wheel(self, event):
        """Handle mouse wheel scrolling."""
        if event.delta > 0:
            self.change_page(self.current_page - 1)
        else:
            self.change_page(self.current_page + 1)

    def on_scroll_up(self, event):
        self.change_page(self.current_page - 1)

    def on_scroll_down(self, event):
        self.change_page(self.current_page + 1)

    def on_resize(self, event):
        self.redraw()

    def redraw(self):
        self.clear()
        self.show_page(
            self.pdf.get_pixmap(self.current_page),
            self.pdf.get_page_extent(self.current_page), 
            self.pdf.get_safe_margin(),
            self.pdf.iter_elements_page(self.current_page))

    def is_inside_rectangle(self, x, y, rectangle):
        """Check if the point (x, y) is inside the given rectangle."""
        x1, y1, x2, y2 = self.coords(rectangle)
        return x1 <= x <= x2 and y1 <= y <= y2

    def on_mouse_down(self, event):
        """Handle mouse moving over the canvas."""
        x, y = self.canvasx(event.x), self.canvasy(event.y)
        for key, rectangle, _, _ in self.elements:
            if self.is_inside_rectangle(x, y, rectangle):
                self.clicked_element = key
                self.event_generate("<<ElementClicked>>")

                # self.elements will be changed by <<ElementClicked>> event, so we need to break here
                break

    def get_clicked_element(self):
        return self.clicked_element

    def on_mouse_move(self, event):
        """Handle mouse moving over the canvas."""
        x, y = self.canvasx(event.x), self.canvasy(event.y)
        for _, rectangle, image_id, _ in self.elements:
            if self.is_inside_rectangle(x, y, rectangle):
                self.itemconfig(image_id, state='normal')  # show image
            else:
                self.itemconfig(image_id, state='hidden')  # hide image

    def clear(self):
        if hasattr(self, 'safe_area'):
            self.safe_area.delete()
            self.safe_area = None
        self.delete('all')  # delete all canvas items
        self.elements = []  # clear rectangles list
        self.photoimg = None

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

    def create_element(self, key, index, safe, visible, x1, y1, x2, y2):

        width = 1

        if safe:
            if visible:
                outline = fill = 'green'
                width = 2
            else:
                outline = fill = 'black'
        else:
            outline = fill = 'gray80'

        alpha = int(0.25 * 255)
        fill = self.winfo_rgb(fill) + (alpha,)
        
        image = Image.new('RGBA', (int(x2-x1), int(y2-y1)), fill)
        image = ImageTk.PhotoImage(image)
        image_id = self.create_image(x1, y1, image=image, anchor='nw')
        self.itemconfig(image_id, state='hidden')  # initially hide the image

        kwargs = { 'outline': outline, 'width': width }
        rectangle = super().create_rectangle(x1, y1, x2, y2, **kwargs)

        # Add text at the top left corner inside the rectangle.
        if safe and visible:
            text_id = self.create_text(x1 - 5 - width/2, y1 - width/2, text=str(index), anchor='ne', fill='white')  # Place the text 5 pixels away from the top left corner.
            text_bg = self.create_rectangle(self.bbox(text_id), fill="green")
            self.tag_lower(text_bg, text_id)

        self.elements.append((key, rectangle, image_id, image))
        return rectangle

    def show_page(self, pix, page_extent, safe_margin, elements):
        page_width, page_height = page_extent

        # Convert the PyMuPDF page to PIL Image and resize to fit window
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img = img.resize((self.get_image_extent(pix)), Image.LANCZOS)

        # Convert the PIL Image to PhotoImage and show it on the Canvas
        self.photoimg = ImageTk.PhotoImage(img)
        self.create_image(0, 0, image=self.photoimg, anchor='nw')

        # Draw the pdfminer layout on the PIL Image
        self.scale_factor_x = img.width / page_width
        self.scale_factor_y = img.height / page_height

        #for element in pdfminer_page:
        index = 1
        for key, element in elements:
            x1, y1, x2, y2 = element.bbox
            x1, x2 = sorted([x1 * self.scale_factor_x, x2 * self.scale_factor_x])
            x2 = max(x2, x1 + 1)  # Ensure x2 is always greater than x1

            y1, y2 = sorted([img.height - y1 * self.scale_factor_y, img.height - y2 * self.scale_factor_y])
            y2 = max(y2, y1 + 1)  # Ensure y2 is always greater than y1

            # Create the rectangle and save the handle
            self.create_element(
                key, 
                index, 
                element.safe, 
                element.visible, 
                x1, y1, x2, y2)
            
            if element.visible and element.safe:
                index += 1

        safe_x1 = self.scale_factor_x * page_width * safe_margin.x1
        safe_x2 = self.scale_factor_x * page_width * safe_margin.x2
        safe_y1 = self.scale_factor_y * page_height * safe_margin.y1
        safe_y2 = self.scale_factor_y * page_height * safe_margin.y2
        self.safe_area = DraggableRectangle(self, safe_x1, safe_y1, safe_x2, safe_y2, outline="red")

    def on_drag_end(self, event):
        # Update the safe_margin based on the new position of safe_area
        x1, y1, x2, y2 = self.coords(self.safe_area.rectangle)
        page_width, page_height = self.pdf.get_page_extent(self.current_page)
        
        self.new_safe_margin = PdfRect(
                x1 / self.scale_factor_x / page_width,
                y1 / self.scale_factor_y / page_height,
                x2 / self.scale_factor_x / page_width,
                y2 / self.scale_factor_y / page_height
            )
        
        self.event_generate("<<SafeAreaChanged>>")

    def get_new_safe_margin(self):
        return self.new_safe_margin