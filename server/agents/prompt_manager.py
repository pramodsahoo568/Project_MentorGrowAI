import yaml
from pathlib import Path

class PromptManager:

    def __init__(self, file_path: str):
        with open(file_path, "r") as f:
            self.data = yaml.safe_load(f)

    def build_messages(self, context, count, domain, template_key=None):

        if template_key is None:
            template_key = self.data.get("default_template")

        system_text = self.data["system_template"].format(
            context=context
        )

        human_template = self.data["human_templates"][template_key]

        human_text = human_template.format(
            count=count,
            domain=domain
        )

        return system_text, human_text