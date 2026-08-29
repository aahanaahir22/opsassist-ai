from __future__ import annotations

import json

from _bootstrap import ROOT
from app.schemas.models import KnowledgeSearchRequest
from app.services.retrieval import RetrievalService


def evaluate(k: int = 3) -> dict:
    queries = json.loads((ROOT / "data" / "evaluation" / "queries.json").read_text())
    service = RetrievalService(ROOT / "data" / "indexes")
    if not service.load():
        raise RuntimeError("Index missing. Run python scripts/build_index.py first.")
    precisions, recalls, reciprocal_ranks = [], [], []
    rows = []
    for query in queries:
        results = service.search(KnowledgeSearchRequest(query=query["query"], service_ids=query["service_ids"], limit=k))
        retrieved = list(dict.fromkeys(item.document_id for item in results))
        relevant = set(query["relevant"])
        hits = [item for item in retrieved if item in relevant]
        precision = len(hits) / max(1, len(retrieved))
        recall = len(hits) / len(relevant)
        rank = next((index + 1 for index, item in enumerate(retrieved) if item in relevant), 0)
        precisions.append(precision); recalls.append(recall); reciprocal_ranks.append(1 / rank if rank else 0)
        rows.append({"query": query["query"], "retrieved": retrieved, "precision_at_k": precision, "recall_at_k": recall, "reciprocal_rank": reciprocal_ranks[-1]})
    return {
        "k": k,
        "precision_at_k": sum(precisions) / len(precisions),
        "recall_at_k": sum(recalls) / len(recalls),
        "mean_reciprocal_rank": sum(reciprocal_ranks) / len(reciprocal_ranks),
        "queries": rows,
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))
