import tkinter as tk
from PIL import Image, ImageTk
from src.draggable_rectangle import DraggableRectangle
from src.pdf import PdfRect
from src.pdf_viewer_toolbar_item import PdfViewerToolbarItem
from src.element_setting import get_setting
from src.utility import check_overlap, get_image_extent

class PdfCanvas(tk.Canvas):
    def __init__(self, master=None, pdf=None, **kwargs):
        super().__init__(master, **kwargs)
        self.pdf = pdf
        
        self.bind('<Motion>', self.on_mouse_move)
        self.bind("<Configure>", self.on_resize)

        self.bind("<Button-1>", self.on_mouse_lb_down)
        self.bind("<Button-3>", self.on_mouse_rb_down)

        self.drag_data = {"x": 0, "y": 0, "item": None}
        self.bind("<ButtonPress-1>", self.on_drag_start)
        self.bind("<B1-Motion>", self.on_drag_motion)
        self.bind("<ButtonRelease-1>", self.on_drag_stop)

        # bind mouse wheel events
        self.bind("<MouseWheel>", self.on_mouse_wheel)  # Windows
        self.bind("<Button-4>", self.on_scroll_up)      # linux
        self.bind("<Button-5>", self.on_scroll_down)    # linux

        # bind drag events
        self.bind("<<SafeAreaDragEnd>>", self.on_safe_area_drag_end)

        self.current_page = 0
        self.elements = []

        self.mode = None
        self.drag_enabled = False

    def change_page(self, new_page_number):
        if new_page_number >= 0 and new_page_number < self.pdf.get_page_number():
            self.current_page = new_page_number
            self.redraw()

    def change_mode(self, new_mode):
        self.mode = new_mode
        if self.mode == PdfViewerToolbarItem.Visibility:
            self.drag_enabled = True
        else:
            self.drag_enabled = False
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

    def on_drag_start(self, event):
        """Begining drag of an object"""
        if self.drag_enabled:
            # record the item and its location
            self.drag_data["item"] = None   # we do not consider it as drag until the mouse is moved
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y

    def on_drag_motion(self, event):
        """Handle dragging of an object"""
        if self.drag_enabled:
            # compute how much the mouse has moved
            delta_x = event.x - self.drag_data["x"]
            delta_y = event.y - self.drag_data["y"]
            
            if self.drag_data["item"] is None:
                # now we begin drag
                self.drag_data["item"] = self.create_rectangle(
                    self.canvasx(event.x), self.canvasy(event.y), 
                    self.canvasx(event.x) + delta_x, self.canvasy(event.y) + delta_y, 
                    outline="green",
                    dash = (5, 3))
            else:
                self.coords(
                    self.drag_data["item"], 
                    self.canvasx(self.drag_data["x"]), self.canvasy(self.drag_data["y"]), 
                    self.canvasx(self.drag_data["x"]) + delta_x, self.canvasy(self.drag_data["y"]) + delta_y)

            self.update_drag_overlap()

    def on_drag_stop(self, event):
        """End drag of an object"""
        if self.drag_enabled:
            if self.drag_data["item"] is not None:
                # drag is finished, so we need to update the drag overlap
                self.update_drag_overlap()
                self.event_generate("<<DragEnd>>")
                self.delete(self.drag_data["item"])
            else:
                # mouse is not moved, so it is a click
                x, y = self.canvasx(event.x), self.canvasy(event.y)
                for key, rectangle, _, _ in self.elements:
                    if self.is_inside_rectangle(x, y, rectangle):
                        self.clicked_element = key
                        self.event_generate("<<ElementLeftClicked>>")

                        # self.elements will be changed by <<ElementLeftClicked>> event, so we need to break here
                        break

            # reset the drag information
            self.drag_data["item"] = None
            self.drag_data["x"] = 0
            self.drag_data["y"] = 0

    def update_drag_overlap(self):
        self.selected_elements = []

        if self.drag_data["item"] is not None:
            drag_rect = self.coords(self.drag_data["item"])
            for key, rectangle, image_id, _ in self.elements:
                element_rect = self.coords(rectangle)
                if check_overlap(drag_rect, element_rect):
                    self.itemconfig(image_id, state='normal')  # show image
                    self.selected_elements.append(key)
                else:
                    self.itemconfig(image_id, state='hidden')  # hide image
        else:
            for _, rectangle, image_id, _ in self.elements:
                self.itemconfig(image_id, state='hidden')  # hide image

    def on_mouse_lb_down(self, event):
        """Handle mouse moving over the canvas."""
        x, y = self.canvasx(event.x), self.canvasy(event.y)
        for key, rectangle, _, _ in self.elements:
            if self.is_inside_rectangle(x, y, rectangle):
                self.clicked_element = key
                self.event_generate("<<ElementLeftClicked>>")

                # self.elements will be changed by <<ElementLeftClicked>> event, so we need to break here
                break

    def on_mouse_rb_down(self, event):
        """Handle mouse moving over the canvas."""
        x, y = self.canvasx(event.x), self.canvasy(event.y)
        for key, rectangle, _, _ in self.elements:
            if self.is_inside_rectangle(x, y, rectangle):
                self.clicked_element = key
                self.event_generate("<<ElementRightClicked>>")

                # self.elements will be changed by <<ElementRightClicked>> event, so we need to break here
                break

    def get_clicked_element(self):
        return self.clicked_element
    
    def get_selected_elements(self):
        return self.selected_elements

    def on_mouse_move(self, event):
        """Handle mouse moving over the canvas."""
        x, y = self.canvasx(event.x), self.canvasy(event.y)
        for _, rectangle, image_id, _ in self.elements:
            if self.is_inside_rectangle(x, y, rectangle):
                self.itemconfig(image_id, state='normal')  # show image
            else:
                self.itemconfig(image_id, state='hidden')  # hide image

    def clear(self):
        if hasattr(self, 'safe_area') and self.safe_area is not None:
            self.safe_area.delete()
            self.safe_area = None
        self.delete('all')  # delete all canvas items
        self.elements = []  # clear rectangles list
        self.photoimg = None

    # Using the table:
    def create_element(self, key, index, safe, visible, x1, y1, x2, y2):

        settings = get_setting(self.mode, safe, visible)
        outline = settings['outline']
        fill = settings['fill']
        dash = settings.get('dash')
        width = settings.get('width')

        # Add text at the top left corner inside the rectangle.
        if safe and visible:
            text_id = self.create_text(x1 - 5 - width/2, y1 - width/2, text=str(index), anchor='ne', fill='white')  # Place the text 5 pixels away from the top left corner.
            text_bg = self.create_rectangle(self.bbox(text_id), fill=fill)
            self.tag_lower(text_bg, text_id)

        alpha = int(0.25 * 255)
        fill = self.winfo_rgb(fill) + (alpha,)
        
        image = Image.new('RGBA', (int(x2-x1), int(y2-y1)), fill)
        image = ImageTk.PhotoImage(image)
        image_id = self.create_image(x1, y1, image=image, anchor='nw')
        self.itemconfig(image_id, state='hidden')  # initially hide the image

        # create rectangle
        kwargs = { 'outline': outline, 'width': width }
        if dash is not None:
            kwargs.update({ 'dash': dash })
        rectangle = super().create_rectangle(x1, y1, x2, y2, **kwargs)

        self.elements.append((key, rectangle, image_id, image))
        return rectangle

    def show_page(self, pix, page_extent, safe_margin, elements):
        page_width, page_height = page_extent

        # Convert the PyMuPDF page to PIL Image and resize to fit window
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img = img.resize((get_image_extent(self, pix)), Image.LANCZOS)

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

        if self.mode == PdfViewerToolbarItem.SafeArea:
            self.safe_area = DraggableRectangle(self, safe_x1, safe_y1, safe_x2, safe_y2, outline="red", width=2, dash=(5, 3))
        else:
            self.create_rectangle(safe_x1, safe_y1, safe_x2, safe_y2, outline="gray40", dash=(5, 3))

    def on_safe_area_drag_end(self, event):
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