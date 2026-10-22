# amatechie-rag

Grounded knowledge assistant over internal documents: hybrid retrieval (pgvector + full-text), reranking, per-user access scoping, citations, and an eval gate.

## Local development

```bash
cp .env.example .env        # fill in LITELLM_TAG and BEDROCK_CHAT_MODEL
docker compose up -d db litellm
uv sync
uv run alembic upgrade head
uv run python -m app.ingestion sample_docs --tenant demo --embedder fake      # offline, free
uv run python -m app.ingestion sample_docs --tenant demo --embedder bedrock   # real Titan embeddings (AWS creds)
uv run python -m eval.retrieval_eval --embedder bedrock --k 5
uv run uvicorn app.main:app --reload
TEST_DATABASE_URL=postgresql+psycopg://app:app@localhost:5432/rag_test uv run pytest
```

## Roadmap (6-8 h/week)

| Weeks | Milestone |
|---|---|
| 1 | Scaffold, Alembic migration, ingestion (load, chunk, embed, upsert by hash) |
| 2 | Hybrid search with access filter; retrieval harness on a golden set |
| 3 | `/ask` with citations; refusal when context is insufficient |
| 4 | Reranking, answer evals (faithfulness, citation correctness), CI gate |
| 5 | Tenant-per-session demo mode, upload limits, TTL cleanup |
| 6 | Terraform: ECS Fargate, RDS, LiteLLM, custom domain; README with eval and cost numbers |

Project 2 (action agent with human approval, MCP, EKS) follows.
