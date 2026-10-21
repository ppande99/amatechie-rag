from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.chunker import chunk_text
from app.ingestion.embedder import Embedder
from app.ingestion.loader import RawDoc
from app.models import Chunk, Document


@dataclass
class IngestStats:
    added: int = 0
    updated: int = 0
    unchanged: int = 0
    chunks_written: int = 0


async def ingest(
    session: AsyncSession, embedder: Embedder, tenant_id: str, docs: list[RawDoc]
) -> IngestStats:
    """Idempotent: re-running on the same files does no embedding work (and costs nothing)."""
    stats = IngestStats()

    for doc in docs:
        existing = (
            await session.execute(
                select(Document).where(
                    Document.tenant_id == tenant_id, Document.source == doc.source
                )
            )
        ).scalar_one_or_none()

        if existing and existing.content_hash == doc.content_hash:
            stats.unchanged += 1
            continue

        pieces = chunk_text(doc.text)
        vectors = await embedder.embed(pieces)  # embed first: a failure leaves old data untouched

        if existing:
            await session.delete(existing)
            await session.flush()
            stats.updated += 1
        else:
            stats.added += 1

        session.add(
            Document(
                tenant_id=tenant_id,
                source=doc.source,
                content_hash=doc.content_hash,
                allowed_groups=doc.allowed_groups,
                chunks=[
                    Chunk(tenant_id=tenant_id, ordinal=i, text=piece, embedding=vec)
                    for i, (piece, vec) in enumerate(zip(pieces, vectors, strict=True))
                ],
            )
        )
        stats.chunks_written += len(pieces)

    await session.commit()
    return stats
