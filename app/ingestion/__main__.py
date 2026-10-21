"""Usage: python -m app.ingestion PATH --tenant NAME [--fake]

--fake uses the offline embedder: free, but vectors are not semantically meaningful.
"""

import argparse
import asyncio
from pathlib import Path

from app.db import SessionLocal
from app.ingestion.embedder import FakeEmbedder, GatewayEmbedder
from app.ingestion.loader import load_directory
from app.ingestion.pipeline import ingest


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--tenant", default="default")
    parser.add_argument("--fake", action="store_true")
    args = parser.parse_args()

    docs = load_directory(args.path)
    embedder = FakeEmbedder() if args.fake else GatewayEmbedder()
    async with SessionLocal() as session:
        stats = await ingest(session, embedder, args.tenant, docs)
    print(f"{len(docs)} files: {stats}")


asyncio.run(main())
