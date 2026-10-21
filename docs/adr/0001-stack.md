# ADR 0001: Stack

**Status:** accepted

- **FastAPI + Pydantic v2 + SQLAlchemy 2.0 async + Alembic.** Pydantic models double as API schemas, LLM structured-output schemas and eval case definitions. Async fits slow, streaming LLM calls.
- **Postgres + pgvector.** One store for relational data, vectors (HNSW) and full-text (GIN), so hybrid search and access filtering happen in a single SQL query. Revisit OpenSearch only if corpus size or recall demands it.
- **LiteLLM gateway with static virtual keys, Bedrock behind it.** Apps hold only a scoped, budgeted key; only the gateway holds Bedrock access. Model aliases (`chat-default`, `embed-default`) let the eval harness compare models without code changes. Pin the image by digest.
- **ECS Fargate for this project; EKS for Project 2.** See ADR 0002 (to write).

## Consequences
Access control is enforced in SQL (`tenant_id`, `allowed_groups`), never by post-filtering retrieved text.
