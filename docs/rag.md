# Retrieval-augmented generation

Runbooks use versioned Markdown headers. The builder chunks documents with overlap, calculates checksums and emits exact IDs such as `RB-DB-017-v3.4-chunk-1`. Queries enforce service metadata and trust-level filters. Known prompt-injection phrases are rejected before retrieval.

`OPSASSIST_EMBEDDING_BACKEND=sentence_transformer` uses `all-MiniLM-L6-v2` and a FAISS inner-product index over normalized vectors. The default `tfidf` backend is a transparent no-download fallback. Index artifacts are excluded from Git and rebuilt with `python scripts/build_index.py`.
