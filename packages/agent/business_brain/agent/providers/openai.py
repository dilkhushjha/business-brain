from openai import OpenAI

from packages.agent.business_brain.agent.llm import GROUNDED_SYSTEM_PROMPT, build_grounded_prompt


class OpenAIClient:
    def __init__(self, model: str = "gpt-5-mini"):
        self.client = OpenAI()
        self.model = model

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.responses.create(
            model=self.model,
            instructions=system_prompt,
            input=user_prompt,
        )
        return response.output_text


def answer_with_openai(question: str, context: dict, model: str = "gpt-5-mini") -> str:
    client = OpenAIClient(model=model)
    return client.generate(GROUNDED_SYSTEM_PROMPT, build_grounded_prompt(question, context))
