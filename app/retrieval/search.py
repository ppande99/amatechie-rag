"""Hybrid retrieval: vector similarity + keyword search, fused with Reciprocal Rank Fusion (RRF).

Why both? Vectors find passages with the same *meaning* ("rotate credentials" ~ "change the secret"),
keywords find exact terms vectors blur (error codes, product names, "SOC 2"). RRF merges the two
ranked lists without needing their scores to be comparable.

Access control lives in the SQL `WHERE`, applied *before* ranking: a chunk the user may not see is
never a candidate, so it cannot leak into the prompt, a citation, or a score.
"""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

RRF_K = 60  # standard constant; dampens the influence of top ranks

_SQL = text(
    """
    WITH allowed AS (
        SELECT c.id, c.embedding, c.tsv
        FROM chunks c
        JOIN documents d ON d.id = c.document_id
        WHERE c.tenant_id = :tenant
          AND (d.expires_at IS NULL OR d.expires_at > now())
          AND (cardinality(d.allowed_groups) = 0 OR d.allowed_groups && CAST(:groups AS varchar[]))
    ),
    vec AS (
        SELECT id, row_number() OVER (ORDER BY dist) AS rnk
        FROM (
            SELECT id, embedding <=> CAST(:qvec AS vector) AS dist
            FROM allowed ORDER BY dist LIMIT :n
        ) s
    ),
    fts AS (
        SELECT id, row_number() OVER (ORDER BY rank DESC) AS rnk
        FROM (
            SELECT a.id, ts_rank_cd(a.tsv, q) AS rank
            FROM allowed a, websearch_to_tsquery('english', :q) q
            WHERE a.tsv @@ q
            ORDER BY rank DESC LIMIT :n
        ) s
    ),
    fused AS (
        SELECT id, sum(1.0 / (:rrf_k + rnk)) AS score
        FROM (SELECT * FROM vec UNION ALL SELECT * FROM fts) u
        GROUP BY id
    )
    SELECT c.id AS chunk_id, d.id AS document_id, d.source, c.ordinal, c.text, f.score
    FROM fused f
    JOIN chunks c ON c.id = f.id
    JOIN documents d ON d.id = c.document_id
    ORDER BY f.score DESC
    LIMIT :k
    """
)


@dataclass(frozen=True)
class Hit:
    chunk_id: UUID
    document_id: UUID
    source: str
    ordinal: int
    text: str
    score: float


async def hybrid_search(
    session: AsyncSession,
    *,
    query: str,
    query_vector: list[float],
    tenant_id: str,
    user_groups: list[str],
    k: int = 8,
    candidates: int = 30,
) -> list[Hit]:
    rows = await session.execute(
        _SQL,
        {
            "tenant": tenant_id,
            "groups": user_groups,
            "qvec": "[" + ",".join(map(str, query_vector)) + "]",
            "q": query,
            "n": candidates,
            "k": k,
            "rrf_k": RRF_K,
        },
    )
    return [Hit(**row._mapping) for row in rows]
