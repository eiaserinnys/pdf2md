import os
from src.config import global_config

class PromptManager:
    def __init__(self):
        self.prompt_templates = {}

    def load_prompt(self, name):
        key = PromptManager.get_prompt_key(name)
        if key not in self.prompt_templates:
            with open(key, "r") as file:
                self.prompt_templates[key] = file.read()
        return self.prompt_templates[key]

    def generate_prompt(self, name, replacements = None):
        prompt_template = self.load_prompt(name)
        if replacements != None:
            return prompt_template.format(**replacements)
        else:
            return prompt_template
    
    @staticmethod
    def get_prompt_key(name):
        return os.path.abspath(os.path.join(global_config.PROMPT_DIR, name + ".txt"))

    def reload(self):
        self.prompt_templates = {}

# Create a global instance of PromptManager
prompt_manager = PromptManager()
