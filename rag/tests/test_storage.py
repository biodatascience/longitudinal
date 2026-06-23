# rag/tests/test_storage.py
import tempfile
from pathlib import Path

import pytest

from bios667_rag.storage import KnowledgeStore


def test_store_initializes_tables():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        store = KnowledgeStore(db_path=db_path, chromadb_path=Path(tmpdir) / "chroma")

        # Check tables exist
        cursor = store.db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = {row[0] for row in cursor.fetchall()}

        assert "nodes" in tables
        assert "edges" in tables
        store.close()


def test_add_and_get_node():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = KnowledgeStore(
            db_path=Path(tmpdir) / "test.db",
            chromadb_path=Path(tmpdir) / "chroma",
        )

        store.add_node(
            node_id="ch8",
            node_type="chapter",
            name="Linear Mixed Effects Models",
            content="This chapter introduces...",
            chapter_num=8,
            page_start=201,
            page_end=250,
        )

        node = store.get_node("ch8")
        assert node is not None
        assert node["name"] == "Linear Mixed Effects Models"
        assert node["type"] == "chapter"
        assert node["chapter_num"] == 8
        store.close()


def test_add_and_query_edges():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = KnowledgeStore(
            db_path=Path(tmpdir) / "test.db",
            chromadb_path=Path(tmpdir) / "chroma",
        )

        # Add nodes
        store.add_node("ch8", "chapter", "Linear Mixed Effects Models", chapter_num=8)
        store.add_node("sec8.1", "section", "Introduction", chapter_num=8)
        store.add_node("concept_reml", "concept", "REML Estimation", chapter_num=8)

        # Add edges
        store.add_edge("ch8", "sec8.1", "contains")
        store.add_edge("sec8.1", "concept_reml", "contains")
        store.add_edge("concept_reml", "concept_ml", "relates_to", confidence=0.9)

        # Query children
        children = store.get_children("ch8")
        assert len(children) == 1
        assert children[0]["id"] == "sec8.1"

        # Query by relationship
        related = store.get_related("concept_reml", relationship="relates_to")
        assert len(related) == 1
        store.close()


def test_vector_search():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = KnowledgeStore(
            db_path=Path(tmpdir) / "test.db",
            chromadb_path=Path(tmpdir) / "chroma",
        )

        # Add nodes with dummy embeddings (384-dim for MiniLM)
        import random
        random.seed(42)

        emb1 = [random.random() for _ in range(384)]
        emb2 = [random.random() for _ in range(384)]

        store.add_node(
            "sec8.1", "section", "Random Effects Introduction",
            content="Random effects allow for correlation within clusters.",
            chapter_num=8, embedding=emb1,
        )
        store.add_node(
            "sec9.1", "section", "Fixed Effects Models",
            content="Fixed effects eliminate between-cluster variation.",
            chapter_num=9, embedding=emb2,
        )

        # Search with query embedding (use emb1 as query)
        results = store.search_vectors(query_embedding=emb1, top_k=2)

        assert len(results) == 2
        assert results[0]["id"] == "sec8.1"  # Should be most similar to itself
        store.close()
