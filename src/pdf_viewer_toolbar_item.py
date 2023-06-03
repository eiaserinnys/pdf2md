from enum import Enum, auto

class PdfViewerToolbarItem(Enum):
    SafeArea = auto(), "Safe Area"
    Visibility = auto(), "Visibility"
    MergeAndSplit = auto(), "Merge & Split"
    Order = auto(), "Order"

    # Override the __new__ method to store the display name in addition to the default Enum value
    def __new__(cls, value, display_name):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.display_name = display_name
        return obj