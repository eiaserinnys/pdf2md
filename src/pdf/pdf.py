import os
import fitz  # PyMuPDF
import pickle
from dataclasses import dataclass, asdict
import pdfplumber
from pdfminer.layout import LAParams, LTTextBox, LTImage, LTFigure
from pdfminer.high_level import extract_pages
from src.pdf.pdf_element import PdfRect, PdfElement
from src.canvas.utility import check_overlap

class PdfPage:
    def __init__(self, page_number, elements = None):
        self.page_number = page_number
        self.width = 1
        self.height = 1
        self.elements = [] if elements is None else elements

    def append(self, key, element):
        self.elements.append((key, element))

class Pdf:
    class Context:
        def __init__(self):
            self.margin = PdfRect(0.15, 0.08, 0.85, 0.92)
            self.pages = []
            self.index = 0

        def save_to_pickle(self, filename):
            with open(filename, 'wb') as file:
                pickle.dump(self, file)

        @staticmethod
        def load_from_pickle(filename):
            with open(filename, 'rb') as file:
                context = pickle.load(file)
            return context

    def __init__(self, pdf_path, intm_path):
        self.intm_path = intm_path

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

        # self.pdfplumber = pdfplumber.open(pdf_path)

        # for page in self.pdfplumber.pages:
        #     tables = page.find_tables()
        #     for table in tables:
        #         print(table.bbox.x0, table.bbox.y0, table.bbox.x1, table.bbox.y1)

        if os.path.exists(self.intm_path):
            self.context = Pdf.Context.load_from_pickle(self.intm_path)
        else:
            doc = fitz.open(pdf_path)
            pdfminer_pages = list(extract_pages(pdf_path, laparams = params))

            self.context = Pdf.Context()
            self.build_element_list(doc, pdfminer_pages)
            self.recalculate_safe_area()
            self.save()

    def build_element_list(self, doc, pdfminer_pages):
        for page_number, pdfminer_page in enumerate(pdfminer_pages):

            self.context.pages.append(PdfPage(page_number + 1))

            cur_page = self.context.pages[-1]
            cur_page.width, cur_page.height = pdfminer_page.width, pdfminer_page.height

            doc_page = doc.load_page(page_number)
            #cur_page.pixmap = doc_page.get_pixmap()
            cur_page.pixmap_ratio = doc_page.bound().width / doc_page.bound().height

            for element in pdfminer_page:
                if isinstance(element, LTTextBox):
                    # for text_line in element:
                    text = element.get_text()
                    text = text.replace("-\n", "")
                    text = text.replace("\n", " ")
                    text = text.strip()

                    new_element = PdfElement(page_number + 1, element.bbox, element.get_text(), text, True, True, True)
                    cur_page.append(self.context.index, new_element)
                    self.context.index += 1

                    new_element.children = []

                    for line in element:
                        text = line.get_text()
                        text = text.replace("-\n", "")
                        text = text.replace("\n", " ")
                        text = text.strip()

                        new_element.children.append((self.context.index, PdfElement(page_number + 1, line.bbox, line.get_text(), text, True, True, True)))
                        self.context.index += 1

                elif isinstance(element, LTFigure):
                    cur_page.append(self.context.index, PdfElement(page_number + 1, element.bbox, "<<<figure>>>", "<<<figure>>>", False, True, True))
                    self.context.index += 1
                elif isinstance(element, LTImage):
                    cur_page.append(self.context.index, PdfElement(page_number + 1, element.bbox, "<<<image>>>", "<<<image>>>", False, True, True))
                    self.context.index += 1

    def merge(self, page_number, key_list):
        if key_list is None or len(key_list) <= 0:
            return

        page = self.context.pages[page_number]
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

        merged_element = PdfElement(page.page_number, merged_bbox, merged_org_text, text, True, True, True)
        merged_element.children = to_merge
        page.elements.insert(insert_position, (self.context.index, merged_element))
        self.context.index += 1

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
        for page in self.context.pages:
            safe_area = (
                page.width * self.context.margin.x1, 
                page.height * (1 - self.context.margin.y2),
                page.width * self.context.margin.x2,
                page.height * (1 - self.context.margin.y1), 
            )
            for _, element in page.elements:
                element.safe = check_overlap(element.bbox, safe_area)

    def toggle_visibility(self, key_to_toggle):
        for page in self.context.pages:
            for key, element in page.elements:
                if key == key_to_toggle:
                    element.visible = not element.visible

    def toggle_concat(self, key_to_toggle):
        for page in self.context.pages:
            for key, element in page.elements:
                if key == key_to_toggle:
                    element.concat = not element.concat

    def split_element(self, key_to_split):
        for page in self.context.pages:
            for i, (key, element) in enumerate(page.elements):
                if key == key_to_split:
                    if element.safe and element.visible and element.can_be_split():
                        # remove the original element
                        page.elements.pop(i)
                        # insert new elements at the same position
                        for j, new_element in enumerate(element.children):
                            page.elements.insert(i + j, new_element)
                        break

    def move_element(self, pivot_key, key_to_move, page_index, disposition = "after"):
        if pivot_key == None or key_to_move == None or pivot_key == key_to_move or page_index >= len(self.context.pages):
            return

        pivot_index = None
        move_index = None
        page = self.context.pages[page_index]

        for i, (key, element) in enumerate(page.elements):
            if key == pivot_key and element.safe and element.visible:
                pivot_index = i
            elif key == key_to_move and element.safe and element.visible:
                move_index = i

        if pivot_index is None or move_index is None:
            return False  # pivot_key or key_to_move was not found in the page

        element_to_move = page.elements.pop(move_index)

        if move_index < pivot_index:
            pivot_index -= 1

        if disposition == "after":
            offset = 1
        else:
            offset = 0

        page.elements.insert(pivot_index + offset, element_to_move)

        return True

    def get_element(self, key):
        for page in self.context.pages:
            for k, element in page.elements:
                if k == key:
                    return element
        return None    

    def get_element_in_page(self, page, key):
        if page < len(self.context.pages):
            for k, element in self.context.pages[page].elements:
                if k == key:
                    return element
        return None
    
    def iter_elements(self):
        """Generator method to iterate over elements safely."""
        for page in self.context.pages:
            for key, element in page.elements:
                yield key, element

    def iter_elements_page(self, page_number):
        """Generator method to iterate over elements safely."""
        if page_number < len(self.context.pages):
            page = self.context.pages[page_number]
            for key, element in page.elements:
                yield key, element

    def get_last_element_in_page(self, page_number):
        """Return the last element of the page safely."""
        if 0 <= page_number and page_number < len(self.context.pages):
            page = self.context.pages[page_number]
            if page.elements:  # Check if elements list is not empty
                return page.elements[-1][1]  # Return the last element
        return None  # If page doesn't exist or there are no elements

    def get_pixmap(self, page_number):
        return self.doc.load_page(page_number).get_pixmap()
        #return self.context.pages[page_number].pixmap
    
    def get_page_ratio(self, page_number):
        #page = self.doc[page_number]
        #return page.bound().width / page.bound().height
        return self.context.pages[page_number].pixmap_ratio
    
    def get_page_extent(self, page_number):
        page = self.context.pages[page_number]
        return page.width, page.height
    
    def get_safe_margin(self):
        return self.context.margin
    
    def get_page_number(self):
        return len(self.context.pages)
    
    def set_safe_margin(self, margin):
        self.context.margin = margin
        self.recalculate_safe_area()

    def save(self):
        self.context.save_to_pickle(self.intm_path)