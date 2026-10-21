from app.ingestion.embedder import FakeEmbedder
from app.ingestion.loader import RawDoc
from app.ingestion.pipeline import ingest
from app.retrieval.search import hybrid_search

embedder = FakeEmbedder()

DOCS = [
    RawDoc("open.md", "Backups are kept for thirty five days."),
    RawDoc("sre-only.md", "Rotate the break-glass credentials every ninety days.", ["sre"]),
    RawDoc("hr-only.md", "Salary bands are reviewed every January.", ["hr"]),
]


async def search(session, query, groups, tenant="t1", k=5):
    (vec,) = await embedder.embed([query])
    return await hybrid_search(
        session, query=query, query_vector=vec, tenant_id=tenant, user_groups=groups, k=k
    )


async def test_finds_relevant_chunk_first(session):
    await ingest(session, embedder, "t1", DOCS)
    hits = await search(session, "how long are backups kept", ["sre"])
    assert hits[0].source == "open.md"


async def test_group_restricted_docs_are_invisible_to_other_groups(session):
    await ingest(session, embedder, "t1", DOCS)
    sources = {h.source for h in await search(session, "salary bands break-glass backups", ["sre"])}
    assert "hr-only.md" not in sources
    assert {"open.md", "sre-only.md"} <= sources


async def test_user_without_groups_sees_only_open_docs(session):
    await ingest(session, embedder, "t1", DOCS)
    sources = {h.source for h in await search(session, "salary break-glass backups", [])}
    assert sources == {"open.md"}


async def test_tenants_do_not_leak(session):
    await ingest(session, embedder, "t1", DOCS)
    assert await search(session, "backups", ["sre", "hr"], tenant="t2") == []


async def test_keyword_only_match_is_found(session):
    # an exact rare term the fake vectors know nothing special about
    await ingest(
        session, embedder, "t1", [RawDoc("code.md", "Error E4721 means the cache is cold.")] + DOCS
    )
    hits = await search(session, "E4721", [])
    assert hits and hits[0].source == "code.md"
