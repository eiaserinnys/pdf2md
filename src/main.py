import os
import argparse
import requests
from urllib.parse import urlparse
import tkinter as tk
from tkinter import font
from src.pdf_viewer import PDFViewer
from src.config import global_config

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
        with open(destination, 'wb') as file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)
        print("File downloaded successfully in ", destination)
        return True
    else:
        print("Failed to download file: ", response.status_code)
        return False

def main():
    root = tk.Tk()
    root.title("pdf2md")
    root.geometry('1200x800')  # set initial window size

    # fonts=list(font.families())
    # fonts.sort()
    # for f in fonts:
    #     print(f)

    # Create the parser
    parser = argparse.ArgumentParser(description='Loads a PDF file and exports to a text file.')

    # Add the arguments
    parser.add_argument('--f', type=str, help='The PDF file to view')

    # Parse the arguments
    args = parser.parse_args()

    # Get the input file
    path_name = args.f
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
        print("URL detected, downloading file...")

        url = path_name

        file_name = get_filename_from_url(url)
        
        if file_name == "":
            print("Failed to get filename from URL")
            return

        path_name = os.path.join(intm_dir, file_name)

        if os.path.isfile(path_name):
            print(f"File '{path_name}' already exists, skipping download")
        else:
            download_file(url, path_name)

    # show GUI
    app = PDFViewer(path_name, intm_dir, export_dir, master=root)
    app.mainloop()

if __name__ == "__main__":
    main()
