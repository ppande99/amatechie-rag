from sqlalchemy import func, select

from app.ingestion.embedder import FakeEmbedder
from app.ingestion.loader import RawDoc
from app.ingestion.pipeline import ingest
from app.models import Chunk, Document


class CountingEmbedder(FakeEmbedder):
    calls = 0

    async def embed(self, texts):
        type(self).calls += 1
        return await super().embed(texts)


async def count(session, model):
    return (await session.execute(select(func.count()).select_from(model))).scalar_one()


async def test_ingest_is_idempotent_and_detects_changes(session):
    embedder = CountingEmbedder()
    docs = [RawDoc("a.md", "alpha text"), RawDoc("b.md", "beta text", ["sre"])]

    stats = await ingest(session, embedder, "t1", docs)
    assert (stats.added, stats.updated, stats.unchanged) == (2, 0, 0)
    assert await count(session, Document) == 2

    CountingEmbedder.calls = 0
    stats = await ingest(session, embedder, "t1", docs)
    assert (stats.added, stats.updated, stats.unchanged) == (0, 0, 2)
    assert CountingEmbedder.calls == 0  # nothing re-embedded, nothing paid for

    changed = [RawDoc("a.md", "alpha text, edited"), docs[1]]
    stats = await ingest(session, embedder, "t1", changed)
    assert (stats.added, stats.updated, stats.unchanged) == (0, 1, 1)
    assert await count(session, Document) == 2
    assert await count(session, Chunk) == 2  # old chunks of a.md were replaced


async def test_tenants_are_isolated(session):
    embedder = FakeEmbedder()
    await ingest(session, embedder, "t1", [RawDoc("a.md", "same")])
    stats = await ingest(session, embedder, "t2", [RawDoc("a.md", "same")])
    assert stats.added == 1
    assert await count(session, Document) == 2


async def test_groups_are_stored(session):
    await ingest(session, FakeEmbedder(), "t1", [RawDoc("a.md", "x", ["sre", "ops"])])
    doc = (await session.execute(select(Document))).scalar_one()
    assert doc.allowed_groups == ["sre", "ops"]
