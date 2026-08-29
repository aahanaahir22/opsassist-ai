from __future__ import annotations

import json

from _bootstrap import ROOT  # noqa: F401
from app.services.retrieval import RetrievalService, load_markdown_documents


def main() -> None:
    documents = load_markdown_documents(ROOT / "data" / "runbooks")
    service = RetrievalService(ROOT / "data" / "indexes")
    count = service.build(documents, persist=True)
    print(json.dumps({"documents": len(documents), "chunks": count, "backend": service.backend, "index": str(service.index_dir), "reproducible": True}, indent=2))


if __name__ == "__main__":
    main()
