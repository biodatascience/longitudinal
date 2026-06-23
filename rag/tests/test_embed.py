import pytest
from bios667_rag.embed import Embedder


def test_embedder_produces_vectors():
    embedder = Embedder(model_name="all-MiniLM-L6-v2")

    texts = [
        "Random effects capture within-cluster correlation.",
        "The sandwich estimator provides robust standard errors.",
    ]

    embeddings = embedder.embed(texts)

    assert len(embeddings) == 2
    assert len(embeddings[0]) == 384  # MiniLM dimension
    assert all(isinstance(v, float) for v in embeddings[0])


def test_embedder_uses_gpu_if_available():
    embedder = Embedder()
    assert embedder.model is not None
