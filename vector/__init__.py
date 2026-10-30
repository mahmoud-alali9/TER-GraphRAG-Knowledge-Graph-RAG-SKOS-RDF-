"""Vector and keyword retrieval over the forest definitions (baselines for GraphRAG).

- ``corpus``  : loads the 2 553 definitions from ``data/schema.ttl``
- ``index``   : dense (FAISS), sparse (BM25) and hybrid (Reciprocal Rank Fusion) search
"""
from vector.corpus import DefinitionDoc, load_definitions
from vector.index import BM25Index, DenseIndex, HybridRetriever, SearchHit, build_retrievers

__all__ = [
    "DefinitionDoc",
    "load_definitions",
    "BM25Index",
    "DenseIndex",
    "HybridRetriever",
    "SearchHit",
    "build_retrievers",
]
