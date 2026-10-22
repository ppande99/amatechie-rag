"""Usage: python -m app.ingestion PATH --tenant NAME [--embedder fake|bedrock|gateway]

fake: offline and free, vectors are not semantically meaningful.
bedrock: Titan V2 directly with your AWS credentials.
gateway: through the LiteLLM proxy (default).
"""

import argparse
import asyncio
from pathlib import Path

from app.db import SessionLocal
from app.ingestion.embedder import make_embedder
from app.ingestion.loader import load_directory
from app.ingestion.pipeline import ingest


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--tenant", default="default")
    parser.add_argument("--embedder", choices=["fake", "bedrock", "gateway"], default="gateway")
    args = parser.parse_args()

    docs = load_directory(args.path)
    embedder = make_embedder(args.embedder)
    async with SessionLocal() as session:
        stats = await ingest(session, embedder, args.tenant, docs)
    print(f"{len(docs)} files: {stats}")


asyncio.run(main())
