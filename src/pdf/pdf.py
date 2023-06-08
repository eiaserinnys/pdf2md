import os
import sys
import fitz  # PyMuPDF
import pickle
from io import BytesIO
from PIL import Image
from pdfminer.layout import LAParams
from pdfminer.high_level import extract_pages
from src.pdf.pdf_element import PdfRect, PdfElement
from src.canvas.utility import check_overlap
from src.service.openai_completion_service import OpenAICompletionService, CompletionResult
from src.service.prompt_manager import prompt_manager

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

    def __init__(self, pdf_path, intm_dir, ignore_cache = False):
        self.intm_dir = intm_dir
        self.intm_path = os.path.join(
            intm_dir, 
            os.path.splitext(os.path.basename(pdf_path))[0] + ".context")

        params = LAParams(
            line_overlap = 0.5, 
            char_margin = 2.0, 
            line_margin = 0.5, 
            word_margin = 0.1, 
            boxes_flow = 0.5, 
            detect_vertical = False, 
            all_texts = False)

        self.context = None

        if os.path.exists(self.intm_path):
            try:
                if ignore_cache:
                    print("Cached PDF found, but ignoring it by --i option")
                else:
                    self.context = Pdf.Context.load_from_pickle(self.intm_path)
                    print("Loaded cached PDF from", self.intm_path)
            except:
                print("Loading cached PDF failed")
        
        self.tables = []

        if self.context is None:
            try:
                doc = fitz.open(pdf_path)
                pdfminer_pages = list(extract_pages(pdf_path, laparams = params))

                # camelot requires Ghostscript to be installed, too much hassle
                # tables = camelot.read_pdf(pdf_path)
                # print("Total tables extracted:", tables.n)
                # for i, table in enumerate(tables):
                #     print("Table", i + 1, ":", table.shape)
                #     print(table.df)

                # tabula requires Java to be installed, too much hassle
                # tables = tabula.read_pdf(pdf_path, pages="all")
                # for i, table in enumerate(tables, start=1):
                #     print("Table", i, ":", table.shape)
                #     print(table)

                # pdfplumber is not so good with default settings
                # pdf = pdfplumber.open(pdf_path)
                # for p, page in enumerate(pdf.pages):
                #     t = page.find_tables(table_settings={})
                #     for table in t:
                #         self.tables.append((p, table))

            except Exception as e:
                print("Loading PDF failed")
                print(e)
                sys.exit(1)
                
            self.context = Pdf.Context()
            self.build_element_list(doc, pdfminer_pages)
            self.recalculate_safe_area()
            self.save()

        # reconstruct images from pickled bytes
        self.images = []
        for page in self.context.pages:
            byte_arr = BytesIO(page.bytes_content)
            self.images.append(Image.open(byte_arr))

        # reconstruct chain list
        self.build_chain_list()

    def build_element_list(self, doc, pdfminer_pages):
        for page_number, pdfminer_page in enumerate(pdfminer_pages):

            self.context.pages.append(PdfPage(page_number + 1))

            cur_page = self.context.pages[-1]
            cur_page.width, cur_page.height = pdfminer_page.width, pdfminer_page.height

            doc_page = doc.load_page(page_number)
            pix = doc_page.get_pixmap(matrix=fitz.Matrix(2, 2))  # This is your pixmap from PyMuPDF
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            byte_arr = BytesIO()
            img.save(byte_arr, format='JPEG')            
            
            # Get the bytes content
            cur_page.bytes_content = byte_arr.getvalue()            

            for element in pdfminer_page:
                if PdfElement.can_be_created(element):
                    cur_page.append(self.context.index, PdfElement.from_pdfminer(page_number + 1, element))
                    self.context.index += 1

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

    def build_chain_list(self):
        self.chains = {}
        self.to_chain = {}

        last_head_key = None
        last_head = None
        last_text = None

        prev_body = None

        for page in self.context.pages:
            for key, element in page.elements:
                if element.visible and element.safe and element.body:
                    if last_head is None:
                        if element.contd is not None:
                            # new chain
                            last_head_key, last_head, last_text = key, element, element.text

                            # save chain head
                            self.to_chain[key] = key
                        else:
                            # new line
                            #self.chain_list.append((key, element, element.text))

                            # save chain head
                            #self.to_chain[key] = key
                            pass
                    else:
                        # continue chain
                        if prev_body.contd == 1:
                            # continue chain by concat
                            last_text += " " + element.text
                        else:
                            # continue chain by join
                            last_text += "\n" + element.text

                        # save chain head
                        self.to_chain[key] = last_head_key

                        if element.contd is None:
                            # end of chain
                            self.chains[last_head_key] = (last_head, last_text)
                            last_head_key, last_head, last_text = None, None, None

                    prev_body = element

        if last_head is not None:
            self.chains[last_head_key] = (last_head, last_text)

    def find_last_body_element_until(self, page):
        prev_element = None
        for i in range(page):
            for _, element in self.iter_elements_page(i):
                if element.visible and element.safe and element.body:
                    prev_element = element
        return prev_element

    def get_chained_text(self, key_to_find):
        if self.to_chain.get(key_to_find) is None:
            e = self.get_element(key_to_find)
            return (key_to_find, e, e.text) if e is not None else (None, None, None)
        else:
            key = self.to_chain[key_to_find]
            return (key, self.chains[key][0], self.chains[key][1]) if key is not None else (None, None, None)
    
    def get_page_text(self, page):
        text = ""

        in_continue = True

        for key, element in self.iter_elements_page(page):
            if not element.safe or not element.visible:
                continue  # Skip unsafe or invisible elements

            if in_continue:
                if self.to_chain.get(key) is None and element.body:
                    in_continue = False
                else:
                    if element.body:
                        text += "(omitted by continuation)\n"

            if not in_continue:
                if self.to_chain.get(key) is not None:
                    if self.to_chain[key] == key:
                        # it is a head of a chain
                        if element.translated is not None:
                            text += element.translated + "\n"
                        else:
                            text += self.chains[key][1] + "\n"
                    else:
                        # it is a continuation of a chain
                        pass
                else:
                    text += element.translated if element.translated is not None else element.text
                    text += "\n"
            else:
                if not element.body:
                    text += element.text + "\n"

        return text

    def get_text(self):
        text = ""

        for page in self.context.pages:
            for key, element in page.elements:
                if not element.safe or not element.visible:
                    continue  # Skip unsafe or invisible elements

                if self.to_chain.get(key) is not None:
                    if self.to_chain[key] == key:
                        # it is a head of a chain
                        if element.translated is not None:
                            text += element.translated + "\n"
                        else:
                            text += self.chains[key][1] + "\n"
                    else:
                        # it is a continuation of a chain
                        pass
                else:
                    text += element.translated if element.translated is not None else element.text
                    text += "\n"

        return text

    def set_safe_margin(self, margin):
        self.context.margin = margin
        self.recalculate_safe_area()
        self.build_chain_list()

    def toggle_visibility(self, key):
        e = self.get_element(key)
        e.visible = not e.visible if e is not None else None

        # rebuild chain list
        self.build_chain_list()

    def toggle_body(self, key):
        e = self.get_element(key)
        e.body = not e.body if e is not None else None

        # rebuild chain list
        self.build_chain_list()

    def toggle_continue(self, key):
        e = self.get_element(key)
        e.toggle_continue() if e is not None else None

        # rebuild chain list
        self.build_chain_list()

    def split_element(self, key_to_split):
        for page in self.context.pages:
            for i, (key, element) in enumerate(page.elements):
                if key == key_to_split:
                    if element.safe and element.visible and element.can_be_split():
                        # remove the original element
                        page.elements.pop(i)
                        # insert new elements at the same position
                        for j, new_element in enumerate(element.children):
                            page.elements.insert(i + j, (self.context.index, new_element))
                            self.context.index += 1

                        # rebuild chain list
                        self.build_chain_list()
                        break

    def merge(self, page_number, key_list, concat_or_join):
        if key_list is None or len(key_list) <= 0:
            return

        page = self.context.pages[page_number]
        insert_position = None
      
        # find elements to merge
        to_merge = []
        for k in key_list:
            for i, (key, element) in enumerate(page.elements):
                if key == k:
                    if element.safe and element.visible and element.can_be_merged():
                        if insert_position is None or i < insert_position:
                            insert_position = i
                        to_merge.append(element)

        if len(to_merge) < 2:
            return

        # mark elements to remove
        for e in to_merge:
            e.marked = True

        page.elements.insert(insert_position, (self.context.index, PdfElement.from_merge(page.page_number, to_merge, concat_or_join)))
        self.context.index += 1

        # removed marked elements
        new_elements = []
        for element in page.elements:
            if element[1].marked:
                continue
            new_elements.append(element)
        page.elements = new_elements

        # reset marked
        for e in to_merge:
            e.marked = False

        # rebuild chain list
        self.build_chain_list()

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

        # rebuild chain list
        self.build_chain_list()

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

    def get_pixmap(self, page_number):
        return self.images[page_number]
    
    def get_page_ratio(self, page_number):
        return self.images[page_number].width / self.images[page_number].height
    
    def get_page_extent(self, page_number):
        page = self.context.pages[page_number]
        return page.width, page.height
    
    def get_safe_margin(self):
        return self.context.margin
    
    def get_page_number(self):
        return len(self.context.pages)
    
    def save(self):
        self.context.save_to_pickle(self.intm_path)

    def can_be_translated(self, key):
        if self.to_chain.get(key) is None:
            e = self.get_element(key)
            return e.can_be_translated() if e is not None else False
        else:
            head = self.chains[self.to_chain[key]][0]
            return head.can_be_translated() if head is not None else False