import asyncio
import tkinter as tk
import wx
from src.pdf_viewer import PDFViewer
from src.pdf_viewer_wx import PDFViewerWx

async def main():
    # app = wx.App(False)
    # frame = PDFViewerWx('./example/voyager.pdf')
    # frame.Show(True)
    # app.MainLoop()

    root = tk.Tk()
    root.title("pdf2md")
    root.geometry('1200x800')  # set initial window size
    app = PDFViewer('./example/voyager.pdf', master=root)
    app.mainloop()

if __name__ == "__main__":
    asyncio.run(main())
