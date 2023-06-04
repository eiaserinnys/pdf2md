import asyncio
import tkinter as tk
from src.pdf_viewer import PDFViewer

async def main():
    root = tk.Tk()
    root.title("pdf2md")
    root.geometry('1200x800')  # set initial window size

    path_name = './example/voyager.pdf'
    intm_name = "./cache/voyager.context"
    # path_name = './example/1751-0473-7-7.pdf'
    # intm_name = './cache/1751-0473-7-7.context'

    app = PDFViewer(path_name, intm_name, master=root)
    app.mainloop()

if __name__ == "__main__":
    asyncio.run(main())
