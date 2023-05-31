import tkinter as tk

class DraggableListbox(tk.Listbox):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.bind("<Button-1>", self.on_drag_start)
        self.bind("<B1-Motion>", self.on_drag_motion)
        self.bind("<ButtonRelease-1>", self.on_drag_release)
        self._drag_data = {"index": None, "y": 0}

    def on_drag_start(self, event):
        """Beginning drag of an object"""
        # record the item's initial position
        self._drag_data["index"] = self.nearest(event.y)
        self._drag_data["y"] = event.y

    def on_drag_motion(self, event):
        """Handle dragging of an object"""
        delta_y = event.y - self._drag_data["y"]
        self._drag_data["y"] = event.y

    def on_drag_release(self, event):
        """End drag of an object"""
        # get the new position of the item
        new_position = self.nearest(event.y)
        # get the old position of the item
        old_position = self._drag_data["index"]
        if new_position is None or old_position is None:
            return
        # get the item
        item = self.get(old_position)
        # delete the item from its old position
        self.delete(old_position)
        # insert the item in its new position
        self.insert(new_position, item)
        # reset the drag information
        self._drag_data = {"index": None, "y": 0}