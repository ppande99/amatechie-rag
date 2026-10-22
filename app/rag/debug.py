"""Show what happened inside one /ask call: retrieved passages, the exact prompt, the raw reply.

    python -m app.rag.debug "What are the engineering salary bands?" --groups hr --tenant demo

Uses the same backends as the app (EMBEDDER_KIND / CHAT_KIND). One chat call, about half a cent.
"""

import argparse
import asyncio

from app.api.ask import get_chat, get_embedder
from app.db import SessionLocal
from app.rag.answer import SYSTEM_PROMPT, build_prompt, extract_citations
from app.retrieval.search import hybrid_search


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("question")
    parser.add_argument("--groups", default="")
    parser.add_argument("--tenant", default="demo")
    parser.add_argument("--k", type=int, default=5)
    args = parser.parse_args()
    groups = [g.strip() for g in args.groups.split(",") if g.strip()]

    (vec,) = await get_embedder().embed([args.question])
    async with SessionLocal() as session:
        hits = await hybrid_search(
            session,
            query=args.question,
            query_vector=vec,
            tenant_id=args.tenant,
            user_groups=groups,
            k=args.k,
        )

    print(f"== retrieved {len(hits)} passages for groups={groups}")
    for i, h in enumerate(hits, 1):
        print(f"  [{i}] score={h.score:.4f} {h.source}")
    if not hits:
        return

    prompt = build_prompt(args.question, hits)
    print("\n== prompt sent to the model\n" + prompt)
    reply = await get_chat().chat(SYSTEM_PROMPT, prompt)
    print("\n== raw model reply\n" + reply)
    print("\n== valid citations:", [c.n for c in extract_citations(reply, hits)])


asyncio.run(main())
