from dataclasses import dataclass, asdict

@dataclass
class PdfRect:
    x1: float
    y1: float
    x2: float
    y2: float

    def as_tuple(self):
        return self.x1, self.y1, self.x2, self.y2    

@dataclass
class PdfElement:
    page_number: int
    bbox: PdfRect
    org_text: str
    text: str
    mergable: bool
    safe: bool
    visible: bool
    translated: str = None
    children = None
    concat: bool = False
    marked: bool = False

    def can_be_split(self):
        return self.children != None and len(self.children) > 1
