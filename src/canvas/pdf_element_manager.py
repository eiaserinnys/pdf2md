from PIL import Image, ImageTk
from src.canvas.element_setting import get_setting
from src.canvas.utility import check_overlap

class PdfElementManager:
    def __init__(self, canvas):
        self.canvas = canvas
        self.elements = []
        self.selected_elements = []

    def add(self, key, rectangle, image_id, image):
        self.elements.append((key, rectangle, image_id, image))

    def clear(self):
        self.elements = []
        self.selected_elements = []

    def get(self):
        return self.elements

    def get_selected(self):
        return self.selected_elements

    def find_by_key(self, key):
        return next((element for element in self.elements if element[0] == key), None)

    def find_by_point(self, x, y):
        return next((element for element in self.elements if self.is_inside_rectangle(x, y, element[1])), None)

    def add_element(self, mode, key, index, safe, visible, x1, y1, x2, y2):
        settings = get_setting(mode, safe, visible)
        outline = settings['outline']
        fill = settings['fill']
        dash = settings.get('dash')
        width = settings.get('width')

        # Add text at the top left corner inside the rectangle.
        if safe and visible:
            text_id = self.canvas.create_text(x1 - 5 - width/2, y1 - width/2, text=str(index), anchor='ne', fill='white')  # Place the text 5 pixels away from the top left corner.
            text_bg = self.canvas.create_rectangle(self.canvas.bbox(text_id), fill=fill)
            self.canvas.tag_lower(text_bg, text_id)

        alpha = int(0.25 * 255)
        fill = self.canvas.winfo_rgb(fill) + (alpha,)
        
        image = Image.new('RGBA', (int(x2-x1), int(y2-y1)), fill)
        image = ImageTk.PhotoImage(image)
        image_id = self.canvas.create_image(x1, y1, image=image, anchor='nw')
        self.canvas.itemconfig(image_id, state='hidden')  # initially hide the image

        # create rectangle
        kwargs = { 'outline': outline, 'width': width }
        if dash is not None:
            kwargs.update({ 'dash': dash })
        rectangle = self.canvas.create_rectangle(x1, y1, x2, y2, **kwargs)

        self.elements.append((key, rectangle, image_id, image))
        return rectangle

    def is_inside_rectangle(self, x, y, rectangle):
        """Check if the point (x, y) is inside the given rectangle."""
        x1, y1, x2, y2 = self.canvas.coords(rectangle)
        return x1 <= x <= x2 and y1 <= y <= y2

    def update_hover(self, x, y):
        for _, rectangle, image_id, _ in self.elements:
            if self.is_inside_rectangle(x, y, rectangle):
                self.canvas.itemconfig(image_id, state='normal')  # show image
            else:
                self.canvas.itemconfig(image_id, state='hidden')  # hide image

    def update_drag(self, drag_id):
        self.selected_elements = []

        if drag_id is not None:
            drag_rect = self.canvas.coords(drag_id)
            for key, rectangle, image_id, _ in self.elements:
                element_rect = self.canvas.coords(rectangle)
                if check_overlap(drag_rect, element_rect):
                    self.canvas.itemconfig(image_id, state='normal')  # show image
                    self.selected_elements.append(key)
                else:
                    self.canvas.itemconfig(image_id, state='hidden')  # hide image
        else:
            for _, rectangle, image_id, _ in self.elements:
                self.canvas.itemconfig(image_id, state='hidden')  # hide image
