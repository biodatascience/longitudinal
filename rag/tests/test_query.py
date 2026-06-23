# rag/tests/test_query.py
import tempfile
from pathlib import Path
import pytest
from bios667_rag.query import QueryEngine
from bios667_rag.storage import KnowledgeStore
from bios667_rag.embed import Embedder


def test_search_textbook():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = KnowledgeStore(
            db_path=Path(tmpdir) / "test.db",
            chromadb_path=Path(tmpdir) / "chroma",
        )
        embedder = Embedder()
        engine = QueryEngine(store, embedder)

        text1 = "Random effects capture within-cluster correlation patterns."
        text2 = "The sandwich estimator provides robust variance estimates."

        store.add_node(
            "chunk_1", "content", "Random Effects",
            content=text1, chapter_num=8,
            embedding=embedder.embed_single(text1),
        )
        store.add_node(
            "chunk_2", "content", "Sandwich Estimator",
            content=text2, chapter_num=12,
            embedding=embedder.embed_single(text2),
        )

        results = engine.search("correlation in clusters")

        assert len(results) > 0
        assert "Random" in results[0]["content"]

        store.close()
