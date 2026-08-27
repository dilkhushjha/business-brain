# Architecture

User → Web/Chat → FastAPI → Agent → Business Tools → Semantic Layer → Metrics/Signals/ML → Evidence → LLM → User.

The LLM explains structured evidence; it does not own numerical truth.

The pilot is a modular monolith using PostgreSQL/pgvector, Redis and object storage. More distributed infrastructure is introduced only when justified.
