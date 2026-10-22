# Eval results

Each row is one run. Add a row whenever retrieval, prompts, models or the corpus change.

## Setup (baseline)
- Corpus: 12 short synthetic documents (`sample_docs/`), one chunk each, 3 with group restrictions, 1 with an embedded prompt injection.
- Embeddings: Amazon Titan Text Embeddings V2 (1024 dims). Chat and judge: Claude Haiku 4.5 on Bedrock (`us.` inference profile), temperature 0.
- Retrieval: hybrid (pgvector cosine + Postgres full-text), RRF fusion, access filter in SQL, top 5.

| Date | Change | Retrieval recall@5 / MRR | Answer pass rate | Security cases | Faithfulness |
|---|---|---|---|---|---|
| 2026-10-22 | Baseline | 1.0 / 1.0 (14 cases) | 19/19 | 5/5 | 1.0 (judge) |

## Caveats
- The set is small and easy: every answer fits in a single chunk, and the corpus has no near-duplicate or conflicting documents. A perfect score here shows the pipeline works, not that retrieval is robust.
- Only one injection style is covered.
- The judge is the same model family as the answerer, so its faithfulness score is optimistic.

## Planned
Harder corpus (multi-chunk documents, near-duplicates, conflicting versions), paraphrased and multi-hop questions, more attack styles, and a second model for comparison.
