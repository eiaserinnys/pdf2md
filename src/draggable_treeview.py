from tkinter.font import Font
from tkinter import ttk

class DraggableTreeview(ttk.Treeview):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.bind("<Button-1>", self.on_drag_start)
        self.bind("<B1-Motion>", self.on_drag_motion)
        self.bind("<ButtonRelease-1>", self.on_drag_release)
        self._drag_data = {"item": None, "y": 0}

    def on_drag_start(self, event):
        """Beginning drag of an object"""
        # record the item's initial position
        self._drag_data["item"] = self.identify_row(event.y)
        self._drag_data["y"] = event.y

    def on_drag_motion(self, event):
        """Handle dragging of an object"""
        delta_y = event.y - self._drag_data["y"]
        self._drag_data["y"] = event.y

    def on_drag_release(self, event):
        """End drag of an object"""
        # get the new position of the item
        new_item = self.identify_row(event.y)
        # get the old position of the item
        old_item = self._drag_data["item"]
        if old_item is None or old_item == '':
            return

        # handle the case where the item is dropped above the first item
        if new_item == '':
            # get the list of items
            items = self.get_children('')
            # get the index of the first item
            first_item_index = self.index(items[0])
            # insert the item before the first item
            self.move(old_item, '', first_item_index)
        # handle the case where the item is dropped below the last item
        elif new_item is None:
            # insert the item at the end
            self.move(old_item, '', 'end')
        else:
            # get the index of the new item
            new_item_index = self.index(new_item)
            # insert the item before the new item
            self.move(old_item, '', new_item_index)
        # reset the drag information
        self._drag_data = {"item": None, "y": 0}