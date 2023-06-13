import os
import argparse
import requests
from tqdm import tqdm
from urllib.parse import urlparse
import tkinter as tk
from tkinter import font
from src.pdf_viewer import PDFViewer
from src.config import global_config
import pyperclip

def is_url(string):
    try:
        result = urlparse(string)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def get_filename_from_url(url):
    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)
    return filename

def download_file(url, destination):
    response = requests.get(url, stream=True)

    # Check if the request was successful
    if response.status_code == 200:
        total_size_in_bytes= int(response.headers.get('content-length', 0))

        progress_bar = None
        if total_size_in_bytes > 0:
            progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)

        with open(destination, 'wb') as file:
            for chunk in response.iter_content(chunk_size=1024):
                if progress_bar is not None:
                    progress_bar.update(len(chunk))
                file.write(chunk)

        if progress_bar is not None:
            progress_bar.close()

        if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
            print("Error, something went wrong.")
            os.remove(destination)
            return False

        print("File downloaded successfully in ", destination)
        return True

    else:
        print("Failed to download file: ", response.status_code)
        return False

def get_path_name_to_open(args):
    # Get the input file
    path_name = args.f
    if path_name is None:

        # check if there is a path in the clipboard
        text = pyperclip.paste()

        if is_url(text):
            print("There is an URL in the clipboard, using that as input")
            path_name = text
        elif os.path.isfile(text):
            print("There is a path name in the clipboard, using that as input")
            path_name = text

    return path_name

def is_arxiv_url(url):
    return url.startswith('https://arxiv.org/abs/')

def is_hugging_face_url(url):
    return url.startswith('https://huggingface.co/papers/')

def try_download(url, intm_dir):

    print("URL detected, trying to download file...")

    # if arxiv URL, download PDF instead
    if is_arxiv_url(url):
        print("Arxiv URL detected, downloading PDF instead")
        url = url.replace('https://arxiv.org/abs/', 'https://arxiv.org/pdf/')
        url += ".pdf"
    elif is_hugging_face_url(url):
        print("Hugging Face URL detected, downloading PDF instead")
        url = url.replace('https://huggingface.co/papers/', 'https://arxiv.org/pdf/')
        url += ".pdf"

    file_name = get_filename_from_url(url)
    if file_name == "":
        print("Failed to get filename from URL")
        return None

    path_name = os.path.join(intm_dir, file_name)

    if os.path.isfile(path_name):
        print(f"File '{path_name}' already exists, skipping download")
    else:
        if not download_file(url, path_name):
            return None
    
    return path_name

def get_arguments():
    # Create the parser
    parser = argparse.ArgumentParser(description='Pdf2md: Loads a PDF file and exports to a text file.')

    # Add the arguments
    parser.add_argument('--f', type=str, help='The PDF file to view')
    parser.add_argument('--l', action='store_true', help='Lists available fonts and exit')
    parser.add_argument('--i', action='store_true', help='Ignores context cache and loads the PDF file again')

    # Parse the arguments
    args = parser.parse_args()

    return args

def main():
    args = get_arguments()

    root = tk.Tk()
    root.title("pdf2md")
    root.geometry('1200x800')  # set initial window size

    if args.l:
        print("Available fonts:")
        fonts=list(font.families())
        fonts.sort()
        for f in fonts:
            print(f)
        return

    path_name = get_path_name_to_open(args)
    if path_name is None:
        print("No input file specified")
        return
    
    intm_dir = global_config.CACHE_DIR
    intm_dir = os.path.abspath(intm_dir)
    os.makedirs(intm_dir, exist_ok=True)

    export_dir = global_config.EXPORT_DIR
    export_dir = os.path.abspath(export_dir)
    os.makedirs(export_dir, exist_ok=True)

    # download file if URL
    if is_url(path_name):
        path_name = try_download(path_name, intm_dir)
        if path_name is None:
            return

    # show GUI
    app = PDFViewer(path_name, intm_dir, export_dir, args.i, master=root)
    app.mainloop()

if __name__ == "__main__":
    main()
