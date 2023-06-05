from enum import Enum
from dataclasses import dataclass, asdict
from pdfminer.layout import LTTextBox, LTTextLine, LTImage, LTFigure

class PdfElementType(Enum):
    Line = 1,
    Text = 2,
    Image = 3,
    Figure = 4, 


@dataclass
class PdfRect:
    x1: float
    y1: float
    x2: float
    y2: float

    def as_tuple(self):
        return self.x1, self.y1, self.x2, self.y2    

class PdfElement:
    def __init__(self, page_number:int, type:PdfElementType, bbox, text:str, children:list = None):

        self.page_number = page_number
        self.type = type
        self.bbox = bbox
        self.text = text

        self.children = children
        self.safe = True
        self.visible = True
        self.translated = None
        self.__body = True
        self.contd = None           # continued
        self.marked = False

    @property
    def body(self):           # getter
        if self.type == PdfElementType.Image or self.type == PdfElementType.Figure:
            return False
        return self.__body
 
    @body.setter
    def body(self, value):    # setter
        if self.type != PdfElementType.Image and self.type != PdfElementType.Figure:
            self.__body = value

    @classmethod
    def from_pdfminer(cls, page_number:int, element:object):
        if isinstance(element, LTTextBox):
            children = []
            for line in element:
                children.append(PdfElement.from_pdfminer(page_number, line))

            return cls(page_number, PdfElementType.Text, element.bbox, PdfElement.refine_concatenated_text(element.get_text()), children)
        
        elif isinstance(element, LTTextLine):
            text = element.get_text()
            text = text.replace("\n", "")
            text = text.strip()
            return cls(page_number, PdfElementType.Line, element.bbox, text)

        elif isinstance(element, LTFigure):
            return cls(page_number, PdfElementType.Figure, element.bbox, "<<<figure>>>")

        elif isinstance(element, LTImage):
            return cls(page_number, PdfElementType.Image, element.bbox, "<<<image>>>")
        
        return None

    @classmethod
    def from_merge(cls, page_number, to_merge:list, concat_or_join:bool = True):

        if concat_or_join:
            
            prev = None
            text = ""

            for el in to_merge:
                if prev is None:
                    text = el.text
                else:
                    if prev.type == PdfElementType.Line:
                        if prev.text[-1] == "-":
                            text = text[:-1]
                            text += el.text
                        else:
                            text += " " + el.text
                    else:
                        text += " " + el.text
                prev = el

        else:
            text = '\n'.join([el.text for el in to_merge])

        merged_bbox = (
            min(el.bbox[0] for el in to_merge),
            min(el.bbox[1] for el in to_merge),
            max(el.bbox[2] for el in to_merge),
            max(el.bbox[3] for el in to_merge))

        return PdfElement(page_number, PdfElementType.Text, merged_bbox, text, to_merge)

    @staticmethod
    def refine_concatenated_text(text):
        text = text.replace("-\n", "")
        text = text.replace("\n", " ")
        text = text.strip()
        return text

    @staticmethod
    def can_be_created(element):
        return isinstance(element, LTTextBox) or isinstance(element, LTTextLine) or isinstance(element, LTImage) or isinstance(element, LTFigure)

    def can_be_merged(self):
        return self.type == PdfElementType.Text or self.type == PdfElementType.Line

    def can_be_translated(self):
        return (self.type == PdfElementType.Text or self.type == PdfElementType.Line) and self.translated is None

    def can_be_split(self):
        return self.children != None and len(self.children) > 1

    def toggle_continue(self):
        if self.contd is None:
            self.contd = 1
        elif self.contd == 1:
            self.contd = 2
        elif self.contd == 2:
            self.contd = None
        else:
            self.contd = None
