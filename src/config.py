from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class Configuration:

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    PROMPT_DIR = os.getenv("PROMPT_DIR")

    CACHE_DIR = os.getenv("CACHE_DIR")

global_config = Configuration()