class BusinessAgent:
    """Orchestration boundary; business tools remain authoritative."""
    def __init__(self, tools, llm): self.tools, self.llm = tools, llm
    def answer(self, question: str): raise NotImplementedError
