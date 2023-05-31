import wx
import wx.lib.agw.ultimatelistctrl as ULC
import fitz  # PyMuPDF
from pdfminer.layout import LTTextBox
from pdfminer.high_level import extract_pages
from PIL import Image
import numpy as np
import io

class PDFViewerWx(wx.Frame):
    def __init__(self, pdf_path, parent=None):
        wx.Frame.__init__(self, parent, -1, "PDF Viewer")

        self.splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        self.panel1 = wx.Panel(self.splitter)
        self.panel2 = wx.Panel(self.splitter)

        self.splitter.SplitVertically(self.panel1, self.panel2)
        self.splitter.SetSashGravity(0.5)

        # Load the PDF with PyMuPDF and pdfminer
        self.doc = fitz.open(pdf_path)
        self.pdfminer_pages = list(extract_pages(pdf_path))
        self.current_page = 0

        # Initialize Canvas
        self.canvas = wx.StaticBitmap(self.panel1)
        self.Bind(wx.EVT_SIZE, self.on_resize)
        self.Bind(wx.EVT_MOTION, self.on_mouse_move)

        # Initialize Text widget
        self.listbox = ULC.UltimateListCtrl(
            self.panel2, 
            agwStyle=wx.LC_REPORT | ULC.ULC_HAS_VARIABLE_ROW_HEIGHT)   # wx.LC_HRULES | wx.LC_VRULES | 
        self.listbox.InsertColumn(0, 'Text')
        pdfminer_page = self.pdfminer_pages[self.current_page]
        # for element in pdfminer_page:
        #     if isinstance(element, LTTextBox):
        #         index = self.listbox.GetItemCount()
        #         self.listbox.InsertStringItem(index, element.get_text())

        # self.listbox.Bind(wx.EVT_LIST_BEGIN_DRAG, self.on_begin_drag)
        # self.listbox.Bind(wx.EVT_LEFT_UP, self.on_end_drag)

        # Get initial size of the first page to maintain aspect ratio
        first_page = self.doc[0]
        self.page_ratio = first_page.bound().width / first_page.bound().height

        #self.show_page()

    def on_begin_drag(self, event):
        self.drag_start_index = event.GetIndex()
        event.Allow()

    def on_end_drag(self, event):
        pos = event.GetPosition()
        index, _ = self.listbox.HitTest(pos)
        if index != self.drag_start_index and index != -1:
            self.listbox.MoveItem(self.drag_start_index, index)

    def on_resize(self, event):
        self.canvas.SetBitmap(wx.Bitmap())  # clear the canvas
        self.show_page()
        event.Skip()

    def show_page(self):
        pymupdf_page = self.doc.load_page(self.current_page)
        pix = pymupdf_page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # Convert the PIL Image to RGBA
        img = img.convert("RGBA")

        # Convert the PIL Image to a wx.Bitmap and display it on the canvas
        image = wx.Bitmap.FromBufferRGBA(img.width, img.height, img.tobytes())
        image = self.scale_bitmap(image, self.panel1.GetSize().width, self.panel1.GetSize().height)
        self.canvas.SetBitmap(image)

    def scale_bitmap(self, bitmap, width, height):
        image = wx.ImageFromBitmap(bitmap)
        image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
        return wx.BitmapFromImage(image)

    def on_mouse_move(self, event):
        pos = event.GetPosition()
        index, _ = self.listbox.HitTest(pos)
        if index != -1:
            self.listbox.Select(index)
        event.Skip()