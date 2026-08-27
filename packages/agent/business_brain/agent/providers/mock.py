class MockLLMClient:
    """Deterministic provider used for local development and integration tests."""

    def __init__(self, response: str = "I can answer from the supplied business evidence."):
        self.response = response
        self.last_system_prompt = None
        self.last_user_prompt = None

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        self.last_system_prompt = system_prompt
        self.last_user_prompt = user_prompt
        return self.response
