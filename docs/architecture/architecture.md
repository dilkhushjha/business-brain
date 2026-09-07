# Architecture

User → Web/Chat → FastAPI → Agent → Business Tools → Semantic Layer → Metrics/Signals/ML → Evidence → LLM → User.

The LLM explains structured evidence; it does not own numerical truth.

The pilot is a modular monolith using PostgreSQL/pgvector, Redis and object storage. More distributed infrastructure is introduced only when justified.

## Agent implementation status

The live `/agent/{business_id}/ask` path does not currently call an LLM at
all -- `packages/agent/business_brain/agent/llm.py`/`llm_responder.py`
(an `LLMClient` protocol plus OpenAI/mock providers) exist but are wired
to nothing; `service.answer()` only calls the deterministic
`render_grounded_response()` in `responder.py`. In one sense this
satisfies "the LLM does not own numerical truth" more strictly than
intended, since there's no LLM in the loop to get anything wrong -- but it
also means every answer is template-formatted text, not natural language
generation. Wiring in a real LLM call for the explanation step (with the
same evidence-only grounding constraint) is a distinct, larger piece of
work from what's covered here.

What *is* covered: `classify_intent()` (keyword-based, not real NLU)
recognizes business_health, sales_performance, margin_analysis,
receivables_analysis, payables_analysis, supplier_analysis,
customer_analysis, product_analysis, and root_cause. Each of the analysis
intents is grounded against real evidence
(`context/builder.py` now includes margin, receivables, payables, and
customer/supplier concentration alongside the original KPI-only evidence)
or real detected signals -- confidence is only reported as "grounded" when
a specific evidence value or signal actually backs the answer, never on
the strength of the question alone. Verified end to end against a real
seeded database for every intent (`tests/integration/test_agent_service_db.py`),
not just against hand-built context dicts.
