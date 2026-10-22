"""Retrieval harness. Run before and after every retrieval change; the numbers are the point.

    python -m eval.retrieval_eval --golden eval/golden.jsonl --tenant demo [--embedder fake|bedrock|gateway] [--k 5]

Reports recall@k and MRR (measured at document level, since chunk ids change on re-ingest) and
counts access violations: any retrieved source listed in a case's `must_not_retrieve`. Violations
must always be zero; the process exits non-zero otherwise, or if scores fall below the thresholds.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from app.db import SessionLocal
from app.ingestion.embedder import Embedder, make_embedder
from app.retrieval.search import hybrid_search
from eval.metrics import mean, recall_at_k, reciprocal_rank


def unique_in_order(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


async def run(golden: list[dict], embedder: Embedder, tenant: str, k: int) -> dict:
    recalls: list[float] = []
    rrs: list[float] = []
    violations: list[dict] = []
    failures: list[dict] = []

    async with SessionLocal() as session:
        for case in golden:
            (vec,) = await embedder.embed([case["question"]])
            hits = await hybrid_search(
                session,
                query=case["question"],
                query_vector=vec,
                tenant_id=tenant,
                user_groups=case.get("user_groups", []),
                k=k,
            )
            sources = unique_in_order([h.source for h in hits])

            for forbidden in case.get("must_not_retrieve", []):
                if forbidden in sources:
                    violations.append({"id": case["id"], "source": forbidden})

            relevant = set(case.get("relevant_sources", []))
            if relevant:  # access-only cases have nothing to score for relevance
                r, rr = recall_at_k(sources, relevant, k), reciprocal_rank(sources, relevant)
                recalls.append(r)
                rrs.append(rr)
                if r < 1.0:
                    failures.append(
                        {"id": case["id"], "question": case["question"], "got": sources}
                    )

    return {
        "k": k,
        "cases": len(golden),
        "scored_cases": len(recalls),
        "recall_at_k": round(mean(recalls), 3),
        "mrr": round(mean(rrs), 3),
        "access_violations": violations,
        "misses": failures,
    }


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--golden", type=Path, default=Path("eval/golden.jsonl"))
    parser.add_argument("--tenant", default="demo")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--embedder", choices=["fake", "bedrock", "gateway"], default="gateway")
    parser.add_argument("--min-recall", type=float, default=0.0)
    parser.add_argument("--min-mrr", type=float, default=0.0)
    args = parser.parse_args()

    golden = [json.loads(line) for line in args.golden.read_text().splitlines() if line.strip()]
    embedder = make_embedder(args.embedder)
    report = await run(golden, embedder, args.tenant, args.k)
    print(json.dumps(report, indent=2))

    ok = (
        not report["access_violations"]
        and report["recall_at_k"] >= args.min_recall
        and report["mrr"] >= args.min_mrr
    )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
