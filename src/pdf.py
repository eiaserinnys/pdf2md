import fitz  # PyMuPDF
from dataclasses import dataclass
import pdfplumber
from pdfminer.layout import LAParams, LTTextBox, LTImage, LTFigure
from pdfminer.high_level import extract_pages
from src.utility import check_overlap

class PdfPage:
    def __init__(self, page_number):
        self.page_number = page_number
        self.elements = {}

@dataclass
class PdfRect:
    x1: float
    y1: float
    x2: float
    y2: float

@dataclass
class PdfElement:
    page_number: int
    bbox: PdfRect
    text: str
    safe: bool
    visible: bool

class Pdf:
    def __init__(self, pdf_path):
        # Load the PDF with PyMuPDF and pdfminer
        self.doc = fitz.open(pdf_path)

        params = LAParams(
            line_overlap = 0.5, 
            char_margin = 2.0, 
            line_margin = 0.5, 
            word_margin = 0.1, 
            boxes_flow = 0.5, 
            detect_vertical = False, 
            all_texts = False)

        self.pdfminer_pages = list(extract_pages(pdf_path, laparams = params))

        # self.pdfplumber = pdfplumber.open(pdf_path)

        # for page in self.pdfplumber.pages:
        #     tables = page.find_tables()
        #     for table in tables:
        #         print(table.bbox.x0, table.bbox.y0, table.bbox.x1, table.bbox.y1)

        self.margin = PdfRect(0.15, 0.08, 0.85, 0.92)

        self.build_element_list()

        self.recalculate_safe_area()

    def build_element_list(self):
        self.pages = []

        index = 0
        for page_number, pdfminer_page in enumerate(self.pdfminer_pages):

            self.pages.append(PdfPage(page_number + 1))
            cur_page = self.pages[-1]

            for element in pdfminer_page:
                if isinstance(element, LTTextBox):
                    # for text_line in element:
                    text = element.get_text()
                    text = text.replace("-\n", "")
                    text = text.replace("\n", " ")
                    text = text.strip()
                    cur_page.elements[index] = PdfElement(page_number + 1, element.bbox, text, True, True)
                    index += 1
                elif isinstance(element, LTFigure):
                    cur_page.elements[index] = PdfElement(page_number + 1, element.bbox, "figure", True, True)
                    index += 1
                elif isinstance(element, LTImage):
                    cur_page.elements[index] = PdfElement(page_number + 1, element.bbox, "image", True, True)
                    index += 1

    def recalculate_safe_area(self):
        for page in self.pages:
            pdfminer_page = self.pdfminer_pages[page.page_number - 1]
            safe_area = (
                pdfminer_page.width * self.margin.x1, 
                pdfminer_page.height * (1 - self.margin.y2),
                pdfminer_page.width * self.margin.x2,
                pdfminer_page.height * (1 - self.margin.y1), 
            )
            for element in page.elements.values():
                element.safe = check_overlap(element.bbox, safe_area)

    def toggle_visibility(self, key):
        for page in self.pages:
            if key in page.elements:
                page.elements[key].visible = not page.elements[key].visible

    def iter_elements(self):
        """Generator method to iterate over elements safely."""
        for page in self.pages:
            for key, element in page.elements.items():
                yield key, element

    def iter_elements_page(self, page_number):
        """Generator method to iterate over elements safely."""
        if page_number < len(self.pages):
            page = self.pages[page_number]
            for key, element in page.elements.items():
                yield key, element

    def get_pixmap(self, page_number):
        return self.doc.load_page(page_number).get_pixmap()
    
    def get_page_ratio(self, page_number):
        page = self.doc[page_number]
        return page.bound().width / page.bound().height
    
    def get_page_extent(self, page_number):
        page = self.pdfminer_pages[page_number]
        return page.width, page.height
    
    def get_safe_margin(self):
        return self.margin
    
    def get_page_number(self):
        return len(self.pdfminer_pages)
    
    def set_safe_margin(self, margin):
        self.margin = margin
        self.recalculate_safe_area()
