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

In order to run pdf2md, you need to set up a .env file. An example .env file could look like:

```
CACHE_DIR="./cache"
EXPORT_DIR="./export"
TEXT_FONT="Malgun Gothic"
TEXT_FONT_SIZE=11

# If you want to translate with RapidAPI DeepL API
DEEPL_RAPID_API_KEY=(your RapidAPI key)
DEEPL_RAPID_API_HOST=(your RapidAPI host)
DEEPL_RAPID_API_SRC_LANG=EN
DEEPL_RAPID_API_DST_LANG=KO

# If you want to translate with OpenAI GPT-4
OPENAI_API_KEY=(your open ai key)
PROMPT_DIR="./prompt"
```

In Korea, we don't have access to the DeepL API yet, so we use RapidAPI, which has similar pricing terms.

To obtain a RapidAPI DeepL API key, please visit the following website:
https://rapidapi.com/splintPRO/api/deepl-translator/

To obtain an OpenAI API key, please visit the following website:
https://platform.openai.com/

## Run

The application can then be run with:
```
python -m src.main --f (URL or file name)
```

In case **the URL points to an Arxiv path**, the program will attempt to infer the PDF file path and read from it.

```
https://arxiv.org/abs/1706.03762 → https://arxiv.org/pdf/1706.03762.pdf
```

If no arguments are provided, the program will attempt to read a PDF from **a URL or file path present in your clipboard**.

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
- Extraction of images embedded in the PDF.
- Extraction of tables in the PDF.
- Proper parsing or image extraction of equations in the PDF.
- Automatic identification and modification of text attributes such as title, subtitle, and body text through font analysis.
- Export to markdown (md) files with formatting.
- Export to MHTML files, including images, tables, and equations.
