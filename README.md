# pdf2md
This project, pdf2md, transforms academic paper PDF files into digestible text files. By analyzing the layout of the PDF file, the application restructures paragraphs and translates desired content. The final result is a conveniently exported text file.

![](/asset/pdf2md_230607.jpg)

## Setup
We recommend setting up a virtual environment for running the application. This can be done with the following commands:

```
python -m venv .venv
# Activate the virtual environment depending on your platform
```

Next, install the required Python packages:
```
pip install -r requirements.txt
```

The application can then be run with:
```
python -m src.main --f (URL or file name)
```

An example .env file could look like:
```
CACHE_DIR="./cache"
EXPORT_DIR="./export"
TEXT_FONT="Malgun Gothic"
TEXT_FONT_SIZE=11
OPENAI_API_KEY=(your open ai key)
PROMPT_DIR="./prompt"
```

## Usage
The user interface is easy to navigate and manipulate. The various functionalities include:

**Safe Area**: Define a safe area in the PDF to designate the primary content. The safe area can be adjusted by dragging the red rectangle and applies to the whole document.

![](/asset/safearea.gif)

**Visibility**: Toggle the visibility of elements in the translation or export. Individual elements can be toggled on and off with a click, or multiple elements can be selected by dragging.

![](/asset/visibility.gif)

**Body**: Distinguish body text from non-body elements. Images are automatically marked as non-body and cannot be changed. Use this button to exclude captions when chaining separated paragraphs.

![](/asset/body.gif)

**Concat / Split**: Merge multiple elements into a single paragraph by dragging, or separate them back into lines with a right click. Merged paragraphs do not include line breaks.

![](/asset/concat.gif)

**Join / Split**: Similar to Concat/Split, but merges paragraphs with line breaks.

![](/asset/join.gif)

**Order**: Adjust the order of paragraphs. First, click an element to set it as the baseline, then left click another element to place it after the baseline, or right click to place it before. Use the Esc key to cancel the selection.

![](/asset/order.gif)

**Chain**: Link paragraphs that have been split over several blocks or pages. A single click links the paragraph to the next body paragraph without a line break, a double click links them with a line break. Chained paragraphs are processed together during translation.

![](/asset/chain.gif)

**Translate**: Translates the selected paragraph into Korean. The application currently uses GPT-4, but you can modify the prompt by changing the prompt/translate.txt file.

![](/asset/translate.gif)

## Roadmap
- Integration with other translation services such as DeepL.
- Extraction of images embedded in the PDF.
- Extraction of tables in the PDF.
- Proper parsing or image extraction of equations in the PDF.
- Automatic identification and modification of text attributes such as title, subtitle, and body text through font analysis.
- Export to markdown (md) files with formatting.
- Export to MHTML files, including images, tables, and equations.
