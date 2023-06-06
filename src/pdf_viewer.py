import tkinter as tk
import threading
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
    def __init__(self, pdf_path, intm_dir, master=None):
        super().__init__(master)
        self.master = master
        self.pack(fill='both', expand=1)

        # Load the PDF with PyMuPDF and pdfminer
        self.pdf = Pdf(pdf_path, intm_dir)

        # Create toolbar
        self.toolbar = PdfViewerToolbar(self)
        self.toolbar.bind("<<ToolbarButtonClicked>>", self.on_toolbar_button_clicked)
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

        for key, element in self.pdf.iter_elements_page(self.canvas.get_current_page()):
            if not element.safe or not element.visible:
                continue  # Skip unsafe or invisible elements

            text = element.translated if element.translated is not None else element.text

            if element.contd == 1:
                self.text_widget.insert(tk.END, f'{text} ')
            else:
                # it should be shown as a new line even if it is a join
                self.text_widget.insert(tk.END, f'{text}\n')

    def add_elements_to_treeview(self):
        self.dtv.delete_all_items()

        for key, element in self.pdf.iter_elements():
            tags = ()
            if not element.safe or not element.visible:
                tags += ("unsafe",)
            if element.page_number % 2 == 0:
                tags += ("oddpage",)

            self.dtv.insert('', "end", key, values=(element.page_number, element.text), tags=tags)

    def on_treeview_select(self, event):
        # Get the selected item
        selection = self.dtv.selection()
        if selection:
            selected_item = selection[0]

            # Extract the page number from the selected item
            page_number, _ = self.dtv.item(selected_item, "values")

            self.canvas.change_page(int(page_number) - 1)

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
        key = self.canvas.get_clicked_element()
        e = self.pdf.get_element(key)
        if e is not None and e.can_be_translated() and not key in self.translating:
            def request_translation(key, text):
                print("Requesting translation...")
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
            threading.Thread(target=request_translation, args=(key, e.text)).start()        

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