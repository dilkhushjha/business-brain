from packages.agent.business_brain.agent.llm import LLMClient, GROUNDED_SYSTEM_PROMPT, build_grounded_prompt


def answer_with_llm(client: LLMClient, question: str, context: dict) -> str:
    prompt = build_grounded_prompt(question, context)
    return client.generate(GROUNDED_SYSTEM_PROMPT, prompt)
