import fitz  # PyMuPDF
from dataclasses import dataclass
import pdfplumber
from pdfminer.layout import LAParams, LTTextBox, LTImage, LTFigure
from pdfminer.high_level import extract_pages
from src.utility import check_overlap

class PdfPage:
    def __init__(self, page_number):
        self.page_number = page_number
        self.elements = []

    def append(self, key, element):
        self.elements.append((key, element))

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
    element: object
    bbox: PdfRect
    org_text: str
    text: str
    mergable: bool
    safe: bool
    visible: bool
    children = None
    marked: bool = False

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

        self.index = 0
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

                    new_element = PdfElement(page_number + 1, element, element.bbox, element.get_text(), text, True, True, True)
                    cur_page.append(self.index, new_element)
                    self.index += 1

                    new_element.children = []

                    for line in element:
                        text = line.get_text()
                        text = text.replace("-\n", "")
                        text = text.replace("\n", " ")
                        text = text.strip()

                        new_element.children.append((self.index, PdfElement(page_number + 1, line, line.bbox, line.get_text(), text, True, True, True)))
                        self.index += 1

                elif isinstance(element, LTFigure):
                    cur_page.append(self.index, PdfElement(page_number + 1, element, element.bbox, "figure", "figure", False, True, True))
                    self.index += 1
                elif isinstance(element, LTImage):
                    cur_page.append(self.index, PdfElement(page_number + 1, element, element.bbox, "image", "image", False, True, True))
                    self.index += 1

    def merge(self, page_number, key_list):
        if key_list is None or len(key_list) <= 0:
            return

        page = self.pages[page_number]
        insert_position = None
      
        # find elements to merge
        to_merge = []
        for k in key_list:
            for i, (key, element) in enumerate(page.elements):
                if key == k:
                    if element.safe and element.visible and element.mergable:
                        if insert_position is None or i < insert_position:
                            insert_position = i
                        to_merge.append((key, element))

        if len(to_merge) < 2:
            return

        # mark elements to remove
        for _, e in to_merge:
            e.marked = True

        # create merged element
        merged_org_text = ''.join([el[1].org_text for el in to_merge])
        text = merged_org_text.replace("-\n", "")
        text = text.replace("\n", " ")
        text = text.strip()

        merged_bbox = (
            min(el[1].bbox[0] for el in to_merge),
            min(el[1].bbox[1] for el in to_merge),
            max(el[1].bbox[2] for el in to_merge),
            max(el[1].bbox[3] for el in to_merge))

        merged_element = PdfElement(page.page_number, None, merged_bbox, merged_org_text, text, True, True, True)
        merged_element.children = to_merge
        page.elements.insert(insert_position, (self.index, merged_element))
        self.index += 1

        # removed marked elements
        new_elements = []
        for element in page.elements:
            if element[1].marked:
                continue
            new_elements.append(element)
        page.elements = new_elements

        # reset marked
        for _, e in to_merge:
            e.marked = False

    def recalculate_safe_area(self):
        for page in self.pages:
            pdfminer_page = self.pdfminer_pages[page.page_number - 1]
            safe_area = (
                pdfminer_page.width * self.margin.x1, 
                pdfminer_page.height * (1 - self.margin.y2),
                pdfminer_page.width * self.margin.x2,
                pdfminer_page.height * (1 - self.margin.y1), 
            )
            for _, element in page.elements:
                element.safe = check_overlap(element.bbox, safe_area)

    def toggle_visibility(self, key_to_toggle):
        for page in self.pages:
            for key, element in page.elements:
                if key == key_to_toggle:
                    element.visible = not element.visible

    def split_element(self, key_to_split):
        for page in self.pages:
            for i, (key, element) in enumerate(page.elements):
                if key == key_to_split:
                    if element.children != None and len(element.children) > 1:
                        # remove the original element
                        page.elements.pop(i)
                        # insert new elements at the same position
                        for j, new_element in enumerate(element.children):
                            page.elements.insert(i + j, new_element)
                        break

    def iter_elements(self):
        """Generator method to iterate over elements safely."""
        for page in self.pages:
            for key, element in page.elements:
                yield key, element

    def iter_elements_page(self, page_number):
        """Generator method to iterate over elements safely."""
        if page_number < len(self.pages):
            page = self.pages[page_number]
            for key, element in page.elements:
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
