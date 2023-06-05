from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class Configuration:

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    PROMPT_DIR = os.getenv("PROMPT_DIR", "./prompt")

    CACHE_DIR = os.getenv("CACHE_DIR", "./cache")

    TEXT_FONT = os.getenv("TEXT_FONT", "tkDefaultFont")
    TEXT_FONT_SIZE = os.getenv("TEXT_FONT_SIZE", 11)

global_config = Configuration()