from typing import Protocol


class LLMClient(Protocol):
    def generate(self, system_prompt: str, user_prompt: str) -> str: ...


GROUNDED_SYSTEM_PROMPT = """You are Business Brain, an AI business analyst for an SME.
Use ONLY the supplied business context as factual evidence. Never invent figures,
customers, products, causes, or recommendations. If evidence is insufficient,
say so. Distinguish observed facts from hypotheses. Keep answers concise and
actionable. When citing a number, preserve the value supplied in the context."""


def build_grounded_prompt(question: str, context: dict) -> str:
    return (
        f"Business question:\n{question}\n\n"
        "Structured business context (source of truth):\n"
        f"{context}\n\n"
        "Answer the question using only this context. Explain the evidence behind "
        "important conclusions and explicitly state when the data is insufficient."
    )
