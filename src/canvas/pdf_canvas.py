import tkinter as tk
from PIL import Image, ImageTk
from src.pdf import PdfRect
from src.toolbar.pdf_viewer_toolbar_item import PdfViewerToolbarItem
from src.canvas.pdf_element_manager import PdfElementManager
from src.canvas.draggable_rectangle import DraggableRectangle
from src.canvas.utility import get_image_extent

class PdfCanvas(tk.Canvas):
    def __init__(self, master=None, pdf=None, **kwargs):
        super().__init__(master, **kwargs)
        self.pdf = pdf
        
        self.bind('<Motion>', self.on_mouse_move)
        self.bind("<Configure>", self.on_resize)
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
        self.elm = PdfElementManager(self)

        self.mode = None
        self.drag_enabled = False

    def change_page(self, new_page_number):
        if new_page_number >= 0 and new_page_number < self.pdf.get_page_number():
            self.current_page = new_page_number
            self.redraw()

    def get_current_page(self):
        return self.current_page

    def change_mode(self, new_mode):
        self.mode = new_mode
        if self.mode == PdfViewerToolbarItem.Visibility or self.mode == PdfViewerToolbarItem.MergeAndSplit:
            self.drag_enabled = True
        else:
            self.drag_enabled = False
        self.redraw()
   
    def redraw(self):
        self.clear()
        self.show_page(
            self.pdf.get_pixmap(self.current_page),
            self.pdf.get_page_extent(self.current_page), 
            self.pdf.get_safe_margin(),
            self.pdf.iter_elements_page(self.current_page))

    def clear(self):
        if hasattr(self, 'safe_area') and self.safe_area is not None:
            self.safe_area.delete()
            self.safe_area = None
        self.delete('all')  # delete all canvas items
        self.elm.clear()
        self.photoimg = None

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
            self.elm.add_element(
                self.mode, 
                key, 
                index, 
                element.safe, 
                element.visible, 
                element.can_be_split(),
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

            self.elm.update_drag(self.drag_data["item"])

    def on_drag_stop(self, event):
        """End drag of an object"""
        if self.drag_enabled:
            if self.drag_data["item"] is not None:
                # drag is finished, so we need to update the drag overlap
                self.elm.update_drag(self.drag_data["item"])
                self.event_generate("<<DragEnd>>")
                self.delete(self.drag_data["item"])
            else:
                # mouse is not moved, so it is a click
                x, y = self.canvasx(event.x), self.canvasy(event.y)
                found = self.elm.find_by_point(x, y)
                self.clicked_element = found[0] if found is not None else None
                self.event_generate("<<ElementLeftClicked>>")

            # reset the drag information
            self.drag_data["item"] = None
            self.drag_data["x"] = 0
            self.drag_data["y"] = 0

    def on_mouse_rb_down(self, event):
        """Handle mouse moving over the canvas."""
        x, y = self.canvasx(event.x), self.canvasy(event.y)
        found = self.elm.find_by_point(x, y)
        self.clicked_element = found[0] if found is not None else None
        self.event_generate("<<ElementRightClicked>>")
       
    def get_clicked_element(self):
        return self.clicked_element
    
    def get_selected_elements(self):
        return self.elm.get_selected()

    def on_mouse_move(self, event):
        """Handle mouse moving over the canvas."""
        x, y = self.canvasx(event.x), self.canvasy(event.y)
        self.elm.update_hover(x, y)

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