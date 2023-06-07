import tkinter as tk
import threading
import requests
import os
from functools import partial
from tkinter import ttk
from src.pdf.pdf import Pdf
from src.canvas.pdf_canvas import PdfCanvas
from src.toolbar.pdf_viewer_toolbar import PdfViewerToolbar
from src.toolbar.pdf_viewer_toolbar_item import PdfViewerToolbarItem
from src.service.openai_completion_service import OpenAICompletionService, CompletionResult
from src.service.prompt_manager import prompt_manager
from src.config import global_config

class PDFViewer(tk.Frame):
    def __init__(self, pdf_path, intm_dir, export_dir, master=None):
        super().__init__(master)
        self.master = master
        self.pack(fill='both', expand=1)

        self.pdf_path = pdf_path

        # Initialize cache directory
        self.intm_dir = os.path.abspath(intm_dir)
        os.makedirs(self.intm_dir, exist_ok=True)

        # Initialize export directory
        self.export_dir = os.path.abspath(export_dir)
        os.makedirs(self.export_dir, exist_ok=True)

        # Load the PDF with PyMuPDF and pdfminer
        self.pdf = Pdf(pdf_path, self.intm_dir)

        # Create toolbar
        self.toolbar = PdfViewerToolbar(self)
        self.toolbar.bind("<<ToolbarButtonClicked>>", self.on_toolbar_button_clicked)
        self.toolbar.bind("<<ExportButtonClicked>>", self.on_export_button_clicked)
        for i in range(1, 6):
            self.master.bind(str(i), self.toolbar.key_press)

        # Create a PanedWindow with horizontal orientation
        self.paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill='both', expand=1)

        # Initialize Canvas
        self.canvas = PdfCanvas(self.paned_window, self.pdf)
        self.paned_window.add(self.canvas)
        self.canvas.bind("<<PageChanged>>", self.on_page_changed_by_canvas)
        self.canvas.bind("<<SafeAreaChanged>>", self.on_safe_area_changed_by_canvas)
        self.canvas.bind("<<DragEnd>>", self.on_drag_end_by_canvas)
        self.canvas.bind("<<ElementLeftClicked>>", self.on_element_left_clicked_by_canvas)
        self.canvas.bind("<<ElementRightClicked>>", self.on_element_right_clicked_by_canvas)
        self.master.bind("<Escape>", self.canvas.on_escape)

        # Initialize Text widget
        self.text_widget = tk.Text(self.paned_window, font=(global_config.TEXT_FONT, global_config.TEXT_FONT_SIZE))
        self.text_widget.config(spacing3=7)
        self.text_widget.pack(fill="both", expand=True)
        self.paned_window.add(self.text_widget)

        # Add elements to the Text widget
        self.add_elements_to_text_widget()

        # Set the minimum size of the Text widget to 60% of the window width
        self.paned_window.update()
        self.paned_window.sashpos(0, 600)

        # Apply initial tool selection
        self.toolbar.toggle_button(PdfViewerToolbarItem.SafeArea)

        self.translating = {}

    def add_elements_to_text_widget(self):
        self.text_widget.delete('1.0', tk.END)  # Clear the text widget
        self.text_widget.insert(tk.END, self.pdf.get_page_text(self.canvas.get_current_page()))

    def on_page_changed_by_canvas(self, event):
        self.add_elements_to_text_widget()

    def redraw(self):
        self.canvas.redraw()
        self.add_elements_to_text_widget()

    def on_safe_area_changed_by_canvas(self, event):
        if self.toolbar.get_current_selection() != PdfViewerToolbarItem.SafeArea:
            return
        
        new_safe_margin = self.canvas.get_new_safe_margin()
        self.pdf.set_safe_margin(new_safe_margin)
        self.pdf.save()
        self.redraw()

    def on_drag_end_by_canvas(self, event):
        actions = {
            PdfViewerToolbarItem.Visibility:    lambda keys: [self.pdf.toggle_visibility(key) for key in keys],
            PdfViewerToolbarItem.MergeAndSplit: lambda keys: self.pdf.merge(self.canvas.get_current_page(), keys, True),
            PdfViewerToolbarItem.JoinAndSplit:  lambda keys: self.pdf.merge(self.canvas.get_current_page(), keys, False),
            PdfViewerToolbarItem.Body:          lambda keys: [self.pdf.toggle_body(key) for key in keys],
        }

        current_selection = self.toolbar.get_current_selection()
        if current_selection in actions:
            action = actions[current_selection]
            action(self.canvas.get_selected_elements())
            self.pdf.save()
            self.redraw()

    def on_element_left_clicked_by_canvas(self, event):
        current_selection = self.toolbar.get_current_selection()
        key = self.canvas.get_clicked_element()

        actions = {
            PdfViewerToolbarItem.Visibility:    lambda: self.pdf.toggle_visibility(key),
            PdfViewerToolbarItem.Order:         self.handle_order,
            PdfViewerToolbarItem.Concat:        lambda: self.pdf.toggle_continue(key),
            PdfViewerToolbarItem.Body:          lambda: self.pdf.toggle_body(key),
            PdfViewerToolbarItem.Translate:     self.handle_translate
        }

        if current_selection in actions:
            actions[current_selection]()
            self.pdf.save()
            self.redraw()

    def handle_order(self):
        key = self.canvas.get_clicked_element()
        if self.canvas.get_pivot() is None:
            element = self.pdf.get_element_in_page(self.canvas.get_current_page(), key)
            if element is not None and element.safe and element.visible:
                self.canvas.set_pivot(key)
        else:
            if self.pdf.move_element(self.canvas.get_pivot(), key, self.canvas.get_current_page(), "after"):
                self.canvas.set_pivot(key)

    def handle_translate(self):
        key, e, text = self.pdf.get_chained_text(self.canvas.get_clicked_element())
        if e is not None and e.can_be_translated() and not key in self.translating:

            def request_translation_deepl(key, text):
                print("Requesting translation via RapidAPI DeepL...")

                url = "https://deepl-translator.p.rapidapi.com/translate"

                payload = {
                    "text": text,
                    "source": global_config.DEEPL_RAPID_API_SRC_LANG,
                    "target": global_config.DEEPL_RAPID_API_DST_LANG
                }
                headers = {
                    "content-type": "application/json",
                    "X-RapidAPI-Key": global_config.DEEPL_RAPID_API_KEY,
                    "X-RapidAPI-Host": global_config.DEEPL_RAPID_API_HOST
                }

                response = requests.post(url, json=payload, headers=headers)

                if response.status_code == 200:
                    self.master.after(0, update_ui, key, response.json()["text"], True)

            def request_translation_openai(key, text):
                print("Requesting translation via OpenAI...")
                response = OpenAICompletionService.request_chat_completion(
                    model="gpt-4",
                    messages=[
                        OpenAICompletionService.user_message(
                            prompt_manager.generate_prompt(
                                "translate",
                                { 
                                    "Text" : text, 
                                })),
                    ],
                    temperature=0.0,
                    stream=True, 
                    stream_callback=partial(stream_callback, key),
                    verbose_prompt=False,
                    verbose_response=False)
                
                if response.status == CompletionResult.OK:
                    self.master.after(0, update_ui, key, response.reply_text, True)

            def stream_callback(key, result, content):
                self.master.after(0, update_ui, key, result, False)

            def update_ui(key, text, finished):
                e = self.pdf.get_element(key)

                if e is not None:
                    need_to_redraw = e.translated is None
                    e.translated = text
                    if not finished:
                        if e.page_number == self.canvas.get_current_page() + 1:
                            if need_to_redraw:
                                self.redraw()
                            else:
                                self.add_elements_to_text_widget()
                    else:
                        self.pdf.save()
                        if e.page_number == self.canvas.get_current_page() + 1:
                            self.redraw()
                
                if finished and key in self.translating:
                    self.translating.pop(key)

            self.translating[key] = True
            if global_config.DEEPL_RAPID_API_KEY is not None:
                threading.Thread(target=request_translation_deepl, args=(key, text)).start()
            elif global_config.OPENAI_API_KEY is not None:
                threading.Thread(target=request_translation_openai, args=(key, text)).start()
            else:
                print("No translation API key provided")

    def on_element_right_clicked_by_canvas(self, event):
        if self.toolbar.get_current_selection() == PdfViewerToolbarItem.MergeAndSplit or self.toolbar.get_current_selection() == PdfViewerToolbarItem.JoinAndSplit:
            self.pdf.split_element(self.canvas.get_clicked_element())
            self.pdf.save()
            self.redraw()
        elif self.toolbar.get_current_selection() == PdfViewerToolbarItem.Order:
            if self.pdf.move_element(self.canvas.get_pivot(), self.canvas.get_clicked_element(), self.canvas.get_current_page(), "before"):
                self.pdf.save()
                # it is very confusing, so we don't change the pivot
                #self.canvas.set_pivot(self.canvas.get_clicked_element())
                self.redraw()
        elif self.toolbar.get_current_selection() == PdfViewerToolbarItem.Translate:
            e = self.pdf.get_element(self.canvas.get_clicked_element())
            if e is not None:
                e.translated = None
                self.pdf.save()
                self.redraw()

    def on_toolbar_button_clicked(self, event):
        self.canvas.change_mode(self.toolbar.get_current_selection())

    def on_export_button_clicked(self, event):
        text = self.pdf.get_text()
        filename = os.path.splitext(os.path.basename(self.pdf_path))[0] + ".txt"
        pathname = os.path.join(self.export_dir, filename)
        with open(pathname, 'w') as file:
            file.write(text)