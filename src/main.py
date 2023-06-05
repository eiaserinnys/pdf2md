import tkinter as tk
from tkinter import font
from src.pdf_viewer import PDFViewer

def main():
    root = tk.Tk()
    root.title("pdf2md")
    root.geometry('1200x800')  # set initial window size

    # fonts=list(font.families())
    # fonts.sort()
    # for f in fonts:
    #     print(f)

    # path_name = './example/voyager.pdf'
    # intm_name = "./cache/voyager.context"
    path_name = "./cache/2305.16213.pdf"
    intm_dir = "./cache"
    # path_name = './example/1751-0473-7-7.pdf'
    # intm_name = './cache/1751-0473-7-7.context'

    app = PDFViewer(path_name, intm_dir, master=root)
    app.mainloop()

if __name__ == "__main__":
    main()
