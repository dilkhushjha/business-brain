from packages.agent.business_brain.agent.llm import build_grounded_prompt


def test_prompt_requires_grounding():
    prompt = build_grounded_prompt("Why are sales down?", {"evidence": [{"metric": "revenue", "value": "100"}]})
    assert "Why are sales down?" in prompt
    assert "source of truth" in prompt
    assert "only this context" in prompt
