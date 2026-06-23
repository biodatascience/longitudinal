# rag/tests/test_integration.py
"""Integration tests for the full RAG pipeline."""

import tempfile
from pathlib import Path

import pytest

from bios667_rag.storage import KnowledgeStore
from bios667_rag.embed import Embedder
from bios667_rag.graph import KnowledgeGraphBuilder
from bios667_rag.query import QueryEngine
from bios667_rag.chunk import Chunk


def test_full_pipeline():
    """Test the complete RAG pipeline."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = KnowledgeStore(
            db_path=Path(tmpdir) / "test.db",
            chromadb_path=Path(tmpdir) / "chroma",
        )
        embedder = Embedder()
        builder = KnowledgeGraphBuilder(store)
        engine = QueryEngine(store, embedder)

        structure = [
            {"type": "chapter", "number": 8, "title": "Linear Mixed Effects Models", "page": 1},
            {"type": "section", "number": "8.1", "title": "Introduction", "page": 1},
            {"type": "section", "number": "8.2", "title": "Model Specification", "page": 5},
        ]
        builder.build_hierarchy(structure)

        chunks = [
            Chunk(
                text="Random effects models account for correlation within clusters by including subject-specific random deviations.",
                chapter_num=8,
                section_path="8.1",
                page_start=1,
                page_end=2,
            ),
            Chunk(
                text="The linear mixed effects model is Y = Xβ + Zb + ε where b represents random effects.",
                chapter_num=8,
                section_path="8.2",
                page_start=5,
                page_end=6,
            ),
        ]

        for chunk in chunks:
            embedding = embedder.embed_single(chunk.text)
            builder.add_chunk_with_embedding(chunk, embedding)

        results = engine.search("correlation within clusters")
        assert len(results) > 0
        assert "correlation" in results[0]["content"].lower()

        outline = engine.get_chapter_outline(8)
        assert outline["name"] == "Linear Mixed Effects Models"
        assert "children" in outline

        store.close()
